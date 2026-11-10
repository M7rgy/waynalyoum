# وين اليوم | @waynalyoum — Agency Operating Manual

> **Internal codename:** Bahrain Positive Pulse (نبض البحرين الإيجابي)
> **Public brand:** وين اليوم — "where to go, what to see, what's happening in Bahrain today"
> **Platforms:** Instagram + TikTok (@waynalyoum)
> **Audience:** GCC — Riyadh, Eastern Province, Dubai, Kuwait, Doha, Muscat, Manama
> **Output:** 3–5 posts/day · no-face · AI visuals + stock B-roll · scheduled via Postiz

---

## 1. Mission & positioning

**English:** وين اليوم is the GCC's go-to answer to *"where should we go in Bahrain?"* — events, places, heritage, food, innovation and people worth celebrating. Every post either gives the viewer **a plan** (go here, on this date) or **a reason to be proud / curious** (did you know…).

**عربي:** "وين اليوم" هو الجواب اليومي لكل خليجي يسأل: *وين نروح في البحرين؟* فعاليات، أماكن، تراث، أكل، ابتكار، وقصص ناس تفرّح. كل منشور يا يعطيك **خطة** (روح هنا، بهالتاريخ)، يا يعطيك **سبب تفتخر أو تنبهر**.

### The 3-second test
Before anything ships, the post must answer one of:
1. **وين؟** (a place / event with date + location)
2. **ليش؟** (a reason it's worth your weekend)
3. **تدري إن…؟** (a verified, surprising positive fact)

---

## 2. Hard boundaries — "الخطوط الحمراء"

| ✅ Allowed (green list) | ❌ Banned (red list — reject immediately) |
|---|---|
| Events, festivals, concerts, exhibitions | Politics, elections, parliament, diplomacy, sanctions |
| Tourism, hotels, beaches, islands, food spots | Political figures — incl. royal patronage lines, ministers' statements, officials' photos |
| Heritage, museums, UNESCO sites, crafts | Crime, accidents, court cases, arrests, deaths |
| Startups, tech, economy milestones (numbers only) | Sectarian or religious debate of any kind |
| Sports achievements & tournaments | Regional tensions, war, security, military |
| Arts, music, film, design, youth success | Protests, strikes, labour disputes, prices/inflation complaints |
| Community initiatives, environment, wildlife | Anything comparing GCC countries negatively |
| **Scope:** Bahrain + positive GCC news (KSA, UAE, Kuwait, Qatar, Oman) + Bahrain on the international stage | Non-GCC world news |

**Borderline = reject.** No appeals inside the pipeline. A human can override manually.

**Patronage rule:** Many Bahrain events run "under the patronage of…". We **drop that line** and never name or show officials. We name the *event, venue, date, organiser brand* only.

**Postponement rule:** If an event was ever postponed, the Gatekeeper must find a source **dated within the last 30 days** confirming the current dates, or the post is held. (Live example: Bahrain Comic Con 2026 was postponed in March; November dates were "listed" but venue/lineup unconfirmed → **held** from the Day 1 batch.)

---

## 3. The agent team

```
          ┌──────────────── CEO (Orchestrator) ────────────────┐
          │ picks today's mix · enforces voice · final sign-off │
          └──────────────┬──────────────────────────────────────┘
                         ▼
 ① SCOUT (Research & Trend) ──► ② GATEKEEPER (Fact & Safety) ──► ③ CREATIVE (Copy)
   RSS + inbox + evergreen        blocklist + LLM audit          Reels · Carousels · Stories · Captions
                                   + source-date check                     │
                                                                           ▼
                         ⑤ OPS (Publisher) ◄──────────── ④ VISUAL DIRECTOR (Assets)
                         Postiz drafts → schedule          AI image/video prompts + B-roll cues
```

| # | Agent | Input | Output | Engine | Cost profile |
|---|---|---|---|---|---|
| 0 | **CEO** | Calendar rules, yesterday's log | `plan.json` — today's mix + slots | Pure Python (rules) | **0 tokens** |
| 1 | **Scout** | Google News RSS (AR+EN), `inbox.md`, evergreen bank | `candidates.json` (≤15 items) | Python fetch + keyword filter | **0 tokens** |
| 2 | **Gatekeeper** | candidates | `approved.json` with facts, dates, source URLs, risk score | Python blocklist → **Haiku** (one batched call) | Tiny |
| 3 | **Creative** | approved facts + plan + Brand Bible (cached) | full post copy per format | **Sonnet** (one call for the whole day) | Main spend |
| 4 | **Visual Director** | post copy | image/video prompts, B-roll search terms, text-overlay specs | Same Sonnet call as #3 | Shared |
| 5 | **Ops** | final JSON | Postiz payloads → **drafts** in Postiz; `batch.md` for human review | Python + `postiz` CLI | 0 tokens |
| 6 | **Gatekeeper pass 2** | final copy | re-scan finished captions for red-list words | Python regex | 0 tokens |

> Design principle: **LLMs only where judgment or language is needed.** Fetching, filtering, scheduling, formatting = plain code.

---

## 4. Daily rhythm (Bahrain time, UTC+3)

| Time | Step | Who |
|---|---|---|
| 06:00 | Pipeline runs (Task Scheduler) | Scout → Gatekeeper → Creative → Ops |
| 06:05 | `content/YYYY-MM-DD/batch.md` ready + Postiz drafts created | Ops |
| 06:05–12:00 | **Human check (5 min):** skim batch.md, drop generated images into `assets/YYYY-MM-DD/`, run `publish.py` | Ali |
| 13:00 | Story 1 | Postiz |
| 17:30 | Carousel 1 | Postiz |
| 19:30 | Story 2 | Postiz |
| 20:30 | Reel / TikTok (GCC prime time) | Postiz |
| 21:30 | Carousel 2 (or skip on 3-post days) | Postiz |

Thursday & Friday = GCC weekend planning nights → always include a **"وين نروح الويكند؟"** post.

---

## 5. Content mix (CEO rules)

| Day | Mix | Theme anchor |
|---|---|---|
| Sun | 1 Reel · 1 Carousel · 1 Story | تدري إن… (facts / heritage) |
| Mon | 1 Reel · 2 Stories | Innovation & youth (startups, students, creators) |
| Tue | 1 Carousel · 2 Stories | Food & cafés |
| Wed | 1 Reel · 2 Carousels · 2 Stories | **Weekend guide** — what's on Thu–Sat |
| Thu | 1 Reel · 1 Carousel · 2 Stories | Weekend guide + countdowns |
| Fri | 1 Reel · 2 Stories | Beaches, islands, nature, family |
| Sat | 1 Carousel · 2 Stories | Sports & achievements / week recap |

Rotation rules (enforced in code):
- No topic repeats within **7 days** (`data/used_topics.json`).
- Max **2 posts/day** from the same category.
- At least **1 interactive** Story daily (poll / quiz / slider).
- Every dated event post includes **date · venue · how to get tickets** — no vague "soon".

---

## 6. Voice in one table

| Do | Don't |
|---|---|
| Warm white-Gulf Arabic: *"يا هلا"، "تراها"، "لا يفوتكم"، "حيّاكم"* | Heavy local slang only one city understands |
| Short lines, one idea per line | Paragraph walls |
| Numbers as digits: 6–7 نوفمبر، 1.6 مليار دولار | Spelled-out numbers |
| Address the GCC visitor: "جايين من الرياض؟ الجسر ساعة!" | Assume everyone lives in Bahrain |
| End with a clear CTA: احفظ · شارك ربعك · تابع للمزيد | Generic "like & follow" |

Full style guide lives in `agency/prompts/brand_bible.md` (this is also the cached system prompt the pipeline sends to Claude).

---

## 6b. Slide styles by post type

| Post type | Style | Covers |
|---|---|---|
| info | لؤلؤ Pearl | Facts, heritage, did-you-know, tips |
| local | سدو Sadu | Bahrain news, events, places to go |
| international | شبكة Swiss | Bahrain on the international stage + GCC news |

---

## 7. Quality gates (checklist the Gatekeeper enforces)

1. ☐ Every fact has a source URL in `sources` (no source → cut the fact).
2. ☐ Event source dated ≤ 30 days, or an official ticketing page.
3. ☐ No red-list keyword in AR/EN (regex pass on final captions).
4. ☐ No person named unless they're the *subject of a positive achievement* and not a political figure.
5. ☐ Prices/dates written exactly as the source says.
6. ☐ Hashtags: 5–8 per IG post, 3–5 per TikTok.
7. ☐ Arabic proofread: hamza, taa marbuta, no mixed-direction glitches.

---

## 8. Folder map

```
Media Agency Agents/
├── README.md                    ← start here
├── 01_Operating_Manual.md       ← this file
├── 03_Automation_Guide.md       ← setup, costs, scheduling
├── content/YYYY-MM-DD/          ← daily batch.md + batch.json + postiz/ payloads + sources
├── assets/YYYY-MM-DD/           ← drop generated images/videos here (named by post id)
├── data/                        ← used_topics.json, evergreen.json, inbox.md, logs
└── agency/                      ← the Python pipeline + agent prompts
```
