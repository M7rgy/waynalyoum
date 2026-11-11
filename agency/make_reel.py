"""Auto-reel: turns a reel script into a 9:16 MP4 slideshow (one branded card per beat, slow zoom, hard cuts).

  python make_reel.py 2026-11-11

Audio (first match wins):
  1. Your voice-over:  voice/<post_id>.mp3|.m4a|.wav  (e.g. voice/D14-06.m4a) -> video stretches to fit the voice
  2. A music track:    assets/music/*.mp3  (put royalty-free tracks here; one is picked per day)
  3. Silence (add a trending sound in the Instagram app if you want)
Optional AI backgrounds per beat: assets/<date>/bg/<post_id>_beat<N>.jpg
Output: assets/<date>/<post_id>.mp4  (H.264 + AAC, 1080x1920, 30 fps, kept under 19 MB for hosting)
"""
import json
import os
import random
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from common import ASSETS, CONTENT, log, read_json
from render import normalize
from render_slides import check_arabic, kicker, style_for
import slide_styles as S

FFMPEG = shutil.which("ffmpeg") or "ffmpeg"
FPS = 30
MAX_MB = 19


def beat_seconds(t, default=4.0):
    nums = [float(x) for x in re.findall(r"\d+(?:\.\d+)?", t or "")]
    if len(nums) >= 2 and nums[1] > nums[0]:
        return max(2.0, nums[1] - nums[0])
    return default


def audio_for(date, pid):
    for vdir in (ASSETS.parent / "voice", ASSETS / date / "voice"):  # repo-root voice/ folder is the easy one
        for ext in ("mp3", "m4a", "wav", "aac", "ogg"):
            f = vdir / f"{pid}.{ext}"
            if f.exists():
                return f, "voice"
    music = sorted((ASSETS / "music").glob("*.mp3")) if (ASSETS / "music").exists() else []
    if music:
        return random.Random(date).choice(music), "music"
    return None, "silent"


def duration(path):
    out = subprocess.run([FFMPEG, "-i", str(path)], capture_output=True, text=True).stderr
    m = re.search(r"Duration: (\d+):(\d+):(\d+\.\d+)", out)
    return int(m[1]) * 3600 + int(m[2]) * 60 + float(m[3]) if m else 0.0


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(r.stderr[-1500:])


def make_slideshow(post, date):
    pid = post["post_id"]
    beats = post.get("script") or []
    if not beats:
        log(f"reel: {pid} has no script beats -> skipped")
        return None
    _, style = style_for(post)
    fn = S.STYLES[style][1]
    secs = [beat_seconds(b.get("t")) for b in beats]
    audio, kind = audio_for(date, pid)
    if kind == "voice":  # stretch beats proportionally to the voice length
        total = duration(audio)
        if total > 0:
            secs = [s * total / sum(secs) for s in secs]
    out = ASSETS / date / f"{pid}.mp4"
    out.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        clips = []
        for i, (b, sec) in enumerate(zip(beats, secs), 1):
            head, *rest = (b.get("on_screen") or "").split("\n")
            bg = ASSETS / date / "bg" / f"{pid}_beat{i}.jpg"
            ctx = {"total": len(beats), "kicker": kicker(post), "handle": "@waynalyoum",
                   "bg": bg if bg.exists() else None, "fmt": "story"}
            card = tmp / f"c{i}.png"
            fn((1080, 1920), {"headline": head, "body": "\n".join(rest), "n": i}, ctx).save(card)
            frames = max(1, int(round(sec * FPS)))
            clip = tmp / f"c{i}.mp4"
            # slow push-in: 1.00 -> 1.06 over the beat (rendered at 2x then scaled for smoothness)
            zoom = f"zoompan=z='1+0.06*on/{frames}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={frames}:s=1080x1920:fps={FPS}"
            run([FFMPEG, "-y", "-loglevel", "error", "-loop", "1", "-i", str(card), "-vf",
                 f"scale=2160:3840,{zoom},format=yuv420p", "-frames:v", str(frames),
                 "-c:v", "libx264", "-preset", "veryfast", "-crf", "23", str(clip)])
            clips.append(clip)
        lst = tmp / "list.txt"
        lst.write_text("".join(f"file '{c.as_posix()}'\n" for c in clips), encoding="utf-8")
        video = tmp / "video.mp4"
        run([FFMPEG, "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy", str(video)])
        total = sum(secs)
        if audio:
            a_in = ["-i", str(audio)]
            a_filter = ["-af", f"afade=t=out:st={max(0, total - 1.5):.2f}:d=1.5"] if kind == "music" else []
        else:
            a_in = ["-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo"]
            a_filter = []
        for crf in (23, 27, 31):
            run([FFMPEG, "-y", "-loglevel", "error", "-i", str(video), *a_in, *a_filter, "-map", "0:v", "-map", "1:a",
                 "-c:v", "libx264", "-preset", "veryfast", "-crf", str(crf), "-pix_fmt", "yuv420p",
                 "-c:a", "aac", "-b:a", "128k", "-ar", "44100", "-t", f"{total:.2f}", "-movflags", "+faststart", str(out)])
            if out.stat().st_size < MAX_MB * 1024 * 1024:
                break
    log(f"reel: {pid} -> {out.name} ({total:.0f}s, audio={kind}, {out.stat().st_size / 1e6:.1f} MB, style={style})")
    return out


# ───────────── motion-graphics reel (Remotion, in ../reel) ─────────────
REEL = ASSETS.parent / "reel"
MONTHS = "يناير|فبراير|مارس|أبريل|مايو|يونيو|يوليو|أغسطس|سبتمبر|أكتوبر|نوفمبر|ديسمبر"
DATE_RX = re.compile(rf"(\d{{1,2}}\s*[-–]\s*\d{{1,2}}\s*({MONTHS}))|(\d{{1,2}}\s*({MONTHS}))|({MONTHS})\s*\d{{4}}")


def is_date(t):
    return bool(DATE_RX.search(t))


def parse_beat(b, use_vo):
    lines = [l.strip() for l in (b.get("on_screen") or "").split("\n") if l.strip()]
    head, chips, body = "", [], []
    for i, line in enumerate(lines):
        parts = [x.strip() for x in line.split("|") if x.strip()]
        if i == 0:
            rest = [x for x in parts if not is_date(x)]
            chips += [x for x in parts if is_date(x)]
            head = " ".join(rest) or parts[0]
        elif len(line) <= 40 and (is_date(line) or "–" in line or "-" in line or len(parts) > 1):
            chips += parts
        else:
            body.append(line)
    if not body and use_vo and b.get("vo"):
        first = re.split(r"(?<=[.!؟?])\s", b["vo"].strip())[0]
        if len(first) <= 110 and first.strip() != head.strip():
            body.append(first)
    num = None
    m = re.search(r"(?<![\d–\-/])(\+?\d{1,3}(?:,\d{3})+\+?|\+?\d{2,7}(?:\.\d+)?\s?[%+]?)(?![\d–\-/x])", head)
    if m and not is_date(head[max(0, m.start() - 3): m.end() + 10]):
        num = m.group(1).strip()
    return {"headline": head, "body": "\n".join(body), "chips": chips[:3], "number": num}


def make_motion(post, date):
    beats = post.get("script") or []
    if not beats:
        return None
    if not (REEL / "node_modules").exists():
        raise RuntimeError("reel/node_modules missing (run: cd reel && npm ci)")
    pid = post["post_id"]
    _, style = style_for(post)
    style = style if style in ("pearl", "sadu", "swiss") else "sadu"
    secs = [max(2.5, beat_seconds(b.get("t"))) for b in beats]
    audio, kind = audio_for(date, pid)
    if kind == "voice":
        total = duration(audio)
        if total > 0:
            secs = [s * (total + 0.3) / sum(secs) for s in secs]
    tmp = REEL / "public" / "tmp"
    shutil.rmtree(tmp, ignore_errors=True)
    tmp.mkdir(parents=True)
    props_beats = []
    for i, (b, sec) in enumerate(zip(beats, secs), 1):
        pb = parse_beat(b, use_vo=(kind != "voice"))
        pb["seconds"] = round(sec, 2)
        bg = ASSETS / date / "bg" / f"{pid}_beat{i}.jpg"
        if bg.exists():
            shutil.copy(bg, tmp / bg.name)
            pb["bg"] = f"tmp/{bg.name}"
        props_beats.append(pb)
    props = {"style": style, "kicker": kicker(post), "handle": "@waynalyoum",
             "cta": "احفظ 📌", "ctaSub": "وأرسله لربعك", "beats": props_beats,
             "audio": None, "audioKind": kind}
    if audio:
        shutil.copy(audio, tmp / f"audio{audio.suffix}")
        props["audio"] = f"tmp/audio{audio.suffix}"
    pfile = tmp / "props.json"
    pfile.write_text(json.dumps(props, ensure_ascii=False), encoding="utf-8")
    out = ASSETS / date / f"{pid}.mp4"
    out.parent.mkdir(parents=True, exist_ok=True)
    npx = shutil.which("npx") or shutil.which("npx.cmd") or "npx"
    cmd = [npx, "remotion", "render", "src/index.ts", "Reel", str(out.resolve()), f"--props={pfile.resolve()}",
           "--codec=h264", "--crf=24", "--x264-preset=veryfast", "--audio-codec=aac", "--log=error"]
    if os.environ.get("REMOTION_BROWSER"):
        cmd.append(f"--browser-executable={os.environ['REMOTION_BROWSER']}")
    r = subprocess.run(cmd, cwd=REEL, capture_output=True, text=True)
    if r.returncode != 0 or not out.exists():
        raise RuntimeError((r.stderr or r.stdout)[-1500:])
    if out.stat().st_size > MAX_MB * 1024 * 1024:  # keep under the hosting limit
        small = out.with_suffix(".small.mp4")
        run([FFMPEG, "-y", "-loglevel", "error", "-i", str(out), "-c:v", "libx264", "-preset", "veryfast", "-crf", "30",
             "-c:a", "copy", "-movflags", "+faststart", str(small)])
        small.replace(out)
    shutil.rmtree(tmp, ignore_errors=True)
    log(f"reel: {pid} -> {out.name} motion graphics ({sum(secs):.0f}s, style={style}, audio={kind}, {out.stat().st_size / 1e6:.1f} MB)")
    return out


def make(post, date):
    try:
        return make_motion(post, date)
    except Exception as e:  # never lose the day's reel: fall back to the simple slideshow
        log(f"reel: motion render failed ({str(e)[:300]}) -> slideshow fallback")
        return make_slideshow(post, date)


def make_day(date):
    check_arabic()
    batch = normalize(read_json(CONTENT / date / "batch.json", None))
    made = [make(p, date) for p in batch["posts"] if p["format"] == "reel"]
    return [m for m in made if m]


if __name__ == "__main__":
    make_day(sys.argv[1])
