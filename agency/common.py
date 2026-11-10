"""Shared paths, config and small helpers for the وين اليوم pipeline."""
import json
import os
import datetime as dt
from pathlib import Path

AGENCY = Path(__file__).resolve().parent
ROOT = AGENCY.parent
PROMPTS = AGENCY / "prompts"
DATA = ROOT / "data"
CONTENT = ROOT / "content"
ASSETS = ROOT / "assets"
LOGS = DATA / "logs"

for p in (DATA, CONTENT, ASSETS, LOGS):
    p.mkdir(parents=True, exist_ok=True)


def load_env():
    """Minimal .env loader (no extra dependency)."""
    env = AGENCY / ".env"
    if env.exists():
        for line in env.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip('"'))


def config():
    return json.loads((AGENCY / "config.json").read_text(encoding="utf-8"))


def prompt(name):
    return (PROMPTS / f"{name}.md").read_text(encoding="utf-8")


def read_json(path, default):
    path = Path(path)
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path, obj):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")


def bahrain_now():
    return dt.datetime.now(dt.timezone(dt.timedelta(hours=3)))


def to_utc_iso(date_str, hhmm, offset="+03:00"):
    """'2026-10-29','20:30' (Bahrain) -> '2026-10-29T17:30:00Z'."""
    local = dt.datetime.fromisoformat(f"{date_str}T{hhmm}:00{offset}")
    return local.astimezone(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def log(msg):
    stamp = bahrain_now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{stamp}] {msg}"
    print(line)
    with open(LOGS / f"{bahrain_now():%Y-%m}.log", "a", encoding="utf-8") as f:
        f.write(line + "\n")
