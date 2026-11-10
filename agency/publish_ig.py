"""Agent 5 — Ops: publishes due posts straight to Instagram via Meta's free Graph API (no Postiz).

  python publish_ig.py --check            # verify token + account
  python publish_ig.py --due              # publish everything whose time has come (run every 30 min by GitHub Actions)
  python publish_ig.py --due --dry-run    # show what would be posted

Needs env: IG_USER_ID, IG_ACCESS_TOKEN (never-expiring Page token, see 04_GitHub_Instagram_Setup.md)
Media are served publicly from this repo through jsDelivr:  https://cdn.jsdelivr.net/gh/<owner>/<repo>@<commit>/assets/...
Veto: comment on today's "Batch YYYY-MM-DD" GitHub issue:  "stop"  (nothing more today)  or  "skip D14-03"
"""
import argparse
import datetime as dt
import json
import os
import re
import subprocess
import time
import urllib.error
import urllib.parse
import urllib.request

from common import ASSETS, CONTENT, ROOT, bahrain_now, config, load_env, log, read_json, write_json
from render import caption, expected_assets, normalize

GRAPH = "https://graph.facebook.com/" + os.environ.get("GRAPH_VERSION", "v27.0")
LATE_LIMIT_H = 3        # don't publish a slot more than 3h late (e.g. after a long GitHub outage)
MAX_ATTEMPTS = 3


# ───────────── Graph API ─────────────
def api(method, path, **params):
    params["access_token"] = os.environ["IG_ACCESS_TOKEN"]
    data = urllib.parse.urlencode(params).encode()
    url = f"{GRAPH}/{path}"
    req = urllib.request.Request(url + ("?" + data.decode() if method == "GET" else ""),
                                 data=None if method == "GET" else data, method=method)
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"Graph API {e.code}: {e.read().decode()[:500]}") from None


def wait_ready(container, timeout=300):
    t0 = time.time()
    while time.time() - t0 < timeout:
        st = api("GET", container, fields="status_code,status").get("status_code")
        if st == "FINISHED":
            return
        if st in ("ERROR", "EXPIRED"):
            raise RuntimeError(f"container {container} {st}: {api('GET', container, fields='status').get('status')}")
        time.sleep(8)
    raise TimeoutError(f"container {container} not ready after {timeout}s")


def publish_container(container):
    wait_ready(container)
    return api("POST", f"{os.environ['IG_USER_ID']}/media_publish", creation_id=container)["id"]


# ───────────── media URLs (jsDelivr in front of this public repo) ─────────────
def media_info(date):
    """Generated files live on the orphan 'media' branch; content/<date>/media.json holds its commit + file list."""
    repo = os.environ.get("GITHUB_REPOSITORY") or config().get("github_repo", "")
    info = read_json(CONTENT / date / "media.json", {})
    sha = info.get("sha") or subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    files = set(info.get("files") or [p.name for p in (ASSETS / date).glob("*") if p.is_file()])
    return f"https://cdn.jsdelivr.net/gh/{repo}@{sha}/assets", files


def warm(url):
    """Ask jsDelivr for the file once so Meta's fetch hits a ready cache."""
    for _ in range(3):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, method="HEAD"), timeout=60) as r:
                if r.status == 200:
                    return True
        except Exception:
            time.sleep(5)
    return False


# ───────────── post types ─────────────
def post_one(post, date, media, dry, done_frames=None, on_frame=None):
    base, available = media
    uid = os.environ.get("IG_USER_ID", "IG_USER_ID")
    files = expected_assets(post)
    urls = [f"{base}/{date}/{f}" for f in files]
    missing = [f for f in files if f not in available]
    if missing:
        raise FileNotFoundError(f"missing assets: {missing}")
    text = caption(post, "instagram")
    fmt = post["format"]
    if dry:
        return {"dry_run": True, "format": fmt, "urls": urls, "caption": text[:120]}
    for u in urls:
        warm(u)
    if fmt == "carousel":
        kids = [api("POST", f"{uid}/media", image_url=u, is_carousel_item="true")["id"] for u in urls[:10]]
        for k in kids:
            wait_ready(k, 120)
        parent = api("POST", f"{uid}/media", media_type="CAROUSEL", children=",".join(kids), caption=text)["id"]
        return {"ig_media_id": publish_container(parent)}
    if fmt == "story":  # frames go out one by one; progress is saved so a retry never repeats a frame
        ids = list(done_frames or [])
        for u in urls[len(ids):]:
            ids.append(publish_container(api("POST", f"{uid}/media", media_type="STORIES", image_url=u)["id"]))
            if on_frame:
                on_frame(ids)
        return {"ig_media_id": ids}
    if fmt == "reel":
        c = api("POST", f"{uid}/media", media_type="REELS", video_url=urls[0], caption=text, share_to_feed="true")["id"]
        wait_ready(c, 600)
        return {"ig_media_id": publish_container(c)}
    c = api("POST", f"{uid}/media", image_url=urls[0], caption=text)["id"]
    return {"ig_media_id": publish_container(c)}


# ───────────── veto via GitHub issue ─────────────
def vetoes(date):
    tok, repo = os.environ.get("GITHUB_TOKEN"), os.environ.get("GITHUB_REPOSITORY")
    state = read_json(CONTENT / date / "summary_issue.json", {})
    if not (tok and repo and state.get("number")):
        return set(), False
    req = urllib.request.Request(f"https://api.github.com/repos/{repo}/issues/{state['number']}/comments?per_page=100",
                                 headers={"Authorization": f"Bearer {tok}", "Accept": "application/vnd.github+json"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            comments = json.loads(r.read())
    except Exception as e:
        log(f"publish: could not read veto comments ({e}) -> continuing")
        return set(), False
    skip, stop = set(), False
    for c in comments:
        if c.get("author_association") not in ("OWNER", "COLLABORATOR", "MEMBER"):
            continue  # only you (and people you add) can veto
        body = c.get("body", "").lower()
        if re.search(r"\b(stop|pause|وقف)\b", body):
            stop = True
        skip |= {m.upper() for m in re.findall(r"\bd\d+-\d{2}\b", body)}
    return skip, stop


# ───────────── main loop ─────────────
def due(dry=False, date=None):
    now = bahrain_now()
    date = date or now.date().isoformat()
    path = CONTENT / date / "batch.json"
    if not path.exists():
        log(f"publish: no batch for {date}")
        return
    batch = normalize(read_json(path, None))
    state_path = CONTENT / date / "ig_state.json"
    state = read_json(state_path, {})
    skip, stop = vetoes(date)
    media = media_info(date)
    for post in sorted(batch["posts"], key=lambda p: p["time_local"]):
        pid = post["post_id"]
        st = state.get(pid, {})
        if st.get("status") in ("published", "vetoed", "too_late") or st.get("attempts", 0) >= MAX_ATTEMPTS:
            continue
        when = dt.datetime.fromisoformat(f"{date}T{post['time_local']}:00+03:00")
        if now < when:
            continue
        if stop or pid in skip:
            state[pid] = {"status": "vetoed", "at": now.isoformat()}
            log(f"publish: {pid} vetoed")
            continue
        if now - when > dt.timedelta(hours=LATE_LIMIT_H):
            state[pid] = {"status": "too_late", "at": now.isoformat()}
            log(f"publish: {pid} skipped (more than {LATE_LIMIT_H}h late)")
            continue
        try:
            def save_frames(ids, pid=pid):
                state[pid] = {**state.get(pid, {}), "frames_done": ids}
                write_json(state_path, state)
            res = post_one(post, date, media, dry, st.get("frames_done"), save_frames)
            if dry:
                print(json.dumps({pid: res}, ensure_ascii=False))
                continue
            state[pid] = {"status": "published", "at": now.isoformat(), **res}
            log(f"publish: {pid} {post['format']} -> published")
        except Exception as e:
            state[pid] = {**state.get(pid, {}), "status": "failed", "attempts": st.get("attempts", 0) + 1,
                          "error": str(e)[:400], "at": now.isoformat()}
            log(f"publish: {pid} FAILED ({e})")
        if not dry:
            write_json(state_path, state)  # save after every post so a crash never double-posts
    if not dry:
        write_json(state_path, state)


def check():
    me = api("GET", os.environ["IG_USER_ID"], fields="username,name,media_count")
    lim = api("GET", f"{os.environ['IG_USER_ID']}/content_publishing_limit", fields="config,quota_usage")
    print("Connected to Instagram:", me)
    print("Publishing quota:", lim)


if __name__ == "__main__":
    load_env()
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--due", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--date")
    a = ap.parse_args()
    if a.check:
        check()
    elif a.due:
        due(a.dry_run, a.date)
    else:
        ap.print_help()
