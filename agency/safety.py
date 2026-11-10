"""Gatekeeper pass 0 and pass 2: free, deterministic red-list filter (Arabic + English).

Runs BEFORE the LLM (to drop obvious no-gos for free) and AFTER the Creative
agent (to catch anything that slipped into finished captions).
"""
import re

RED_EN = [
    r"politic\w*", r"election\w*", r"parliament\w*", r"diplomat\w*",
    r"sanction\w*", r"protest\w*", r"strike\b", r"military", r"army", r"missile\w*", r"war\b",
    r"attack\w*", r"tension\w*", r"conflict\w*", r"security forces", r"crime\w*", r"criminal",
    r"arrest\w*", r"police", r"court\b", r"trial\b", r"jail\w*", r"prison\w*", r"sentenc\w*",
    r"accident\w*", r"crash\w*", r"killed", r"dead\b", r"death\w*", r"died", r"fire breaks",
    r"sectarian", r"shia\b", r"sunni\b", r"clash\w*", r"layoff\w*",
    r"iran\w*", r"israel\w*", r"houthi\w*", r"drone strike",
]
# SOFT terms: fine in a SOURCE (many good events mention patronage/officials),
# but must never reach FINISHED copy. Used only in pass 2.
SOFT_EN = [r"crown prince", r"prime minister", r"minister\w*", r"ministry", r"his majesty",
           r"his highness", r"patronage", r"shaikh", r"sheikh", r"postpon\w*", r"cancel\w*"]
RED_AR = [
    "سياس", "انتخاب", "برلمان", "مجلس النواب", "مجلس الشورى", "دبلوماس", "عقوبات",
    "احتجاج", "مظاهر", "إضراب", "عسكري", "جيش", "صاروخ", "حرب", "هجوم", "توتر", "نزاع",
    "جريمة", "جرائم", "القبض", "اعتقال", "شرطة", "محكمة", "قضية", "سجن", "حكم على",
    "حادث", "تصادم", "وفاة", "توفي", "مقتل", "حريق", "طائف", "شيعة", "سنة والشيعة", "مذهب",
    "إيران", "إسرائيل", "تسريح",
]
SOFT_AR = ["وزير", "وزارة", "ولي العهد", "رئيس الوزراء", "جلالة", "سمو ", "تحت رعاية", "الشيخ", "تأجيل", "إلغاء"]

_HARD_EN = re.compile(r"\b(?:" + "|".join(RED_EN) + r")", re.IGNORECASE)
_ALL_EN = re.compile(r"\b(?:" + "|".join(RED_EN + SOFT_EN) + r")", re.IGNORECASE)


def red_hits(text: str, strict: bool = False):
    """Red-list terms found in text (empty = clean). strict=True also checks SOFT terms."""
    if not text:
        return []
    rx, ar = (_ALL_EN, RED_AR + SOFT_AR) if strict else (_HARD_EN, RED_AR)
    hits = [m.group(0) for m in rx.finditer(text)]
    hits += [w.strip() for w in ar if w in text]
    return sorted(set(h.lower() for h in hits))


def is_clean(text: str) -> bool:
    return not red_hits(text, strict=True)


def scan_post(post: dict):
    """Pass 2: scan every public-facing string in a finished post."""
    public = [post.get("hook", ""), post.get("caption_instagram", ""), post.get("caption_tiktok", "")]
    for s in post.get("script", []) or []:
        public += [s.get("on_screen", ""), s.get("vo", "")]
    for s in post.get("slides", []) or []:
        public += [s.get("headline", ""), s.get("body", "")]
    for f in post.get("frames", []) or []:
        public.append(f.get("text", ""))
    return red_hits("\n".join(public), strict=True)
