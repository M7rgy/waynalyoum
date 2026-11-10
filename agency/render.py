"""Ops helper: batch.json -> human-readable batch.md + one Postiz plan file per post."""
import sys
from pathlib import Path

from common import CONTENT, config, read_json, write_json, to_utc_iso

STICKERS = {"poll", "quiz", "slider", "question", "countdown"}


def normalize(batch):
    """AI output can contain nulls where lists/objects are expected -> make them safe."""
    for p in batch.get("posts", []):
        for k in ("script", "slides", "frames", "hashtags", "visual_prompts", "broll_search", "sources", "platforms"):
            p[k] = p.get(k) or []
        p["post_type"] = (p.get("post_type") or "local").lower()
        for k in ("hook", "caption_instagram", "caption_tiktok", "audio_suggestion", "title_internal"):
            p[k] = p.get(k) or ""
        for f in p["frames"]:
            f["sticker"] = f.get("sticker") or {}
            f["text"] = f.get("text") or ""
            f["visual_prompt"] = f.get("visual_prompt") or ""
        for sl in p["slides"]:
            sl["body"] = sl.get("body") or ""
            sl["visual_prompt"] = sl.get("visual_prompt") or ""
    return batch


def needs_phone(post):
    """Instagram's API can't add interactive stickers. In full-auto mode stories go out without them."""
    if config().get("automation", {}).get("full_auto", True):
        return False
    return post["format"] == "story" and any(
        f.get("sticker", {}).get("type") in STICKERS for f in post.get("frames", []))


def expected_assets(post):
    pid = post["post_id"]
    if post["format"] == "reel":
        return [f"{pid}.mp4"]
    if post["format"] == "carousel":
        return [f"{pid}_{s['n']}.jpg" for s in post["slides"]]
    if post["format"] == "story":
        return [f"{pid}_{f['n']}.jpg" for f in post["frames"]]
    return [f"{pid}.jpg"]


def caption(post, platform):
    text = post.get(f"caption_{platform}") or post.get("caption_instagram") or post.get("hook", "")
    tags = post.get("hashtags", [])[:5]  # Instagram caps hashtags at 5; TikTok works best with 3-5
    return (text + ("\n\n" + " ".join(tags) if tags else "")).strip()


def postiz_plan(batch):
    cfg = config()
    plans = []
    for p in batch["posts"]:
        for platform in p["platforms"]:
            settings = {}
            if platform == "instagram":
                settings = {"post_type": "story" if p["format"] == "story" else "post"}
            elif platform == "tiktok":
                settings = dict(cfg["postiz"]["tiktok_settings"])
            plans.append({
                "post_id": p["post_id"], "platform": platform, "format": p["format"],
                "schedule_utc": to_utc_iso(batch["date"], p["time_local"], cfg["timezone_offset"]),
                "time_local": p["time_local"], "content": "" if p["format"] == "story" else caption(p, platform),
                "assets": expected_assets(p), "settings": settings,
                "manual_on_phone": needs_phone(p),
            })
    return plans


def markdown(batch):
    L = [f"# وين اليوم — Daily Batch {batch['date']}", "",
         f"**Theme:** {batch.get('day_theme', '')}", ""]
    if batch.get("held_topics"):
        L += ["> ⏸️ **Held by Gatekeeper:**"] + [f"> - {h['topic']} — {h['reason']}" for h in batch["held_topics"]] + [""]
    L += ["| # | Time (BH) | Format | Platforms | Topic | Post from |", "|---|---|---|---|---|---|"]
    for p in sorted(batch["posts"], key=lambda x: x["time_local"]):
        L.append(f"| {p['post_id']} | {p['time_local']} | {p['format']} | {', '.join(p['platforms'])} | "
                 f"{p['title_internal']} | {'📱 phone (sticker)' if needs_phone(p) else 'Postiz'} |")
    L.append("")
    for p in sorted(batch["posts"], key=lambda x: x["time_local"]):
        L += ["---", "", f"## {p['post_id']} · {p['format'].upper()} · {p['time_local']} — {p['title_internal']}", "",
              f"**Type:** {p['post_type']}  ·  **Hook:** {p['hook']}", ""]
        if p.get("script"):
            L += ["| Time | On-screen text | Voice-over | Visual |", "|---|---|---|---|"]
            for s in p["script"]:
                cell = lambda x: x.replace("\n", "<br>").replace("|", "/")
                L.append(f"| {s['t']} | {cell(s['on_screen'])} | {cell(s['vo'])} | {cell(s['visual'])} |")
            L.append("")
        if p.get("slides"):
            L += ["| Slide | Headline | Body |", "|---|---|---|"]
            for s in p["slides"]:
                L.append(f"| {s['n']} | {s['headline']} | {s['body'].replace(chr(10), '<br>')} |")
            L.append("")
        if p.get("frames"):
            for f in p["frames"]:
                st = f.get("sticker", {})
                L.append(f"- **Frame {f['n']}:** {f['text'].replace(chr(10), ' / ')}  ·  sticker: `{st.get('type')}` {st.get('data', '')}")
            L.append("")
        if p.get("caption_instagram"):
            L += ["**Instagram caption:**", "", "```", caption(p, "instagram"), "```", ""]
        if "tiktok" in p["platforms"]:
            L += ["**TikTok caption:**", "", "```", caption(p, "tiktok"), "```", ""]
        if p.get("audio_suggestion"):
            L.append(f"**Audio:** {p['audio_suggestion']}  ")
        prompts = p.get("visual_prompts", []) + [s["visual_prompt"] for s in p.get("slides", [])] + \
                  [f["visual_prompt"] for f in p.get("frames", [])]
        if prompts:
            L += ["", "<details><summary>🎨 Visual prompts</summary>", ""] + [f"{i}. `{x}`" for i, x in enumerate(prompts, 1)] + ["", "</details>"]
        if p.get("broll_search"):
            L.append(f"\n**B-roll search:** {', '.join(p['broll_search'])}")
        L.append(f"\n**Assets expected in `assets/{batch['date']}/`:** {', '.join(expected_assets(p))}")
        L += ["", "**Sources:**"] + [f"- {u}" for u in p.get("sources", [])] + [""]
    return "\n".join(L)


def render(date):
    folder = CONTENT / date
    batch = normalize(read_json(folder / "batch.json", None))
    (folder / "batch.md").write_text(markdown(batch), encoding="utf-8")
    write_json(folder / "postiz" / "plan.json", postiz_plan(batch))
    return folder


if __name__ == "__main__":
    print(render(sys.argv[1]))
