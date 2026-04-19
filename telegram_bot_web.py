"""
SAT SAMARKAND — TELEGRAM BOT (Web Service version for Render free tier)
========================================================================
Same as telegram_bot.py, but wraps the polling bot inside a Flask app
so it can be deployed as a Render Web Service (which has a free tier).

A keep-alive ping endpoint prevents the free tier from sleeping.
"""

import os
import json
import logging
import threading
from datetime import datetime
from pathlib import Path

from flask import Flask
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters
from anthropic import Anthropic
import gspread
from google.oauth2.service_account import Credentials

# ----------------------------------------------------------------------------
# CONFIG
# ----------------------------------------------------------------------------
TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
ANTHROPIC_API_KEY  = os.environ["ANTHROPIC_API_KEY"]
FARIDUN_CHAT_ID    = int(os.environ["FARIDUN_CHAT_ID"])
GOOGLE_SHEET_ID    = os.environ["GOOGLE_SHEET_ID"]
GOOGLE_CREDS_JSON  = os.environ["GOOGLE_CREDS_JSON"]
PORT               = int(os.environ.get("PORT", 10000))

# ----------------------------------------------------------------------------
# SETUP
# ----------------------------------------------------------------------------
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
log = logging.getLogger("sat-bot")

anthropic = Anthropic(api_key=ANTHROPIC_API_KEY)

BASE = Path(__file__).parent
SYSTEM_PROMPT = (BASE / "system_prompt.md").read_text(encoding="utf-8")
KNOWLEDGE_BASE = (BASE / "knowledge_base.md").read_text(encoding="utf-8")
FULL_SYSTEM = f"{SYSTEM_PROMPT}\n\n---\n\n# KNOWLEDGE BASE\n\n{KNOWLEDGE_BASE}"

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
creds = Credentials.from_service_account_info(json.loads(GOOGLE_CREDS_JSON), scopes=SCOPES)
gc = gspread.authorize(creds)
sheet = gc.open_by_key(GOOGLE_SHEET_ID).sheet1

conversations: dict[int, list[dict]] = {}

# ----------------------------------------------------------------------------
# FLASK APP (so Render Web Service stays alive)
# ----------------------------------------------------------------------------
app = Flask(__name__)

@app.route("/")
def health():
    return "SAT Samarkand bot is running 🟢", 200

@app.route("/ping")
def ping():
    return "pong", 200

# ----------------------------------------------------------------------------
# BOT HELPERS
# ----------------------------------------------------------------------------
def log_to_sheet(row: list) -> None:
    try:
        sheet.append_row(row, value_input_option="USER_ENTERED")
    except Exception as e:
        log.error(f"Sheets log failed: {e}")


async def notify_faridun(context: ContextTypes.DEFAULT_TYPE, lead_info: str) -> None:
    try:
        await context.bot.send_message(chat_id=FARIDUN_CHAT_ID, text=f"🔥 HOT LEAD 🔥\n\n{lead_info}")
    except Exception as e:
        log.error(f"Faridun notify failed: {e}")


def ask_claude(user_id: int, user_message: str) -> tuple[str, bool]:
    history = conversations.setdefault(user_id, [])
    history.append({"role": "user", "content": user_message})
    trimmed = history[-20:]

    response = anthropic.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1024,
        system=FULL_SYSTEM,
        messages=trimmed,
    )
    reply = response.content[0].text
    history.append({"role": "assistant", "content": reply})

    is_hot = "[ESCALATE_HOT_LEAD]" in reply
    reply = reply.replace("[ESCALATE_HOT_LEAD]", "").strip()
    return reply, is_hot


# ----------------------------------------------------------------------------
# TELEGRAM HANDLERS
# ----------------------------------------------------------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    conversations[user.id] = []
    welcome = (
        "Assalomu alaykum! 👋\n"
        "Здравствуйте! / Hello!\n\n"
        "Men Nigora, SAT Samarkand'ning yordamchisiman. "
        "SAT kurslarimiz, narxlar, jadval yoki boshqa har qanday savol bo'yicha yordam bera olaman. "
        "O'zingizga qulay tilda yozing — o'zbek, rus yoki ingliz! 😊"
    )
    await update.message.reply_text(welcome)
    log_to_sheet([
        datetime.now().isoformat(timespec="seconds"),
        "telegram", str(user.id),
        f"{user.first_name} {user.last_name or ''}".strip(),
        user.username or "", "[/start]", welcome, "NEW",
    ])


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    text = update.message.text
    log.info(f"Message from {user.id} ({user.username}): {text[:80]}")

    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

    try:
        reply, is_hot = ask_claude(user.id, text)
    except Exception as e:
        log.error(f"Claude error: {e}")
        reply = (
            "Kechirasiz, texnik muammo bor. Iltimos, bir oz kutib qayta yozing 🙏\n"
            "Yoki to'g'ridan-to'g'ri @sat_samarkand kanaliga murojaat qiling."
        )
        is_hot = False

    await update.message.reply_text(reply)

    log_to_sheet([
        datetime.now().isoformat(timespec="seconds"),
        "telegram", str(user.id),
        f"{user.first_name} {user.last_name or ''}".strip(),
        user.username or "", text, reply, "HOT" if is_hot else "ACTIVE",
    ])

    if is_hot:
        lead_info = (
            f"Channel: Telegram\n"
            f"Name: {user.first_name} {user.last_name or ''}\n"
            f"Username: @{user.username or 'n/a'}\n"
            f"User ID: {user.id}\n"
            f"Last message: {text}\n\n"
            f"Bot reply: {reply}\n\n"
            f"Open chat: tg://user?id={user.id}"
        )
        await notify_faridun(context, lead_info)


async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    conversations[update.effective_user.id] = []
    await update.message.reply_text("Suhbat tarixi tozalandi. Qaytadan boshlaymiz ✅")


# ----------------------------------------------------------------------------
# RUN BOT IN A BACKGROUND THREAD + FLASK ON MAIN
# ----------------------------------------------------------------------------
def run_telegram_bot():
    bot_app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    bot_app.add_handler(CommandHandler("start", start))
    bot_app.add_handler(CommandHandler("reset", reset))
    bot_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    log.info("SAT Samarkand bot polling...")
    bot_app.run_polling(allowed_updates=Update.ALL_TYPES, stop_signals=None)


# Start the Telegram bot in a background thread when Flask app starts
threading.Thread(target=run_telegram_bot, daemon=True).start()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT)
