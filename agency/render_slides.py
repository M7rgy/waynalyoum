"""Visual helper: turns carousel slides & story frames into finished JPGs with Arabic text.

  python render_slides.py 2026-11-10                 # render that day in the style set in config.json
  python render_slides.py 2026-11-10 --style night   # override the style for this run
  python render_slides.py --samples                  # render the same carousel in all 5 styles to compare

Style is picked per post from its "post_type" (config.json -> render.style_by_type):
  info -> pearl   |   local -> sadu   |   international -> swiss   (all 5 styles still available via --style)
Optional AI backgrounds: assets/<date>/bg/<post_id>_<n>.jpg  (used by every style when present)
Output: assets/<date>/<post_id>_<n>.jpg  (the exact names publish.py expects)
"""
import argparse
import sys

from common import ASSETS, CONTENT, config, read_json
from render import normalize
import slide_styles as S

SKIP_TAGS = {"#وين_اليوم", "#البحرين", "#الخليج", "#bahrain", "#visitbahrain"}


def kicker(post):
    for t in post.get("hashtags", []):
        if t.lower() not in SKIP_TAGS and not t.isascii():
            return t.lstrip("#").replace("_", " ")
    return {"carousel": "وين نروح؟", "story": "اليوم"}.get(post["format"], "البحرين")


def check_arabic():
    if not S.RAQM:
        print("⚠️  Arabic text shaping is OFF (Pillow can't find fribidi). Slides would come out broken.")
        print(f"   Make sure this file exists: {S.HERE / 'bin' / 'fribidi-0.dll'}")
        print("   If it does, copy it next to python.exe (run:  where python) and try again.")
        sys.exit(1)


def render_post(post, date, style_key, out, bg_dir):
    fn = S.STYLES[style_key][1]
    made = []
    items = post["slides"] if post["format"] == "carousel" else post["frames"] if post["format"] == "story" else []
    size = (1080, 1350) if post["format"] == "carousel" else (1080, 1920)
    for it in items:
        if post["format"] == "story":
            head, *rest = (it.get("text") or "").split("\n")
            slide = {"headline": head, "body": "\n".join(rest), "n": it["n"]}
        else:
            slide = {"headline": it.get("headline", ""), "body": it.get("body", ""), "n": it["n"]}
        name = f"{post['post_id']}_{it['n']}.jpg"
        bg = bg_dir / name
        ctx = {"total": len(items), "kicker": kicker(post), "handle": config().get("handle", "@waynalyoum"),
               "bg": bg if bg.exists() else None, "fmt": post["format"]}
        out.mkdir(parents=True, exist_ok=True)
        fn(size, slide, ctx).save(out / name, "JPEG", quality=92)
        made.append(name)
    return made


def style_for(post):
    r = config()["render"]
    t = (post.get("post_type") or r.get("default_type", "local")).lower()
    return t, r["style_by_type"].get(t, r["style_by_type"][r.get("default_type", "local")])


def render_day(date, style_key=None):
    check_arabic()
    batch = normalize(read_json(CONTENT / date / "batch.json", None))
    out, bg = ASSETS / date, ASSETS / date / "bg"
    made = []
    for p in batch["posts"]:
        t, key = (p.get("post_type", "-"), style_key) if style_key else style_for(p)
        names = render_post(p, date, key, out, bg)
        if names:
            print(f"{p['post_id']:>7}  {t:<13} -> {key:<8} ({len(names)} images)")
        made += names
    print(f"rendered {len(made)} images -> {out}")
    return made


def samples(date="2026-10-29", post_id="D1-02"):
    """Same carousel in all 5 styles + a story frame, plus one comparison sheet per style."""
    check_arabic()
    from PIL import Image
    batch = normalize(read_json(CONTENT / date / "batch.json", None))
    post = next(p for p in batch["posts"] if p["post_id"] == post_id)
    story = {"post_id": "STORY", "format": "story", "hashtags": ["#رياضة"],
             "frames": [{"n": 1, "text": "أقوى بطولات 3x3 بالعالم جاية المنامة\nالأفنيوز – المنامة\n20–21 نوفمبر"}]}
    root = ASSETS / "style_samples"
    for key, (label, _) in S.STYLES.items():
        d = root / key
        names = render_post(post, date, key, d, ASSETS / date / "bg") + render_post(story, date, key, d, ASSETS / date / "bg")
        thumbs = [Image.open(d / n).resize((432, 540)) for n in names[:1] + names[1:2] + names[3:4] + names[-2:-1]]
        st = Image.open(d / names[-1]).resize((304, 540))
        sheet = Image.new("RGB", (432 * 4 + 304 + 50, 580), (24, 24, 28))
        x = 10
        for im in thumbs + [st]:
            sheet.paste(im, (x, 20))
            x += im.width + 10
        sheet.save(root / f"{key}.jpg", quality=88)
        print(f"{key:<9} {label}  -> {root / (key + '.jpg')}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("date", nargs="?")
    ap.add_argument("--style", choices=list(S.STYLES))
    ap.add_argument("--samples", action="store_true")
    a = ap.parse_args()
    if a.samples:
        samples()
    elif a.date:
        render_day(a.date, a.style)
    else:
        ap.print_help()
