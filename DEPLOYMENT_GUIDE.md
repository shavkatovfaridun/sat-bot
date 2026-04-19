# 🚀 SAT SAMARKAND BOT — DEPLOYMENT GUIDE

Complete setup from zero to live bot on all 3 channels. Total time: ~2–4 hours first time.

---

## 📦 WHAT'S IN THIS PROJECT

| File | Purpose |
|------|---------|
| `knowledge_base.md` | Bot's brain — facts about your center (EDIT THIS FIRST) |
| `system_prompt.md` | Bot's personality and rules |
| `telegram_bot.py` | Telegram channel bot |
| `instagram_bot.py` | Instagram DM bot |
| `whatsapp_bot.py` | WhatsApp Business bot |
| `requirements.txt` | Python dependencies |

---

## STEP 1 — GET YOUR API KEYS (30 min)

### 1A. Anthropic API Key (for Claude AI)
1. Go to https://console.anthropic.com
2. Sign up / log in
3. Go to **API Keys** → **Create Key**
4. Copy it — save as `ANTHROPIC_API_KEY`
5. Add $20 credit to start (it'll last months at your volume)

### 1B. Telegram Bot Token
1. Open Telegram, message **@BotFather**
2. Send `/newbot`
3. Name: `SAT Samarkand Assistant`
4. Username: `sat_samarkand_bot` (or similar — must end in `bot`)
5. Copy the token — save as `TELEGRAM_BOT_TOKEN`

### 1C. Your Telegram Chat ID (for hot-lead alerts)
1. Message **@userinfobot** on Telegram
2. It will reply with your chat ID (a number like `123456789`)
3. Save as `FARIDUN_CHAT_ID`

### 1D. Google Sheet for lead logging
1. Go to https://sheets.google.com → **New** → rename to `SAT Samarkand Leads`
2. In row 1, add headers:
   ```
   Timestamp | Channel | User ID | Name | Username | Their Message | Bot Reply | Status
   ```
3. Copy the Sheet ID from URL: `docs.google.com/spreadsheets/d/`**`THIS_PART_IS_THE_ID`**`/edit`
4. Save as `GOOGLE_SHEET_ID`

### 1E. Google Service Account (so bot can write to the sheet)
1. Go to https://console.cloud.google.com
2. Create new project: `sat-samarkand-bot`
3. Enable APIs: **Google Sheets API**
4. Go to **IAM & Admin** → **Service Accounts** → **Create**
5. Name: `sheet-writer`, click through
6. Open the service account → **Keys** tab → **Add Key** → **JSON** → download
7. Open the JSON file — copy its entire contents. This is your `GOOGLE_CREDS_JSON`
8. Inside the JSON, find `"client_email"` — copy that email
9. Go back to your Google Sheet → click **Share** → paste that email → give **Editor** access

---

## STEP 2 — DEPLOY TELEGRAM BOT FIRST (60 min)

Start with Telegram because it's live in 1 hour and has no approval process.

### Option A: Render.com (recommended, free tier)

1. Push this project to GitHub (public or private):
   ```bash
   cd /path/to/sat-bot
   git init && git add . && git commit -m "initial"
   # Create repo on github.com, then:
   git remote add origin https://github.com/YOUR_USERNAME/sat-bot.git
   git push -u origin main
   ```

2. Go to https://render.com → Sign up with GitHub
3. **New** → **Background Worker** (NOT Web Service — Telegram bot uses polling)
4. Connect your repo
5. Settings:
   - **Runtime:** Python 3
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `python telegram_bot.py`
6. **Environment Variables** tab — add these ALL:
   ```
   TELEGRAM_BOT_TOKEN       = (from step 1B)
   ANTHROPIC_API_KEY        = (from step 1A)
   FARIDUN_CHAT_ID          = (from step 1C)
   GOOGLE_SHEET_ID          = (from step 1D)
   GOOGLE_CREDS_JSON        = (paste the entire JSON from step 1E as one line)
   ```
7. **Create Background Worker** → wait for deploy (~3 min)
8. Check logs — you should see `SAT Samarkand bot is running...`

### Test it
1. Open Telegram → search for your bot username
2. Send `/start`
3. Ask: "Narxingiz qancha?" / "Where are you located?" / "AP Calculus haqida aytib bering"
4. Check your Google Sheet — rows should appear
5. Type "I want to enroll" — you should get a Telegram notification from your bot to YOU

✅ **Telegram bot live!**

---

## STEP 3 — DEPLOY INSTAGRAM BOT (2–3 hours, needs approvals)

### 3A. Convert Instagram to Business account
1. Open Instagram app → Settings → Account → **Switch to Professional Account**
2. Choose **Business**
3. You'll need a Facebook Page — create one if you don't have one (`SAT Samarkand`)
4. Connect the Facebook Page to your Instagram

### 3B. Create Meta Developer App
1. Go to https://developers.facebook.com
2. **My Apps** → **Create App** → **Business** → name it `SAT Samarkand Bot`
3. Add products:
   - **Instagram** (the newer "Instagram API with Instagram Login" option is fine)
   - **Webhooks**

### 3C. Get access token
1. In your app dashboard → **Instagram** → **API Setup with Instagram Business Login**
2. Generate access token for your Page
3. Use **Graph API Explorer** to convert it to a long-lived token (60 days)
   - Or use the Token Debugger → Extend Access Token
4. Save as `META_PAGE_ACCESS_TOKEN`

### 3D. Deploy Instagram bot on Render
1. Same as Telegram deploy, but:
   - **New** → **Web Service** (not Background Worker — IG uses webhooks)
   - **Start Command:** `gunicorn instagram_bot:app`
2. Environment variables — add all from Telegram PLUS:
   ```
   META_VERIFY_TOKEN        = (invent any string, e.g., "sat_samarkand_2026")
   META_PAGE_ACCESS_TOKEN   = (from step 3C)
   META_APP_SECRET          = (from Meta app dashboard → Basic → App Secret)
   ```
3. Deploy → Render will give you a URL like `https://sat-ig-bot.onrender.com`

### 3E. Register webhook with Meta
1. In Meta app → **Webhooks** → **Instagram**
2. Callback URL: `https://sat-ig-bot.onrender.com/webhook`
3. Verify token: the same `META_VERIFY_TOKEN` you invented above
4. Subscribe to: **messages**, **messaging_postbacks**

### Test it
1. Get a friend to DM your Instagram business account
2. Bot should reply within seconds
3. Google Sheet should log it

✅ **Instagram bot live!**

---

## STEP 4 — WHATSAPP (choose ONE path)

### Path A (Recommended for you): Semi-auto with link
**Start here. Upgrade later.**

1. Use your existing WhatsApp Business app on phone
2. Set a permanent auto-reply template:
   > "Salom! Tezroq javob olish uchun bizning Telegram botimizga yozing: t.me/sat_samarkand_bot — u SAT haqida hamma savollarga 24/7 javob beradi. Yoki bu yerda kuting, tez javob beramiz."
3. Add a WhatsApp click-to-chat link on your Instagram bio and landing page:
   `https://wa.me/998XXXXXXXXX?text=Salom,%20SAT%20haqida%20savollar%20bor`

**Why:** WhatsApp Business API approval in Uzbekistan can take 3-7 days and requires business docs. The link + auto-reply covers 80% of value for 0% hassle.

### Path B: Full WhatsApp Cloud API (when volume justifies)
Follow `whatsapp_bot.py` comments. Requires:
- Verified Meta Business Manager
- Dedicated phone number (not used for anything else)
- Business registration docs

OR use **Wati.io** as shortcut (~$40/mo, they handle Meta verification).

---

## STEP 5 — OPERATIONAL CHECKLIST

### Daily
- Check Google Sheet for new hot leads (bot will also Telegram you)
- Follow up on hot leads within 1-2 hours

### Weekly
- Review bot conversations in Google Sheet
- Note any questions bot didn't handle well → add answers to `knowledge_base.md`
- Redeploy after editing (Render auto-deploys from GitHub)

### Monthly
- Check Anthropic API usage at console.anthropic.com
- Top up $10-20 credit
- Review conversion rate: leads messaged → placement tests booked → paying students

---

## 💰 EXPECTED COSTS

| Service | Cost |
|---------|------|
| Render.com (2 services) | Free tier is enough to start |
| Anthropic API | ~$5–15/month at 100 leads/day |
| Google Sheets | Free |
| Meta (IG + WA) | Free |
| **TOTAL** | **~$5–15/month** |

---

## 🆘 TROUBLESHOOTING

**Bot doesn't reply on Telegram:**
- Check Render logs → look for errors
- Make sure `TELEGRAM_BOT_TOKEN` is correct
- Make sure bot is deployed as **Background Worker**, not Web Service

**Google Sheet isn't updating:**
- Did you share the sheet with the service account email?
- Is `GOOGLE_CREDS_JSON` the full JSON (not just part of it)?

**Bot gives weird answers:**
- Edit `knowledge_base.md` → push to GitHub → Render auto-redeploys
- Check that `knowledge_base.md` is in the same folder as the bot `.py` file

**Instagram webhook fails:**
- Meta needs HTTPS — Render gives you HTTPS automatically
- Double-check verify token matches in both Render env vars and Meta dashboard

---

## 🎯 NEXT STEPS (WEEK 2+)

1. **Add memory persistence** — move `conversations` dict to Redis (Upstash is free) so bot remembers leads across restarts
2. **Add Apps Script integration** — your score-predictor quiz data can flow into the same conversation, so bot knows their score when they come from the quiz
3. **Add WhatsApp Cloud API** once you have >50 WhatsApp leads/month
4. **Green Ivy Academy integration** — same codebase, different knowledge_base.md file, different Telegram bot token → instant second bot for Green Ivy leads
5. **A/B test messages** — track which opening greetings convert best
