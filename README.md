# SAT Samarkand AI Lead Bot 🎓🤖

Automated lead engagement across Telegram, Instagram, and WhatsApp.
Answers questions in Uzbek/Russian/English, qualifies leads, books placement tests,
and alerts Faridun instantly when a lead is ready to enroll.

## Quick Start

1. **EDIT `knowledge_base.md` FIRST** — fix pricing, schedule, course length, and any `[PLACEHOLDER]` values
2. Follow `DEPLOYMENT_GUIDE.md` step by step
3. Telegram bot goes live in ~1 hour
4. Instagram bot in ~2–3 hours (Meta approvals)
5. WhatsApp: start with semi-auto link, upgrade later

## Architecture

```
Lead sends message
      ↓
[Telegram / Instagram / WhatsApp webhook]
      ↓
Bot sends conversation + knowledge_base.md to Claude API
      ↓
Claude responds in lead's language
      ↓
Bot sends reply + logs to Google Sheet
      ↓
If hot lead → Telegram alert to Faridun
```

## Files

- `knowledge_base.md` — **edit this often**, it's the bot's brain
- `system_prompt.md` — bot personality and rules (rarely edit)
- `telegram_bot.py` — Telegram channel
- `instagram_bot.py` — Instagram DMs
- `whatsapp_bot.py` — WhatsApp (advanced path)
- `DEPLOYMENT_GUIDE.md` — full setup walkthrough
- `requirements.txt` — Python dependencies

## Monthly Cost: ~$5–15

Most of this is Anthropic API usage. Render, Google Sheets, Meta platforms are free.

## Update Flow

1. Edit `knowledge_base.md` locally or in GitHub
2. Commit + push
3. Render auto-redeploys within 2 minutes
4. Bot now uses updated knowledge

## Support

Built for Faridun Shavkatov / SAT Samarkand / Green Ivy Academy.
