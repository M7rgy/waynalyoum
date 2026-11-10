"""Agent 1 — Scout. Zero tokens: fetches Google News RSS (AR + EN), your inbox, and the evergreen bank."""
import datetime as dt
import email.utils
import hashlib
import html
import re
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

from common import DATA, config, read_json, log
from safety import red_hits

UA = {"User-Agent": "Mozilla/5.0 (waynalyoum-scout)"}


def _rss(query, lang):
    hl, ceid = ("ar", "BH:ar") if lang == "ar" else ("en-BH", "BH:en")
    url = "https://news.google.com/rss/search?" + urllib.parse.urlencode(
        {"q": f"{query} when:21d", "hl": hl, "gl": "BH", "ceid": ceid})
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=20) as r:
            root = ET.fromstring(r.read())
    except Exception as e:  # network hiccup -> skip this query
        log(f"scout: query failed '{query}': {e}")
        return []
    items = []
    for it in root.iter("item"):
        title = html.unescape(it.findtext("title", ""))
        desc = re.sub("<[^>]+>", " ", html.unescape(it.findtext("description", "")))
        pub = it.findtext("pubDate", "")
        try:
            published = email.utils.parsedate_to_datetime(pub)
        except Exception:
            published = None
        items.append({"title": title.strip(), "summary": " ".join(desc.split())[:400],
                      "url": it.findtext("link", ""), "published": published.isoformat() if published else None,
                      "lang": lang, "origin": "rss"})
    return items


def _inbox():
    """Lines you add to data/inbox.md (one idea + URL per line) are always considered first."""
    path = DATA / "inbox.md"
    if not path.exists():
        return []
    out = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip("-* ").strip()
        if line and not line.startswith("#"):
            url = (re.findall(r"https?://\S+", line) or [""])[0]
            out.append({"title": line.replace(url, "").strip(), "summary": line, "url": url,
                        "published": None, "lang": "mixed", "origin": "inbox"})
    return out


def _evergreen(used_keys):
    bank = read_json(DATA / "evergreen.json", [])
    return [dict(e, origin="evergreen") for e in bank if e.get("topic_key") not in used_keys]


def run(used_keys, limit=None):
    cfg = config()["scout"]
    caps = cfg["max_candidates"] if isinstance(cfg["max_candidates"], dict) else {"bahrain": cfg["max_candidates"], "gcc": 0}
    raw = _inbox()
    for scope, keys in (("bahrain", ("queries_en", "queries_ar")), ("gcc", ("queries_gcc_en", "queries_gcc_ar"))):
        for k in keys:
            for q in cfg.get(k, []):
                for it in _rss(q, "ar" if k.endswith("_ar") else "en"):
                    it["scope_hint"] = scope
                    raw.append(it)

    seen, clean = set(), []
    cutoff = dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=cfg["max_age_days"])
    for item in raw:
        key = re.sub(r"\W+", "", item["title"].lower())[:60]
        if not key or key in seen:
            continue
        seen.add(key)
        if item["published"] and dt.datetime.fromisoformat(item["published"]) < cutoff:
            continue
        if red_hits(item["title"] + " " + item["summary"]):
            continue  # free pre-filter: never pay tokens for red-list news
        item["id"] = hashlib.md5(key.encode()).hexdigest()[:8]
        clean.append(item)

    # inbox first, then newest news; evergreen tops up if the news day is thin
    clean.sort(key=lambda x: (x["origin"] != "inbox", -(dt.datetime.fromisoformat(x["published"]).timestamp() if x["published"] else 0)))
    bh = [x for x in clean if x.get("scope_hint", "bahrain") == "bahrain"][: caps["bahrain"]]
    gc = [x for x in clean if x.get("scope_hint") == "gcc"][: caps["gcc"]]
    picked = bh + gc
    if len(bh) < 8:
        picked += _evergreen(used_keys)[: 8 - len(bh)]
    log(f"scout: {len(raw)} raw -> {len(clean)} clean -> {len(bh)} bahrain + {len(gc)} gcc candidates")
    return picked
