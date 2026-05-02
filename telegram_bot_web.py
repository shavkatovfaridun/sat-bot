"""
SAT SAMARKAND — TELEGRAM BOT (Web Service for Render free tier)
================================================================
Uses Google Gemini API (free tier).

To run on Render:
  1. Set Start Command: python telegram_bot_web.py
  2. Required env vars:
       TELEGRAM_BOT_TOKEN
       GEMINI_API_KEY
       FARIDUN_CHAT_ID
       GOOGLE_SHEET_ID
       GOOGLE_CREDS_JSON
  3. Optional env vars:
       GEMINI_MODEL (defaults to "gemini-2.0-flash")
       PORT (defaults to 10000)

Get a Gemini API key (free): https://aistudio.google.com → Get API key
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
import google.generativeai as genai
import gspread
from google.oauth2.service_account import Credentials

# ----------------------------------------------------------------------------
# CONFIG
# ----------------------------------------------------------------------------
TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
GEMINI_API_KEY     = os.environ["GEMINI_API_KEY"]
FARIDUN_CHAT_ID    = int(os.environ["FARIDUN_CHAT_ID"])
GOOGLE_SHEET_ID    = os.environ["GOOGLE_SHEET_ID"]
GOOGLE_CREDS_JSON  = os.environ["GOOGLE_CREDS_JSON"]
PORT               = int(os.environ.get("PORT", 10000))

# Model: gemini-2.0-flash is fast, free, multilingual, decent at instructions.
# Alternatives: gemini-1.5-flash, gemini-2.5-flash. Override via env var.
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.0-flash")

# ----------------------------------------------------------------------------
# SETUP
# ----------------------------------------------------------------------------
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
log = logging.getLogger("sat-bot")

# Configure Gemini SDK
genai.configure(api_key=GEMINI_API_KEY)

# Load system prompt + knowledge base from same files we used with Claude
BASE = Path(__file__).parent
SYSTEM_PROMPT = (BASE / "system_prompt.md").read_text(encoding="utf-8")
KNOWLEDGE_BASE = (BASE / "knowledge_base.md").read_text(encoding="utf-8")
FULL_SYSTEM = f"{SYSTEM_PROMPT}\n\n---\n\n# KNOWLEDGE BASE\n\n{KNOWLEDGE_BASE}"

# Build Gemini model with system instruction baked in
gemini_model = genai.GenerativeModel(
    model_name=GEMINI_MODEL,
    system_instruction=FULL_SYSTEM,
    generation_config={
        "temperature": 0.7,
        "max_output_tokens": 1024,
    },
)

# Google Sheets
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
creds = Credentials.from_service_account_info(json.loads(GOOGLE_CREDS_JSON), scopes=SCOPES)
gc = gspread.authorize(creds)
sheet = gc.open_by_key(GOOGLE_SHEET_ID).sheet1

# Per-user conversation history (resets on Render restart — no Redis yet).
# Format: dict[user_id, list[{role: 'user'|'model', parts: [text]}]]
conversations: dict[int, list[dict]] = {}

# ----------------------------------------------------------------------------
# FLASK APP (so Render Web Service stays alive + UptimeRobot can ping)
# ----------------------------------------------------------------------------
app = Flask(__name__)


@app.route("/")
def health():
    return f"SAT Samarkand bot running 🟢  ({GEMINI_MODEL})", 200


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
        await context.bot.send_message(
            chat_id=FARIDUN_CHAT_ID,
            text=f"🔥 HOT LEAD 🔥\n\n{lead_info}",
        )
    except Exception as e:
        log.error(f"Faridun notify failed: {e}")


def ask_ai(user_id: int, user_message: str) -> tuple[str, bool]:
    """
    Send conversation to Gemini. Returns (reply_text, is_hot_lead).

    Gemini uses 'user' and 'model' roles (Anthropic used 'user' and 'assistant').
    """
    history = conversations.setdefault(user_id, [])

    # Trim to last 20 turns to control token usage
    trimmed = history[-20:]

    # Start a chat session with prior history
    chat = gemini_model.start_chat(history=trimmed)

    # Send new message and get response
    response = chat.send_message(user_message)
    reply = (response.text or "").strip()

    if not reply:
        # Gemini occasionally returns empty under safety filters; signal a fallback
        raise ValueError("Empty reply from Gemini")

    # Append both turns to memory
    history.append({"role": "user", "parts": [user_message]})
    history.append({"role": "model", "parts": [reply]})

    # Detect hot lead escalation tag
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
        "Men Xusnida, SAT Samarkand'ning yordamchisiman. "
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
        reply, is_hot = ask_ai(user.id, text)
    except Exception as e:
        log.error(f"AI error: {e}")
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
    log.info(f"SAT Samarkand bot polling... ({GEMINI_MODEL})")
    bot_app.run_polling(allowed_updates=Update.ALL_TYPES, stop_signals=None)


# Start the Telegram bot in a background thread when Flask app starts
threading.Thread(target=run_telegram_bot, daemon=True).start()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT)
