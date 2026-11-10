"""وين اليوم — 5 slide design styles for carousels (4:5) and stories (9:16).

Each style is a function  style(size, slide, ctx) -> PIL.Image
  slide = {"headline", "body", "n"}           ctx = {"total", "kicker", "handle", "bg" (path|None), "fmt"}
Fonts live in agency/fonts (all SIL Open Font License, free for commercial use).
"""
import math
import os
import random
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
FONTS = HERE / "fonts"
# Windows: Pillow needs fribidi-0.dll to shape Arabic correctly. We ship it in agency/bin.
if sys.platform == "win32" and (HERE / "bin").exists():
    os.environ["PATH"] = str(HERE / "bin") + os.pathsep + os.environ.get("PATH", "")
    try:
        os.add_dll_directory(str(HERE / "bin"))
    except Exception:
        pass

from PIL import Image, ImageDraw, ImageFilter, ImageFont, features  # noqa: E402

RAQM = features.check("raqm")
if not RAQM:
    import arabic_reshaper
    from bidi.algorithm import get_display

_EMOJI = re.compile("[\U0001F000-\U0001FAFF☀-➿️‍⃣⬀-⯿]+")
_cache = {}


# ───────────────────────── helpers ─────────────────────────
def font(name, size):
    key = (name, size)
    if key not in _cache:
        _cache[key] = ImageFont.truetype(str(FONTS / name), size)
    return _cache[key]


def wght(name, size, weight):
    """Variable font with an explicit weight axis value."""
    key = (name, size, "w", weight)
    if key not in _cache:
        f = ImageFont.truetype(str(FONTS / name), size)
        try:
            vals = []
            for a in f.get_variation_axes():
                nm = a.get("name")
                nm = nm.decode() if isinstance(nm, bytes) else str(nm)
                vals.append(weight if nm.lower().startswith("weight") else a.get("default", 0))
            f.set_variation_by_axes(vals)
        except Exception:
            pass
        _cache[key] = f
    return _cache[key]


_KEYCAP = re.compile("[0-9#*]\uFE0F?\u20E3")


def clean(t):
    t = _KEYCAP.sub("", t or "").replace("…", "...")
    t = re.sub(r"(\d)\s*[–—]\s*(\d)", r"\1-\2", t)  # "20–21" keeps its order inside RTL text
    t = re.sub(r"@([A-Za-z0-9_.]+)", "\u200e@\\1\u200e", t)  # keep @ on the left of handles in RTL text
    return "\n".join(" ".join(_EMOJI.sub("", ln).split()) for ln in t.split("\n")).strip()


def shape(s):
    return s if RAQM else get_display(arabic_reshaper.reshape(s))


def tw(draw, s, f):
    return draw.textlength(shape(s), font=f, **({"direction": "rtl"} if RAQM else {}))


def wrap(draw, text, f, max_w):
    out = []
    for para in clean(text).split("\n"):
        line = ""
        for w in para.split():
            trial = (line + " " + w).strip()
            if not line or tw(draw, trial, f) <= max_w:
                line = trial
            else:
                out.append(line)
                line = w
        if line:
            out.append(line)
    return out


def fit(draw, text, fontfn, max_w, max_lines, start, minimum):
    """Largest font size (from start down to minimum) where text fits in max_lines."""
    size = start
    while size > minimum:
        f = fontfn(size)
        lines = wrap(draw, text, f, max_w)
        if len(lines) <= max_lines:
            return f, lines
        size -= 4
    f = fontfn(minimum)
    return f, wrap(draw, text, f, max_w)


def put(draw, s, f, x, y, fill, anchor_x="right"):
    """Draw one RTL line. x = right edge (right), centre (center) or left edge (left)."""
    if not re.search("[\u0600-\u06FF]", s):  # pure Latin (handles, counters) -> plain LTR
        w = draw.textlength(s, font=f)
        left = {"right": x - w, "center": x - w / 2, "left": x}[anchor_x]
        draw.text((left, y), s, font=f, fill=fill)
        return w
    s = re.sub(r"(?<!\u200e)@([A-Za-z0-9_.]+)", "\u200e@\\1\u200e", s)
    w = tw(draw, s, f)
    left = {"right": x - w, "center": x - w / 2, "left": x}[anchor_x]
    draw.text((left, y), shape(s), font=f, fill=fill, **({"direction": "rtl"} if RAQM else {}))
    return w


def block(draw, lines, f, x, y, fill, align="right", gap=1.25):
    lh = int(f.size * gap)
    for ln in lines:
        put(draw, ln, f, x, y, fill, align)
        y += lh
    return y


def block_h(lines, f, gap=1.25):
    return int(f.size * gap) * len(lines)


def cover(path, size):
    im = Image.open(path).convert("RGB")
    W, H = size
    s = max(W / im.width, H / im.height)
    im = im.resize((math.ceil(im.width * s), math.ceil(im.height * s)), Image.LANCZOS)
    l, t = (im.width - W) // 2, (im.height - H) // 2
    return im.crop((l, t, l + W, t + H))


def hexc(h, a=255):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)) + (a,)


def first_number(text):
    m = re.search(r"[+]?\d[\d,\.]*\s?%?", clean(text))
    return m.group(0).strip() if m else None


def grain(im, amount=10, seed=7):
    rnd = random.Random(seed)
    noise = Image.effect_noise(im.size, amount).convert("L")
    return Image.blend(im.convert("RGB"), Image.merge("RGB", (noise, noise, noise)), 0.04)


# ───────────────────────── 1. لؤلؤ  Pearl Editorial ─────────────────────────
def pearl(size, sl, ctx):
    W, H = size
    C = dict(bg="#F6F1E7", ink="#0B2A43", sub="#4A5560", acc="#E4664F", sand="#CDAE78")
    im = Image.new("RGBA", size, hexc(C["bg"]))
    d = ImageDraw.Draw(im)
    m = int(W * 0.085)
    R = W - m
    # top bar
    put(d, ctx["handle"], font("IBMPlexSansArabic-Medium.ttf", int(W * .026)), m, int(H * .045), hexc(C["sub"]), "left")
    put(d, ctx["kicker"], font("IBMPlexSansArabic-Bold.ttf", int(W * .026)), R, int(H * .045), hexc(C["acc"]))
    d.line([(m, int(H * .085)), (R, int(H * .085))], fill=hexc(C["sand"]), width=2)
    # visual: arch window (photo inside if provided)
    top, bot = int(H * .12), int(H * (.50 if ctx["fmt"] == "carousel" else .46))
    aw = int(W * .56)
    ax0, ax1 = R - aw, R
    mask = Image.new("L", size, 0)
    md = ImageDraw.Draw(mask)
    md.rectangle([ax0, top + aw // 2, ax1, bot], fill=255)
    md.ellipse([ax0, top, ax1, top + aw], fill=255)
    if ctx.get("bg"):
        im.paste(cover(ctx["bg"], size).convert("RGBA"), (0, 0), mask)
    else:
        fill = Image.new("RGBA", size, hexc("#E7D9BD"))
        fd = ImageDraw.Draw(fill)
        for i in range(9):  # concentric pearl rings
            r = int(aw * (.15 + i * .07))
            cx, cy = (ax0 + ax1) // 2, int(top + aw * .55)
            fd.ellipse([cx - r, cy - r, cx + r, cy + r], outline=hexc(C["sand"]), width=3)
        fd.ellipse([(ax0 + ax1) // 2 - aw // 9, int(top + aw * .55) - aw // 9, (ax0 + ax1) // 2 + aw // 9, int(top + aw * .55) + aw // 9], fill=hexc("#FFFFFF"))
        im.paste(fill, (0, 0), mask)
    d.arc([ax0 - 14, top - 14, ax1 + 14, top + aw + 14], 180, 360, fill=hexc(C["sand"]), width=3)
    # big index number
    num = f"{sl['n']:02d}"
    put(d, num, font("Amiri-Bold.ttf", int(W * .20)), m, top - int(W * .02), hexc(C["acc"]), "left")
    # headline + body
    y = bot + int(H * .045)
    hf, hl = fit(d, sl["headline"], lambda s: font("Amiri-Bold.ttf", s), R - m, 3, int(W * .095), int(W * .06))
    y = block(d, hl, hf, R, y, hexc(C["ink"]), gap=1.35)
    d.line([(R - int(W * .12), y + 10), (R, y + 10)], fill=hexc(C["acc"]), width=6)
    y += int(H * .035)
    bf, bl = fit(d, sl["body"], lambda s: font("IBMPlexSansArabic-Medium.ttf", s), R - m, 6, int(W * .042), int(W * .032))
    block(d, bl, bf, R, y, hexc(C["sub"]), gap=1.55)
    # progress dots
    tot = ctx["total"]
    for i in range(tot):
        x = m + i * 26
        d.ellipse([x, H - int(H * .05), x + 12, H - int(H * .05) + 12], fill=hexc(C["ink"] if i < sl["n"] else C["sand"]))
    put(d, "وين اليوم", font("Amiri-Bold.ttf", int(W * .034)), R, H - int(H * .062), hexc(C["ink"]))
    return im.convert("RGB")


# ───────────────────────── 2. ليل المنامة  Night Pop ─────────────────────────
def night(size, sl, ctx):
    W, H = size
    C = dict(bg="#0A0F24", acc="#FF5E4D", acc2="#2EE6C5", yel="#FFD23F", txt="#FFFFFF", sub="#B9C2E0")
    base = Image.new("RGB", size, hexc(C["bg"])[:3])
    if ctx.get("bg"):
        ph = cover(ctx["bg"], size)
        base = Image.blend(ph, base, 0.72)
    glow = Image.new("RGB", size, (0, 0, 0))
    g = ImageDraw.Draw(glow)
    rnd = random.Random(sl["n"])
    for col, r in ((C["acc"], .55), (C["acc2"], .45), ("#5B3DF5", .5)):
        cx, cy = rnd.randint(0, W), rnd.randint(0, H)
        rr = int(W * r)
        g.ellipse([cx - rr, cy - rr, cx + rr, cy + rr], fill=hexc(col)[:3])
    glow = glow.filter(ImageFilter.GaussianBlur(W // 5))
    im = Image.blend(base, glow, 0.35).convert("RGBA")
    d = ImageDraw.Draw(im)
    m = int(W * .08)
    R = W - m
    # top: counter pill + handle
    pf = font("ReadexPro.ttf", int(W * .03))
    pill = f"{sl['n']}/{ctx['total']}"
    pw = d.textlength(pill, font=pf)
    d.rounded_rectangle([m, int(H * .045), m + pw + 44, int(H * .045) + int(W * .058)], radius=40, outline=hexc(C["sub"]), width=2)
    d.text((m + 22, int(H * .045) + int(W * .011)), pill, font=pf, fill=hexc(C["sub"]))
    put(d, ctx["handle"], font("ReadexPro.ttf", int(W * .03)), R, int(H * .05), hexc(C["sub"]))
    # headline (Lalezar), each line on a highlight bar; first line accent colour
    hf, hl = fit(d, sl["headline"], lambda s: font("Lalezar-Regular.ttf", s), R - m - 40, 3, int(W * .13), int(W * .075))
    bf, bl = fit(d, sl["body"], lambda s: font("Tajawal-Medium.ttf", s), R - m, 5, int(W * .046), int(W * .034))
    lh = int(hf.size * 1.32)
    total_h = lh * len(hl) + int(H * .05) + block_h(bl, bf, 1.5)
    y = max(int(H * .2), (H - total_h) // 2 - int(H * .02))
    for i, ln in enumerate(hl):
        w = tw(d, ln, hf)
        pad = 22
        colr = C["acc"] if i == 0 else C["yel"] if i == 1 else C["acc2"]
        d.rounded_rectangle([R - w - pad * 2, y + int(hf.size * .12), R, y + int(hf.size * 1.18)], radius=18, fill=hexc(colr))
        put(d, ln, hf, R - pad, y, hexc(C["bg"]))
        y += lh
    y += int(H * .05)
    block(d, bl, bf, R, y, hexc(C["txt"]), gap=1.5)
    # footer
    if sl["n"] == 1:
        af = font("Lalezar-Regular.ttf", int(W * .05))
        ay = H - int(H * .085)
        aw = put(d, "اسحب", af, m + 90, ay, hexc(C["acc2"]), "left")
        cy = ay + int(af.size * .62)
        d.line([(m + 10, cy), (m + 75, cy)], fill=hexc(C["acc2"]), width=7)
        d.polygon([(m, cy), (m + 28, cy - 18), (m + 28, cy + 18)], fill=hexc(C["acc2"]))
    else:
        bar_w = (R - m) * sl["n"] / max(ctx["total"], 1)
        d.rounded_rectangle([m, H - int(H * .05), R, H - int(H * .05) + 8], radius=4, fill=hexc("#FFFFFF", 50))
        d.rounded_rectangle([R - bar_w, H - int(H * .05), R, H - int(H * .05) + 8], radius=4, fill=hexc(C["acc2"]))
    put(d, "وين اليوم", font("Lalezar-Regular.ttf", int(W * .045)), R, H - int(H * .1), hexc(C["txt"]))
    return im.convert("RGB")


# ───────────────────────── 3. مجلة  Photo Magazine ─────────────────────────
def magazine(size, sl, ctx):
    W, H = size
    if ctx.get("bg"):
        im = cover(ctx["bg"], size).convert("RGBA")
    else:  # placeholder "photo": warm sunset duotone with sea + dhow silhouette
        im = Image.new("RGBA", size)
        g = ImageDraw.Draw(im)
        for y in range(H):
            t = y / H
            a, b = hexc("#F4A259"), hexc("#3A1C4A")
            g.line([(0, y), (W, y)], fill=tuple(int(a[i] * (1 - t) + b[i] * t) for i in range(3)) + (255,))
        sun_r = int(W * .16)
        g.ellipse([W * .58 - sun_r, H * .36 - sun_r, W * .58 + sun_r, H * .36 + sun_r], fill=hexc("#FFE2A8"))
        g.rectangle([0, int(H * .44), W, H], fill=hexc("#22163A"))
        # dhow
        bx, by = int(W * .3), int(H * .44)
        g.polygon([(bx - 120, by - 8), (bx + 140, by - 8), (bx + 100, by + 30), (bx - 90, by + 30)], fill=hexc("#140C24"))
        g.polygon([(bx, by - 10), (bx, by - 260), (bx + 150, by - 30)], fill=hexc("#140C24"))
        g.line([(bx, by - 10), (bx, by - 280)], fill=hexc("#140C24"), width=6)
        im = grain(im).convert("RGBA")
    # bottom gradient
    grad = Image.new("L", (1, H))
    for y in range(H):
        grad.putpixel((0, y), int(255 * max(0, (y / H - .32) / .68) ** 1.2 * .92))
    shade = Image.new("RGBA", size, (8, 10, 20, 255))
    shade.putalpha(grad.resize(size))
    im = Image.alpha_composite(im, shade)
    d = ImageDraw.Draw(im)
    m = int(W * .075)
    R = W - m
    # masthead
    put(d, "وين اليوم", font("Tajawal-Black.ttf", int(W * .05)), R, int(H * .04), hexc("#FFFFFF"))
    put(d, ctx["handle"], font("Tajawal-Medium.ttf", int(W * .028)), m, int(H * .052), hexc("#FFFFFF", 220), "left")
    d.line([(m, int(H * .105)), (R, int(H * .105))], fill=hexc("#FFFFFF", 120), width=2)
    # text from the bottom up
    bf, bl = fit(d, sl["body"], lambda s: font("Tajawal-Medium.ttf", s), R - m, 4, int(W * .043), int(W * .033))
    hf, hl = fit(d, sl["headline"], lambda s: font("Tajawal-Black.ttf", s), R - m, 3, int(W * .11), int(W * .07))
    y = H - int(H * .09) - block_h(bl, bf, 1.5)
    y_body = y
    y -= int(H * .03) + block_h(hl, hf, 1.18)
    y_head = y
    # kicker pill
    kf = font("Tajawal-Bold.ttf", int(W * .03))
    kw = tw(d, ctx["kicker"], kf)
    ky = y_head - int(W * .085)
    d.rounded_rectangle([R - kw - 44, ky, R, ky + int(W * .058)], radius=10, fill=hexc("#FF5E4D"))
    put(d, ctx["kicker"], kf, R - 22, ky + int(W * .008), hexc("#FFFFFF"))
    block(d, hl, hf, R, y_head, hexc("#FFFFFF"), gap=1.18)
    block(d, bl, bf, R, y_body, hexc("#E8E8EE"), gap=1.5)
    # page count
    put(d, f"{sl['n']:02d} / {ctx['total']:02d}", font("Tajawal-Bold.ttf", int(W * .028)), m, H - int(H * .05), hexc("#FFFFFF", 200), "left")
    return im.convert("RGB")


# ───────────────────────── 4. سدو  Sadu Heritage ─────────────────────────
def _sadu_band(d, x0, y0, x1, h, C):
    d.rectangle([x0, y0, x1, y0 + h], fill=hexc(C["red"]))
    unit = h
    for i, x in enumerate(range(x0, x1, unit)):
        cx, cy = x + unit / 2, y0 + h / 2
        col = C["cream"] if i % 2 == 0 else C["black"]
        d.polygon([(cx, y0 + 6), (x + unit - 6, cy), (cx, y0 + h - 6), (x + 6, cy)], fill=hexc(col))
        d.polygon([(cx, cy - h * .18), (cx + h * .18, cy), (cx, cy + h * .18), (cx - h * .18, cy)], fill=hexc(C["red"]))
    for yy in (y0 - 14, y0 + h + 6):
        for i, x in enumerate(range(x0, x1, 28)):
            d.polygon([(x, yy + 8), (x + 14, yy), (x + 28, yy + 8)], fill=hexc(C["black"] if i % 2 else C["red"]))


def sadu(size, sl, ctx):
    W, H = size
    C = dict(bg="#EBDDBF", red="#9E2A1E", black="#1E1A17", cream="#F7EEDC", sub="#4B3B2E")
    im = Image.new("RGBA", size, hexc(C["bg"]))
    d = ImageDraw.Draw(im)
    band = int(W * .07)
    _sadu_band(d, 0, int(H * .035), W, band, C)
    _sadu_band(d, 0, H - int(H * .035) - band, W, band, C)
    m = int(W * .1)
    R = W - m
    inner_top, inner_bot = int(H * .035) + band + int(H * .05), H - int(H * .035) - band - int(H * .05)
    if ctx.get("bg"):  # photo framed like a woven panel
        ph = cover(ctx["bg"], (R - m, int((inner_bot - inner_top) * .42)))
        im.paste(ph, (m, inner_top))
        d.rectangle([m - 8, inner_top - 8, R + 8, inner_top + ph.height + 8], outline=hexc(C["red"]), width=6)
        content_top = inner_top + ph.height + int(H * .05)
    else:
        content_top = inner_top + int(H * .04)
    # diamond with number
    cx = W // 2
    s = int(W * .075)
    cy = content_top + s
    d.polygon([(cx, cy - s), (cx + s, cy), (cx, cy + s), (cx - s, cy)], fill=hexc(C["red"]))
    d.polygon([(cx, cy - s + 12), (cx + s - 12, cy), (cx, cy + s - 12), (cx - s + 12, cy)], outline=hexc(C["cream"]), width=3)
    nf = font("ReemKufi.ttf", int(s * .9))
    nt = str(sl["n"])
    d.text((cx - d.textlength(nt, font=nf) / 2, cy - nf.size * .62), nt, font=nf, fill=hexc(C["cream"]))
    y = cy + s + int(H * .04)
    hf, hl = fit(d, sl["headline"], lambda z: wght("ReemKufi.ttf", z, 700), R - m, 3, int(W * .1), int(W * .062))
    y = block(d, hl, hf, cx, y, hexc(C["black"]), align="center", gap=1.4)
    # ornament divider
    for i, dx in enumerate((-60, 0, 60)):
        r = 9 if dx == 0 else 6
        d.polygon([(cx + dx, y + 18 - r), (cx + dx + r, y + 18), (cx + dx, y + 18 + r), (cx + dx - r, y + 18)], fill=hexc(C["red"]))
    y += int(H * .05)
    bf, bl = fit(d, sl["body"], lambda z: font("IBMPlexSansArabic-Medium.ttf", z), R - m, 6, int(W * .044), int(W * .033))
    block(d, bl, bf, cx, y, hexc(C["sub"]), align="center", gap=1.55)
    tag = f"وين اليوم  •  {ctx['handle']}"
    put(d, tag, font("IBMPlexSansArabic-Bold.ttf", int(W * .027)), cx, inner_bot - int(H * .005), hexc(C["red"]), "center")
    return im.convert("RGB")


# ───────────────────────── 5. شبكة  Swiss Data ─────────────────────────
def swiss(size, sl, ctx):
    W, H = size
    C = dict(bg="#FFFFFF", blue="#0E4C92", ink="#111418", sub="#5B6470", acc="#FF5E4D", line="#E3E6EA")
    im = Image.new("RGBA", size, hexc(C["bg"]))
    d = ImageDraw.Draw(im)
    m = int(W * .07)
    R = W - m
    block_h_px = int(H * (.42 if ctx["fmt"] == "carousel" else .38))
    if ctx.get("bg"):
        ph = cover(ctx["bg"], (W, block_h_px))
        blue = Image.new("RGB", ph.size, hexc(C["blue"])[:3])
        im.paste(Image.blend(ph.convert("L").convert("RGB"), blue, .55), (0, 0))
    else:
        d.rectangle([0, 0, W, block_h_px], fill=hexc(C["blue"]))
        for x in range(0, W, int(W / 12)):  # faint grid
            d.line([(x, 0), (x, block_h_px)], fill=hexc("#FFFFFF", 28), width=1)
    d.rectangle([R - int(W * .06), block_h_px - int(W * .03), R, block_h_px + int(W * .03)], fill=hexc(C["acc"]))
    # hero number (first number in headline/body, else slide index)
    hero = first_number(sl["headline"]) or first_number(sl["body"]) or f"{sl['n']:02d}"
    hfnt = wght("Cairo.ttf", int(W * .27), 900)
    while d.textlength(hero, font=hfnt) > R - m and hfnt.size > 60:
        hfnt = wght("Cairo.ttf", hfnt.size - 10, 900)
    bb = d.textbbox((0, 0), hero, font=hfnt)
    d.text((m - bb[0], block_h_px - int(H * .045) - bb[3]), hero, font=hfnt, fill=hexc("#FFFFFF"))
    put(d, ctx["kicker"], wght("Cairo.ttf", int(W * .03), 700), R, int(H * .04), hexc("#FFFFFF"))
    d.text((m, int(H * .04)), f"{sl['n']:02d} / {ctx['total']:02d}", font=wght("Cairo.ttf", int(W * .03), 700), fill=hexc("#FFFFFF"))
    # text
    y = block_h_px + int(H * .06)
    hf, hl = fit(d, sl["headline"], lambda s: wght("Cairo.ttf", s, 800), R - m, 3, int(W * .085), int(W * .056))
    y = block(d, hl, hf, R, y, hexc(C["ink"]), gap=1.3)
    y += int(H * .015)
    d.line([(m, y), (R, y)], fill=hexc(C["line"]), width=3)
    y += int(H * .03)
    bf, bl = fit(d, sl["body"], lambda s: wght("Cairo.ttf", s, 500), R - m, 6, int(W * .042), int(W * .032))
    block(d, bl, bf, R, y, hexc(C["sub"]), gap=1.55)
    # footer
    d.line([(m, H - int(H * .08)), (R, H - int(H * .08))], fill=hexc(C["ink"]), width=3)
    put(d, "وين اليوم", wght("Cairo.ttf", int(W * .036), 900), R, H - int(H * .068), hexc(C["ink"]))
    d.text((m, H - int(H * .066)), ctx["handle"], font=wght("Cairo.ttf", int(W * .028), 600), fill=hexc(C["sub"]))
    return im.convert("RGB")


STYLES = {
    "pearl": ("لؤلؤ — Pearl Editorial", pearl),
    "night": ("ليل المنامة — Night Pop", night),
    "magazine": ("مجلة — Photo Magazine", magazine),
    "sadu": ("سدو — Sadu Heritage", sadu),
    "swiss": ("شبكة — Swiss Data", swiss),
}
