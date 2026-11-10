# وين اليوم · @waynalyoum — AI Media Agency

Positive Bahrain content for the whole GCC · Instagram + TikTok · 3–5 posts/day · ≈ $0.10/day in API costs

| Open this | For |
|---|---|
| `01_Operating_Manual.md` | How the 6 agents work together, red lines, daily rhythm, content mix |
| `content/2026-10-29/batch.md` | **Day 1 batch** — 1 Reel, 2 Carousels, 2 Stories, ready to produce |
| `assets/2026-10-29/` | Day 1 carousel slides + story frames, already rendered with Arabic text |
| **`04_GitHub_Instagram_Setup.md`** | **Full-auto setup: GitHub cloud + free Instagram API (start here)** |
| `03_Automation_Guide.md` | Setup steps, token-saving design, costs, daily 5-min routine |
| `agency/prompts/brand_bible.md` | Voice, hashtags, visual identity (also the AI's system prompt) |
| `data/inbox.md` | Drop tomorrow's ideas + links here |

## Quick start
1. Double-click `agency/setup_windows.bat`
2. Paste your API key in `agency/.env`
3. `postiz auth:login` → `python publish.py --check` → paste IDs into `agency/config.json`
4. `python run_daily.py --dry-run` → then `python run_daily.py --today`

## Pipeline
```
CEO (rules) → Scout (RSS) → Gatekeeper (regex + Haiku) → Creative/Visual (Sonnet) → Gatekeeper pass 2 (regex) → Ops (slides + Postiz drafts)
```
