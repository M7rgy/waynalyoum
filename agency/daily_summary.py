"""Opens today's "Batch YYYY-MM-DD" GitHub issue: preview of every post + veto instructions + TikTok files.
GitHub's phone app notifies you when it appears (Settings > Notifications > watch this repo).

  python daily_summary.py 2026-11-11
"""
import json
import os
import subprocess
import sys
import urllib.request

from common import ASSETS, CONTENT, ROOT, read_json, write_json, log
from render import caption, expected_assets, normalize


def body(date, batch, base):
    L = [f"## وين اليوم — {date}", "",
         "Everything below **posts automatically** at the listed time (Bahrain).",
         "**To veto:** comment `skip D14-03` (one or more IDs) or `stop` (cancel the rest of today).", ""]
    if batch.get("held_topics"):
        L += ["<details><summary>Held by Gatekeeper</summary>", ""] + [f"- {h['topic']} — {h['reason']}" for h in batch["held_topics"]] + ["", "</details>", ""]
    L += ["| ID | Time | Format | Type | Topic |", "|---|---|---|---|---|"]
    for p in sorted(batch["posts"], key=lambda x: x["time_local"]):
        L.append(f"| {p['post_id']} | {p['time_local']} | {p['format']} | {(p.get('region') + '/') if p.get('region') else ''}{p['post_type']} | {p['title_internal']} |")
    L.append("")
    for p in sorted(batch["posts"], key=lambda x: x["time_local"]):
        files = expected_assets(p)
        L += ["---", f"### {p['post_id']} · {p['time_local']} · {p['format']} — {p['title_internal']}", ""]
        if p["format"] == "reel":
            L.append(f"🎬 [Watch / download the reel]({base}/{date}/{files[0]})")
            L.append(f"🎙️ Want your voice on it? Upload `{p['post_id']}.m4a` (or .mp3) to the [voice/ folder](https://github.com/{os.environ.get('GITHUB_REPOSITORY', 'M7rgy/waynalyoum')}/tree/main/voice) before {p['time_local']}.")
        else:
            L.append(" ".join(f'<img src="{base}/{date}/{f}" width="160">' for f in files[:4]))
        if p["format"] != "story":
            L += ["", "```", caption(p, "instagram"), "```"]
        ideas = [f.get("phone_sticker_idea") for f in p.get("frames", []) if f.get("phone_sticker_idea")]
        if ideas:
            L.append(f"\n💡 Optional sticker to add from your phone: {ideas[0]}")
        if "tiktok" in p["platforms"]:
            L += ["", "**TikTok (post manually):** download the reel above, caption:", "```", caption(p, "tiktok"), "```"]
        if p.get("sources"):
            L.append("\nSources: " + " · ".join(f"[{i}]({u})" for i, u in enumerate(p["sources"], 1)))
        L.append("")
    return "\n".join(L)


def main(date):
    repo, tok = os.environ.get("GITHUB_REPOSITORY"), os.environ.get("GITHUB_TOKEN")
    batch = normalize(read_json(CONTENT / date / "batch.json", None))
    sha = read_json(CONTENT / date / "media.json", {}).get("sha") or \
        subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    base = f"https://cdn.jsdelivr.net/gh/{repo}@{sha}/assets"
    text = body(date, batch, base)
    if not (repo and tok):
        print(text)
        return
    req = urllib.request.Request(f"https://api.github.com/repos/{repo}/issues", method="POST",
                                 data=json.dumps({"title": f"Batch {date} — {len(batch['posts'])} posts", "body": text[:65000]}).encode(),
                                 headers={"Authorization": f"Bearer {tok}", "Accept": "application/vnd.github+json",
                                          "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        issue = json.loads(r.read())
    write_json(CONTENT / date / "summary_issue.json", {"number": issue["number"], "url": issue["html_url"]})
    log(f"summary: issue #{issue['number']} {issue['html_url']}")


if __name__ == "__main__":
    main(sys.argv[1])
