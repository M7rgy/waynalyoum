"""Agent 0 — CEO. Pure rules, zero tokens: decides today's mix, slots and theme."""
import datetime as dt

from common import DATA, config, read_json, write_json

def plan(date: dt.date):
    """Same 8 slots every day: 5 Bahrain + 3 GCC (config.json -> daily_mix)."""
    cfg = config()
    day = date.strftime("%A")
    mix = sorted(cfg["daily_mix"], key=lambda s: s["time"])
    n = (date - dt.date(2026, 10, 28)).days  # D1 = 2026-10-29
    return {
        "date": date.isoformat(),
        "weekday": day,
        "theme": cfg["weekly_theme"][day] + " (applies to the Bahrain posts)",
        "rules": [
            "fill every slot with a fact from its own region: bahrain slots -> region=bahrain facts, gcc slots -> region=gcc facts",
            "if there is no approved fact for a slot's region, OMIT that slot (never invent, never swap regions)",
            "the 3 gcc posts should cover different countries when possible",
            "post_type: gcc posts are always 'international'; bahrain posts are 'info' or 'local' (or 'international' for Bahrain on the world stage)",
            "max 2 posts from the same category; stories carry their question in the text (no stickers)",
            "Thursday/Friday: include a 'وين نروح الويكند؟' angle",
            "dated events must include date + venue + how to get tickets",
        ],
        "slots": [
            {"post_id": f"D{n}-{i:02d}", "slot": s["slot"], "format": s["format"], "region": s["region"],
             "time_local": s["time"],
             "platforms": ["instagram", "tiktok"] if s["format"] == "reel" else ["instagram"]}
            for i, s in enumerate(mix, 1)
        ],
    }


def used_topic_keys(today: dt.date):
    used = read_json(DATA / "used_topics.json", {})
    keep_after = today - dt.timedelta(days=config()["dedupe_days"])
    return {k for k, d in used.items() if dt.date.fromisoformat(d) >= keep_after}


def remember_topics(batch):
    used = read_json(DATA / "used_topics.json", {})
    for p in batch["posts"]:
        used[p["topic_key"]] = batch["date"]
    write_json(DATA / "used_topics.json", used)
