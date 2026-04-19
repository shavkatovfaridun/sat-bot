"""
SAT SAMARKAND — INSTAGRAM DM BOT (Flask webhook)
=================================================
Receives Instagram DMs via Meta Graph API webhook, replies using Claude AI.

SETUP REQUIRED (one-time):
1. Convert your Instagram to a Business/Creator account
2. Connect it to a Facebook Page you own
3. Create a Meta Developer app: https://developers.facebook.com
4. Add "Instagram Graph API" + "Messenger" products
5. Subscribe to 'messages' webhook event
6. Get long-lived Page Access Token
7. Set environment variables and deploy this file
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
VERIFY_TOKEN       = os.environ["META_VERIFY_TOKEN"]       # any string you choose, used in webhook setup
PAGE_ACCESS_TOKEN  = os.environ["META_PAGE_ACCESS_TOKEN"]  # from Meta app dashboard
APP_SECRET         = os.environ["META_APP_SECRET"]         # for verifying webhook signatures
ANTHROPIC_API_KEY  = os.environ["ANTHROPIC_API_KEY"]
FARIDUN_TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]  # to notify Faridun
FARIDUN_CHAT_ID    = int(os.environ["FARIDUN_CHAT_ID"])
GOOGLE_SHEET_ID    = os.environ["GOOGLE_SHEET_ID"]
GOOGLE_CREDS_JSON  = os.environ["GOOGLE_CREDS_JSON"]

# ----------------------------------------------------------------------------
# SETUP
# ----------------------------------------------------------------------------
logging.basicConfig(level=logging.INFO)
log = logging.getLogger("ig-bot")

app = Flask(__name__)
anthropic = Anthropic(api_key=ANTHROPIC_API_KEY)

BASE = Path(__file__).parent
SYSTEM_PROMPT = (BASE / "system_prompt.md").read_text(encoding="utf-8")
KNOWLEDGE_BASE = (BASE / "knowledge_base.md").read_text(encoding="utf-8")
FULL_SYSTEM = f"{SYSTEM_PROMPT}\n\n---\n\n# KNOWLEDGE BASE\n\n{KNOWLEDGE_BASE}"

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
creds = Credentials.from_service_account_info(json.loads(GOOGLE_CREDS_JSON), scopes=SCOPES)
sheet = gspread.authorize(creds).open_by_key(GOOGLE_SHEET_ID).sheet1

conversations: dict[str, list[dict]] = {}  # keyed by Instagram user ID

# ----------------------------------------------------------------------------
# HELPERS
# ----------------------------------------------------------------------------
def verify_signature(payload: bytes, signature_header: str) -> bool:
    if not signature_header:
        return False
    expected = "sha256=" + hmac.new(
        APP_SECRET.encode(), payload, hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature_header)


def send_instagram_message(recipient_id: str, text: str) -> None:
    url = f"https://graph.facebook.com/v21.0/me/messages?access_token={PAGE_ACCESS_TOKEN}"
    payload = {
        "recipient": {"id": recipient_id},
        "message": {"text": text},
        "messaging_type": "RESPONSE",
    }
    r = requests.post(url, json=payload, timeout=15)
    if not r.ok:
        log.error(f"IG send failed: {r.status_code} {r.text}")


def notify_faridun(message: str) -> None:
    url = f"https://api.telegram.org/bot{FARIDUN_TELEGRAM_BOT_TOKEN}/sendMessage"
    try:
        requests.post(url, json={"chat_id": FARIDUN_CHAT_ID, "text": message}, timeout=10)
    except Exception as e:
        log.error(f"Faridun notify failed: {e}")


def log_to_sheet(row: list) -> None:
    try:
        sheet.append_row(row, value_input_option="USER_ENTERED")
    except Exception as e:
        log.error(f"Sheets error: {e}")


def ask_claude(user_id: str, msg: str) -> tuple[str, bool]:
    history = conversations.setdefault(user_id, [])
    history.append({"role": "user", "content": msg})
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
    return reply.replace("[ESCALATE_HOT_LEAD]", "").strip(), is_hot


# ----------------------------------------------------------------------------
# ROUTES
# ----------------------------------------------------------------------------
@app.route("/webhook", methods=["GET"])
def verify():
    """Webhook verification handshake with Meta."""
    if (
        request.args.get("hub.mode") == "subscribe"
        and request.args.get("hub.verify_token") == VERIFY_TOKEN
    ):
        return request.args.get("hub.challenge"), 200
    return "Verification failed", 403


@app.route("/webhook", methods=["POST"])
def webhook():
    """Receives Instagram DM events."""
    signature = request.headers.get("X-Hub-Signature-256", "")
    if not verify_signature(request.data, signature):
        log.warning("Invalid signature")
        abort(403)

    data = request.json
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
                reply = "Kechirasiz, bir oz kuting, tez orada javob beraman 🙏"
                is_hot = False

            send_instagram_message(sender_id, reply)

            log_to_sheet([
                datetime.now().isoformat(timespec="seconds"),
                "instagram",
                sender_id,
                "",  # IG doesn't give name in DM webhook without extra API call
                "",
                text,
                reply,
                "HOT" if is_hot else "ACTIVE",
            ])

            if is_hot:
                notify_faridun(
                    f"🔥 HOT LEAD (Instagram) 🔥\n\n"
                    f"IG User ID: {sender_id}\n"
                    f"Last message: {text}\n\n"
                    f"Bot reply: {reply}"
                )

    return "OK", 200


@app.route("/", methods=["GET"])
def health():
    return "SAT Samarkand IG bot is running 🟢", 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
