# وين اليوم — Full-Auto Setup (GitHub + Instagram, free)

Once this is done, everything runs in the cloud. Your PC can stay off.

```
06:00  GitHub builds the day: research → safety → 8 posts → slides, stories, reel
06:05  "Batch YYYY-MM-DD" issue lands on your phone (GitHub app) with previews
10:00 → 22:30  each post publishes to Instagram on time (checked every 30 min)
You:   nothing. Optional: comment "skip D14-03" or "stop" on the issue · post the reel to TikTok by hand
```

| What | Cost |
|---|---|
| GitHub Actions (public repo) | Free |
| Instagram Graph API | Free |
| Media hosting (jsDelivr) | Free |
| Claude API | about $0.25/day |

---

## Part A — Instagram (about 20 min, one time)

**A1. Make @waynalyoum a Professional account and link a Facebook Page**
- Instagram app → Settings → *Account type and tools* → **Switch to professional** (Creator or Business).
- Create a Facebook Page called وين اليوم if you don't have one (facebook.com/pages/create).
- Instagram → Edit profile → **Page** → connect that Page.

**A2. Create a Meta app**
1. Go to **developers.facebook.com** → My Apps → **Create App**.
2. Use case: **Other** → type **Business** → name it `waynalyoum-publisher`.
3. In the app dashboard: **Add product → Instagram → "API setup with Facebook login"**.
4. Keep the app in **Development mode**. That's fine because you're the admin and it's your own account, so no App Review is needed.
5. Settings → Basic: copy the **App ID** and **App Secret**.

**A3. Get a short token**
1. Go to **developers.facebook.com/tools/explorer**.
2. Pick your app at the top right → **Get User Access Token**.
3. Tick these permissions: `instagram_basic`, `instagram_content_publish`, `pages_show_list`, `pages_read_engagement`, `business_management`.
4. Generate, approve the pop-up (choose your Page and @waynalyoum), then copy the token.

**A4. Turn it into a never-expiring token (helper script)**
In your activated terminal (`start_here.bat`):
```
python get_ig_token.py
```
Paste the App ID, App Secret and the short token. It prints:
```
Instagram account: waynalyoum
Token expires: NEVER ✅
IG_USER_ID      = 1784…
IG_ACCESS_TOKEN = EAAG…
```
Keep this window open for Part B. Don't paste these values into chat.

---

## Part B — GitHub (about 10 min, one time)

**B1. Create the repo:** github.com/new → name **`waynalyoum`** → **Public** → no README → Create.
> It has to be public so Instagram can fetch the images for free. Your code and upcoming posts will be visible to anyone. No keys are ever stored in the repo.

**B2. Tell Claude "repo is ready"** and the agency code gets pushed there.

**B3. Add the secrets:** repo → **Settings → Secrets and variables → Actions → New repository secret**

| Name | Value |
|---|---|
| `ANTHROPIC_API_KEY` | Your Claude key (`sk-ant-…`) |
| `ANTHROPIC_WORKSPACE_ID` | Only if your key needs it (`wrkspc_…`) |
| `IG_USER_ID` | From A4 |
| `IG_ACCESS_TOKEN` | From A4 |

**B4. Phone notifications:** GitHub app → open the repo → **Watch → All activity**.

**B5. Test it:** repo → **Actions → Daily batch → Run workflow**. After about 5 min you should get a new issue with the day's previews.

**B6. Stop the PC version** so it doesn't run twice. In a terminal:
```
schtasks /Delete /TN "WaynAlyoum Daily Batch" /F
```

---

## Daily controls

| Want to… | Do this |
|---|---|
| Cancel one post | Comment `skip D14-03` on today's issue (several IDs is fine) |
| Cancel the rest of today | Comment `stop` |
| Add your voice to the reel | Repo → `voice/` folder → **Add file → Upload files** → name it after the reel's ID, e.g. `D14-06.m4a` (phone voice memos are fine). The reel rebuilds in about 3 min. Do it before 20:30. |
| Background music for reels | Upload royalty-free `.mp3` files to `assets/music/`. One is picked each day. |
| Post to TikTok | Today's issue has a reel download link + TikTok caption. Upload them from your phone. |
| Push tomorrow's topic | Edit `data/inbox.md` on GitHub (one line + link) |
| Change times, styles, rules | `agency/config.json` · `agency/prompts/*.md` |

**Safety nets built in:** posts more than 3h late are skipped (never posted at the wrong time) · each post is tried at most 3 times · a story that fails halfway resumes without repeating frames · only you can veto (comments from others are ignored).

**Limits to know:** GitHub's scheduler can run 5–30 min late at busy times · Instagram allows about 50 API posts a day (we use about 12) · stories go out without poll/quiz stickers (Instagram's API can't add them, so add one from your phone if you want).
