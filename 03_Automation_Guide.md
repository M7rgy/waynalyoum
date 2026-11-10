# وين اليوم — Automation & Cost-Efficiency Guide

**Stack:** Python (on your Windows PC) + Claude API + Postiz · **Runs:** daily at 06:00 Bahrain · **Target cost:** ≈ $0.10/day

---

## 1. How the pipeline spends (and doesn't spend) tokens

| Step | Agent | Tool | Tokens | Why it's cheap |
|---|---|---|---|---|
| Plan the day | CEO | `ceo.py` — rules in `config.json` | **0** | Calendar logic is code, not AI |
| Find stories | Scout | `scout.py` — Google News RSS (AR+EN) + `data/inbox.md` + `data/evergreen.json` | **0** | No LLM "browsing"; RSS is free |
| Pre-filter | Gatekeeper pass 0 | `safety.py` regex (crime, war, politics…) | **0** | Red-list news never reaches the API |
| Audit + extract facts | Gatekeeper | **Haiku 5.5**, ONE call for all ≤15 items | ~5k in / ~2k out | Cheapest model, batched |
| Write all posts + visual prompts | Creative + Visual | **Sonnet 5.5**, ONE call for the whole day | ~6k in / ~10k out | One call, compact JSON |
| Final scan | Gatekeeper pass 2 | `safety.py` strict regex on finished copy | **0** | Catches patronage/officials that slipped in |
| Slides + stories with Arabic text | Visual | `render_slides.py` (Pillow) | **0** | No Canva, no image-model cost for text cards |
| Schedule | Ops | `publish.py` → `postiz` CLI | **0** | Plain CLI calls |

### Cost estimate (third-party-reported list prices, Oct 2026 — confirm on Anthropic's pricing page)

| | Price / 1M tokens | Daily use | Daily cost |
|---|---|---|---|
| Haiku 5.5 in / out | $0.10 / $0.50 (≤100k prompt) | 5k / 2k | ≈ $0.0015 |
| Sonnet 5.5 in / out | $2 / $10 | 6k / 10k | ≈ $0.11 |
| **Total** | | | **≈ $0.11/day ≈ $3.5/month** |
| With `"use_batch_api": true` | −50% | | **≈ $1.7/month** |

> 90% of spend is Sonnet **output**. To cut further: shorter captions, 3-post days, or switch `models.creative` to Haiku for Tue/Sat (simpler formats).

### Token rules baked into the code
1. **Code before AI** — fetching, dedupe, scheduling, formatting, safety regex are all Python.
2. **One call per agent per day** — never one call per post.
3. **Cached Brand Bible** — `brand_bible.md` is the first system block with `cache_control`. Re-runs/regens the same morning read it at ~10% price. *Don't edit it daily* — every edit busts the cache.
4. **JSON-only replies** — no chatty prose to pay for.
5. **Haiku for judgment, Sonnet for language** — Haiku never writes public copy.
6. **Batch API switch** — set `"use_batch_api": true` in `config.json`: 50% off, result within minutes to an hour (fine for a 06:00 run).
7. **Evergreen bank** — slow news days fall back to `data/evergreen.json` instead of making the model "invent".

---

## 2. One-time setup (≈ 20 min)

| # | Do this | Notes |
|---|---|---|
| 1 | Install **Python 3.10+** (python.org, tick "Add to PATH") and **Node.js 18+** (nodejs.org) | Needed for the pipeline and the Postiz CLI |
| 2 | Get an **Anthropic API key** at console.anthropic.com → set a monthly spend limit (e.g. $10) | Hard cap = no surprises |
| 3 | Create a **Postiz** account (postiz.com, or self-host free) → connect **Instagram (Business/Creator)** + **TikTok** @waynalyoum | IG must be a Professional account linked to a Facebook Page |
| 4 | Double-click `agency\setup_windows.bat` | Creates venv, installs packages + Postiz CLI, registers the 06:00 task |
| 5 | Open `agency\.env` → paste `ANTHROPIC_API_KEY` | `.env` is private, never share it |
| 6 | In a terminal inside `agency\`: `postiz auth:login` | Device-flow login in the browser |
| 7 | `.venv\Scripts\python publish.py --check` | Prints integration IDs + each platform's posting **rules** — read them once |
| 8 | Paste the Instagram & TikTok IDs into `config.json → postiz.integration_ids` | |
| 9 | Test: `.venv\Scripts\python run_daily.py --dry-run` | No API cost; shows today's plan + candidates |
| 10 | Test the real thing: `.venv\Scripts\python run_daily.py --today` | Check `content\<date>\batch.md` |

---

## 3. Your 5-minute daily routine

```
06:00  PC runs run_daily.bat  →  content\<date>\batch.md  +  carousel/story JPGs  +  Postiz DRAFTS
```

1. **Read** `content\<date>\batch.md` (2 min). Fix anything in Postiz's editor or in `batch.json`.
2. **Reel:** generate the clips from the visual prompts (or grab the B-roll terms on Pexels), edit in CapCut with the script table, export `D?-01.mp4` → drop into `assets\<date>\`, run `python publish.py <date>` again.
3. **Better carousel backgrounds (optional):** drop AI images as `assets\<date>\bg\D1-02_1.jpg` etc. → `python render_slides.py <date>` → text is re-overlaid automatically.
4. **Approve** drafts in Postiz (or run `python publish.py <date> --schedule` to schedule directly once you trust it).
5. **Stories with polls/quizzes/countdowns** → post from your phone: the JPGs are in `assets\<date>\`, add the sticker in the IG app. *(Instagram's API can't add interactive stickers — that's a platform limit, not a pipeline one.)*

---

## 4. Safety architecture (why nothing off-brand gets out)

```
RSS item ──► pass 0 regex (hard red list) ──► Haiku audit (approve / hold / reject, risk 0–10)
        ──► Sonnet writes ONLY from approved FACTS ──► pass 2 strict regex (incl. patronage, officials)
        ──► Postiz DRAFT (human glance) ──► live
```

- **Hold rule:** postponed/cancelled-before events need a source ≤ 30 days old. Unconfirmed = held, listed at the top of `batch.md`.
- **Default is DRAFT** (`"create_as": "draft"`). Flip to auto-scheduling only after ~2 weeks of clean batches.
- Edit the red list in `agency\safety.py` (`RED_EN`, `RED_AR`, `SOFT_EN`, `SOFT_AR`).

---

## 5. Tuning cheat-sheet

| Want to… | Change |
|---|---|
| Different post times | `config.json → slots` |
| More/fewer posts per weekday | `config.json → weekly_mix` |
| New search topics | `config.json → scout.queries_en / queries_ar` |
| Force a topic tomorrow | Add a line + URL to `data\inbox.md` |
| Slow-news backup content | Add facts to `data\evergreen.json` |
| Allow a topic to repeat sooner | `config.json → dedupe_days` |
| Change voice / hashtags / palette | `agency\prompts\brand_bible.md` (busts cache once) |
| Use n8n later | n8n "Execute Command" node → `run_daily.bat`; keep Python as the engine |

---

## 6. Troubleshooting

| Symptom | Fix |
|---|---|
| `scout: query failed … 403` | Network/proxy blocking news.google.com — check internet or VPN; inbox + evergreen still work |
| `gatekeeper: nothing approved` | Quiet news day → add 2–3 lines to `inbox.md` or evergreen facts |
| Arabic shows as boxes on slides | Set a font that has Arabic in `config.json → render.font_paths` (Segoe UI Bold / Tahoma Bold are on every Windows PC) |
| TikTok post "succeeds" but never appears | `content_posting_method` must be `DIRECT_POST` (already set) — `UPLOAD` only drops it in your TikTok inbox |
| Postiz analytics `{"missing": true}` | `postiz posts:missing <id>` then `postiz posts:connect <id> --release-id <rid>` |
| Task didn't run | PC must be on at 06:00 — Task Scheduler → task → Settings → "Run task as soon as possible after a scheduled start is missed" |
