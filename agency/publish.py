"""Agent 5 — Ops/Publisher. Uploads assets to Postiz and creates drafts (or scheduled posts).

Usage:
  python publish.py --check                 # show Postiz integration ids + settings rules (do this once)
  python publish.py 2026-10-29              # create DRAFTS for that day (safe default)
  python publish.py 2026-10-29 --schedule   # create SCHEDULED posts (goes live automatically)
  python publish.py 2026-10-29 --dry-run    # print the commands only
"""
import argparse
import json
import shutil
import subprocess
import sys

from common import ASSETS, CONTENT, config, read_json, write_json, log, load_env

POSTIZ = shutil.which("postiz") or shutil.which("postiz.cmd") or "postiz"


def run(args, dry=False):
    if not dry and not shutil.which(POSTIZ):
        raise SystemExit("Postiz CLI not found. Install Node.js 18+, then run:  npm install -g postiz")
    if dry:
        print("  $ postiz " + " ".join(json.dumps(a, ensure_ascii=False) if " " in a or "{" in a else a for a in args))
        return "{}"
    out = subprocess.run([POSTIZ, *args], capture_output=True, text=True, encoding="utf-8")
    if out.returncode != 0:
        raise RuntimeError(out.stderr or out.stdout)
    return out.stdout


def _json(stdout):
    # the CLI may print a header line before the JSON
    i = min([x for x in (stdout.find("{"), stdout.find("[")) if x >= 0], default=0)
    return json.loads(stdout[i:])


def check():
    try:
        print(run(["auth:status"]))
        integrations = _json(run(["integrations:list"]))
    except RuntimeError as e:
        print(str(e).strip())
        print("\n-> Not logged in to Postiz. Run:  postiz auth:login")
        print("   (or paste a key from Postiz > Settings > Public API into POSTIZ_API_KEY in .env)")
        return
    for it in integrations:
        print(f"\n== {it.get('identifier')} | id={it.get('id')} | {it.get('name')}")
        s = _json(run(["integrations:settings", it["id"]]))
        print("rules:", s.get("output", {}).get("rules"))
    print("\nPaste the instagram/tiktok ids into agency/config.json -> postiz.integration_ids")


def publish(date, schedule=False, dry=False):
    cfg = config()["postiz"]
    plan_path = CONTENT / date / "postiz" / "plan.json"
    if not plan_path.exists():
        days = sorted(p.name for p in CONTENT.iterdir() if (p / "postiz" / "plan.json").exists())
        print(f"No batch found for {date} (looked for {plan_path}).")
        print("Create it first:  python run_daily.py --date " + date)
        print("Batches you already have: " + (", ".join(days) or "none"))
        return
    ids = cfg["integration_ids"]
    if not dry and any(v.startswith("PASTE_") for v in ids.values()):
        print("Postiz account IDs are not set yet in config.json -> postiz.integration_ids.")
        print("Run:  python publish.py --check   then paste the instagram/tiktok ids into config.json.")
        return
    plan = read_json(plan_path, [])
    print(f"Publishing {len(plan)} items for {date} as {'SCHEDULED' if schedule else 'DRAFTS'}...")
    folder = ASSETS / date
    report = []
    for item in plan:
        tag = f"{item['post_id']}/{item['platform']}"
        if item["manual_on_phone"]:
            report.append({**item, "status": "manual — post from phone (interactive sticker)"})
            log(f"publish: {tag} skipped (phone story)")
            continue
        missing = [a for a in item["assets"] if not (folder / a).exists()]
        if missing and not dry:
            report.append({**item, "status": f"missing assets: {missing}"})
            log(f"publish: {tag} missing {missing}")
            continue
        urls = []
        for a in item["assets"]:
            urls.append(_json(run(["upload", str(folder / a)], dry)).get("path", f"<{a}>"))
        integ = cfg["integration_ids"][item["platform"]]
        args = ["posts:create", "-c", item["content"] or " ", "-s", item["schedule_utc"],
                "-i", integ, "-m", ",".join(urls), "--settings", json.dumps(item["settings"])]
        if not schedule:
            args += ["-t", "draft"]
        res = run(args, dry)
        report.append({**item, "status": "scheduled" if schedule else "draft", "postiz": res.strip()[:300]})
        log(f"publish: {tag} -> {'scheduled' if schedule else 'draft'}")
    write_json(CONTENT / date / "postiz" / "publish_report.json", report)
    for r in report:
        print(f"{r['post_id']:>6} {r['platform']:<9} {r['time_local']}  {r['status']}")


if __name__ == "__main__":
    load_env()
    ap = argparse.ArgumentParser()
    ap.add_argument("date", nargs="?")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--schedule", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    if a.check:
        check()
    elif a.date:
        publish(a.date, a.schedule, a.dry_run)
    else:
        ap.print_help()
        print("\nExample:  python publish.py 2026-10-29 --dry-run")
