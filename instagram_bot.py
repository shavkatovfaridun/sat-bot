"""
SAT SAMARKAND — INSTAGRAM DM BOT (Web Service for Render free tier)
====================================================================
Receives Instagram DMs via Meta Graph API webhook, replies as Sora using
Claude, logs everything to the same Google Sheet as the Telegram bot, and
pings Faridun on Telegram for hot leads.

To run on Render (as a SECOND Web Service alongside telegram_bot_web.py):
  1. Set Start Command: python instagram_bot.py
  2. Required env vars (some shared with Telegram bot):
       ANTHROPIC_API_KEY
       FARIDUN_CHAT_ID
       GOOGLE_SHEET_ID
       GOOGLE_CREDS_JSON
       TELEGRAM_BOT_TOKEN          (used to forward hot leads to your TG)
       META_VERIFY_TOKEN           (the string YOU made up in Step A9)
       META_PAGE_ACCESS_TOKEN      (from Step A7)
       META_APP_SECRET             (from Step A8)
  3. Optional:
       PORT (defaults to 10000)

After deploying, copy the Render URL and configure the webhook in Meta App
Dashboard → Instagram product → Webhooks → callback URL = <RENDER_URL>/webhook
"""

import os
import json
import logging
import hmac
import hashlib
from datetime import datetime
from pathlib import Path

import requests
from flask import Flask, request, abort
from anthropic import Anthropic
import gspread
from google.oauth2.service_account import Credentials

# ----------------------------------------------------------------------------
# CONFIG
# ----------------------------------------------------------------------------
ANTHROPIC_API_KEY     = os.environ["ANTHROPIC_API_KEY"]
FARIDUN_CHAT_ID       = int(os.environ["FARIDUN_CHAT_ID"])
GOOGLE_SHEET_ID       = os.environ["GOOGLE_SHEET_ID"]
GOOGLE_CREDS_JSON     = os.environ["GOOGLE_CREDS_JSON"]
TELEGRAM_BOT_TOKEN    = os.environ["TELEGRAM_BOT_TOKEN"]

META_VERIFY_TOKEN     = os.environ["META_VERIFY_TOKEN"]
META_PAGE_ACCESS_TOKEN = os.environ["META_PAGE_ACCESS_TOKEN"]
META_APP_SECRET       = os.environ["META_APP_SECRET"]

PORT = int(os.environ.get("PORT", 10000))

# ----------------------------------------------------------------------------
# SETUP
# ----------------------------------------------------------------------------
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
log = logging.getLogger("ig-bot")

app = Flask(__name__)
anthropic = Anthropic(api_key=ANTHROPIC_API_KEY)

BASE = Path(__file__).parent
SYSTEM_PROMPT = (BASE / "system_prompt.md").read_text(encoding="utf-8")
KNOWLEDGE_BASE = (BASE / "knowledge_base.md").read_text(encoding="utf-8")
FULL_SYSTEM = f"{SYSTEM_PROMPT}\n\n---\n\n# KNOWLEDGE BASE\n\n{KNOWLEDGE_BASE}"

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
try:
    creds = Credentials.from_service_account_info(json.loads(GOOGLE_CREDS_JSON), scopes=SCOPES)
    sheet = gspread.authorize(creds).open_by_key(GOOGLE_SHEET_ID).sheet1
except Exception as e:
    log.error(f"Google Sheets init failed: {e}")
    sheet = None

# Per-IG-user conversation history (resets on Render restart)
conversations: dict[str, list[dict]] = {}

# ----------------------------------------------------------------------------
# HELPERS
# ----------------------------------------------------------------------------
def verify_signature(payload: bytes, signature_header: str) -> bool:
    """Verify that the webhook payload really came from Meta."""
    if not signature_header:
        return False
    expected = "sha256=" + hmac.new(
        META_APP_SECRET.encode(), payload, digestmod=hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature_header)


def send_instagram_message(recipient_id: str, text: str) -> None:
    """Send a DM via Instagram Graph API."""
    url = f"https://graph.facebook.com/v22.0/me/messages?access_token={META_PAGE_ACCESS_TOKEN}"
    payload = {
        "recipient": {"id": recipient_id},
        "message": {"text": text},
        "messaging_type": "RESPONSE",
    }
    try:
        r = requests.post(url, json=payload, timeout=15)
        if not r.ok:
            log.error(f"IG send failed: {r.status_code} {r.text}")
    except Exception as e:
        log.error(f"IG send exception: {e}")


def notify_faridun_via_telegram(message: str) -> None:
    """Use Telegram Bot API to ping Faridun about a hot IG lead."""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    try:
        requests.post(url, json={"chat_id": FARIDUN_CHAT_ID, "text": message}, timeout=10)
    except Exception as e:
        log.error(f"Faridun notify failed: {e}")


def log_to_sheet(row: list) -> None:
    if sheet is None:
        return
    try:
        sheet.append_row(row, value_input_option="USER_ENTERED")
    except Exception as e:
        log.error(f"Sheets log failed: {e}")


def ask_claude(user_id: str, user_message: str) -> tuple[str, bool]:
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
# ROUTES
# ----------------------------------------------------------------------------
@app.route("/")
def health():
    return "SAT Samarkand IG bot running 🟢", 200


@app.route("/ping")
def ping():
    return "pong", 200


@app.route("/webhook", methods=["GET"])
def verify_webhook():
    """One-time handshake when you set up the webhook in Meta's dashboard."""
    if (
        request.args.get("hub.mode") == "subscribe"
        and request.args.get("hub.verify_token") == META_VERIFY_TOKEN
    ):
        log.info("Webhook verified ✅")
        return request.args.get("hub.challenge"), 200
    log.warning("Webhook verification failed")
    return "Verification failed", 403


@app.route("/webhook", methods=["POST"])
def webhook():
    """Receives every Instagram DM event."""
    signature = request.headers.get("X-Hub-Signature-256", "")
    if not verify_signature(request.data, signature):
        log.warning("Invalid signature on incoming webhook")
        abort(403)

    data = request.json or {}
    for entry in data.get("entry", []):
        for msg_event in entry.get("messaging", []):
            # Skip echoes (messages WE sent)
            if msg_event.get("message", {}).get("is_echo"):
                continue

            sender_id = msg_event["sender"]["id"]
            text = msg_event.get("message", {}).get("text")
            if not text:
                continue  # ignore stickers, photos, etc. for now

            log.info(f"IG message from {sender_id}: {text[:80]}")

            try:
                reply, is_hot = ask_claude(sender_id, text)
            except Exception as e:
                log.error(f"Claude error: {e}")
                reply = (
                    "Kechirasiz, bir oz kuting, tez orada javob beraman 🙏\n"
                    "Yoki Telegram orqali yozing: @sat_samarkand"
                )
                is_hot = False

            send_instagram_message(sender_id, reply)

            log_to_sheet([
                datetime.now().isoformat(timespec="seconds"),
                "instagram",
                sender_id,
                "",   # IG webhooks don't include the user's display name by default
                "",   # username also requires extra Graph API call
                text,
                reply,
                "HOT" if is_hot else "ACTIVE",
            ])

            if is_hot:
                notify_faridun_via_telegram(
                    f"🔥 HOT LEAD (Instagram) 🔥\n\n"
                    f"IG User ID: {sender_id}\n"
                    f"Last message: {text}\n\n"
                    f"Bot reply: {reply}\n\n"
                    f"To message back: open Instagram DMs"
                )

    return "OK", 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT)
