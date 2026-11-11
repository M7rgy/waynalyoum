"""وين اليوم — daily orchestrator. CEO -> Scout -> Gatekeeper -> Creative/Visual -> Gatekeeper pass 2 -> Ops.

  python run_daily.py                    # tomorrow's batch (default: run at 06:00 for today -> use --today)
  python run_daily.py --today
  python run_daily.py --date 2026-11-02
  python run_daily.py --dry-run          # no API calls: shows plan, candidates and a token estimate
"""
import argparse
import datetime as dt
import json
import re

import ceo
import scout
from common import CONTENT, bahrain_now, load_env, log, write_json, read_json
from render import render
from safety import scan_post


def approx_tokens(obj):
    return len(json.dumps(obj, ensure_ascii=False)) // 3  # rough: Arabic ≈ 3 chars/token


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date")
    ap.add_argument("--today", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    load_env()

    today = bahrain_now().date()
    date = dt.date.fromisoformat(a.date) if a.date else (today if a.today else today + dt.timedelta(days=1))
    folder = CONTENT / date.isoformat()
    folder.mkdir(parents=True, exist_ok=True)

    # 0 — CEO (rules, free)
    plan = ceo.plan(date)
    used = ceo.used_topic_keys(date)
    write_json(folder / "plan.json", plan)
    log(f"ceo: {date} {plan['weekday']} -> {[s['format'] for s in plan['slots']]}")

    # 1 — Scout (RSS + inbox + evergreen, free)
    candidates = scout.run(used)
    write_json(folder / "candidates.json", candidates)

    if a.dry_run:
        g_in = approx_tokens(candidates) + 1500
        c_in = approx_tokens(plan) + g_in // 2 + 1500
        print(f"\nDRY RUN — {len(candidates)} candidates. Est. tokens: gatekeeper ~{g_in} in / ~2k out, "
              f"creative ~{c_in} in / ~8-10k out.")
        for c in candidates:
            print(f" - [{c['origin']}] {c['title'][:90]}")
        return

    from llm import ask

    # 2 — Gatekeeper (Haiku, one call for all candidates)
    verdicts = []  # judge in chunks of 10 so a big news day never overflows one reply
    for i in range(0, len(candidates), 10):
        out = ask("gatekeeper", "gatekeeper", {"today": date.isoformat(), "candidates": candidates[i:i + 10]})
        if isinstance(out, dict):  # tolerate {"verdicts": [...]} or a single object
            out = next((v for v in out.values() if isinstance(v, list)), [out])
        verdicts += [v for v in out if isinstance(v, dict)]
    by_id = {c["id"]: c for c in candidates}
    for v in verdicts:  # fill gaps the model left out
        c = by_id.get(v.get("id"), {})
        v.setdefault("region", c.get("scope_hint", "bahrain"))
        v.setdefault("facts", [{"fact": c.get("title", ""), "source_url": c.get("url", "")}] if c else [])
    approved = [v for v in verdicts if v.get("decision") == "approve" and (v.get("risk") or 0) < 3]
    held = [{"topic": by_id.get(v.get("id"), {}).get("title", v.get("id")), "reason": v.get("reason", "")}
            for v in verdicts if v.get("decision") == "hold"]
    write_json(folder / "gatekeeper.json", verdicts)
    counts = {d: sum(1 for v in verdicts if v.get("decision") == d) for d in ("approve", "hold", "reject")}
    log(f"gatekeeper: {len(approved)} approved ({sum(1 for v in approved if v['region'] == 'bahrain')} bahrain, "
        f"{sum(1 for v in approved if v['region'] == 'gcc')} gcc) | raw decisions {counts} of {len(candidates)} candidates")
    # slow news day: top up Bahrain with pre-checked evergreen facts so the day is never empty
    if sum(1 for v in approved if v["region"] == "bahrain") < 3:
        for e in scout._evergreen(used)[:5]:
            approved.append({"id": e["id"], "decision": "approve", "risk": 0, "region": "bahrain", "category": "heritage",
                             "facts": [{"fact": e["title"] + ". " + e.get("summary", ""), "source_url": e.get("url", "")}],
                             "angle": "evergreen"})
        log(f"gatekeeper: topped up with evergreen -> {len(approved)} facts")
    if not approved:
        raise SystemExit("gatekeeper: nothing approved and no evergreen left -> add ideas to data/inbox.md")

    # 3+4 — Creative + Visual Director (Sonnet, one call for the whole day)
    batch = ask("creative", "creative", {"plan": plan, "facts": approved, "avoid_topic_keys": sorted(used)})
    batch["date"], batch["day_theme"] = date.isoformat(), plan["theme"]
    batch["held_topics"] = held + batch.get("held_topics", [])

    # 2b — Gatekeeper pass 2 (regex, free): drop any post whose public copy hits the red list
    source_text = json.dumps(approved, ensure_ascii=False) + json.dumps(candidates, ensure_ascii=False)
    clean = []
    for p in batch["posts"]:
        public = json.dumps({k: p.get(k) for k in ("hook", "slides", "frames", "script", "caption_instagram")}, ensure_ascii=False)
        bad_names = [n for n in set(re.findall(r"«([^»]{2,40})»", public)) if n not in source_text]
        if bad_names:  # a quoted event name that appears in no source = likely misread/invented
            batch["held_topics"].append({"topic": p.get("title_internal", p["post_id"]), "reason": f"unverified names: {bad_names}"})
            log(f"pass2: dropped {p['post_id']} unverified names {bad_names}")
            continue
        hits = scan_post(p)
        if hits:
            batch["held_topics"].append({"topic": p.get("title_internal", p["post_id"]), "reason": f"red-list words in copy: {hits}"})
            log(f"pass2: dropped {p['post_id']} {hits}")
        else:
            clean.append(p)
    batch["posts"] = clean

    # 5 — Ops: save, render review doc + Postiz plan, remember topics
    write_json(folder / "batch.json", batch)
    render(date.isoformat())
    ceo.remember_topics(batch)
    by = {r: sum(1 for p in clean if (p.get("region") or ("gcc" if p.get("post_type") == "international" else "bahrain")) == r) for r in ("bahrain", "gcc")}
    log(f"ops: {len(clean)}/{len(plan['slots'])} posts ready (bahrain {by['bahrain']}/5, gcc {by['gcc']}/3) -> {folder / 'batch.md'}")
    if len(clean) < len(plan["slots"]):
        log("ops: some slots empty -> not enough approved news; add ideas to data/inbox.md")


if __name__ == "__main__":
    main()
