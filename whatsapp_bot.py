"""
SAT SAMARKAND — WHATSAPP BOT (Meta WhatsApp Cloud API)
========================================================
Receives WhatsApp messages via Meta Cloud API webhook, replies using Claude AI.

SETUP REQUIRED (one-time — takes 1-2 days):
1. Register at https://business.facebook.com
2. Create WhatsApp Business Cloud API app: https://developers.facebook.com
3. Verify your business (Uzbekistan business registration required)
4. Add a phone number dedicated to WhatsApp Business (NOT your personal one!)
5. Get: Phone Number ID, Business Account ID, System User Access Token
6. Configure webhook pointing to this server's /whatsapp endpoint
7. Deploy this file

ALTERNATIVE (easier, faster): Use Wati.io or 360Dialog as a wrapper — same code,
they handle Meta verification for you. Costs ~$40/mo but live in 1 day.
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
VERIFY_TOKEN         = os.environ["META_VERIFY_TOKEN"]
WHATSAPP_ACCESS_TOKEN = os.environ["WHATSAPP_ACCESS_TOKEN"]
WHATSAPP_PHONE_ID    = os.environ["WHATSAPP_PHONE_ID"]
APP_SECRET           = os.environ["META_APP_SECRET"]
ANTHROPIC_API_KEY    = os.environ["ANTHROPIC_API_KEY"]
FARIDUN_TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
FARIDUN_CHAT_ID      = int(os.environ["FARIDUN_CHAT_ID"])
GOOGLE_SHEET_ID      = os.environ["GOOGLE_SHEET_ID"]
GOOGLE_CREDS_JSON    = os.environ["GOOGLE_CREDS_JSON"]

# ----------------------------------------------------------------------------
# SETUP
# ----------------------------------------------------------------------------
logging.basicConfig(level=logging.INFO)
log = logging.getLogger("wa-bot")

app = Flask(__name__)
anthropic = Anthropic(api_key=ANTHROPIC_API_KEY)

BASE = Path(__file__).parent
SYSTEM_PROMPT = (BASE / "system_prompt.md").read_text(encoding="utf-8")
KNOWLEDGE_BASE = (BASE / "knowledge_base.md").read_text(encoding="utf-8")
FULL_SYSTEM = f"{SYSTEM_PROMPT}\n\n---\n\n# KNOWLEDGE BASE\n\n{KNOWLEDGE_BASE}"

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
creds = Credentials.from_service_account_info(json.loads(GOOGLE_CREDS_JSON), scopes=SCOPES)
sheet = gspread.authorize(creds).open_by_key(GOOGLE_SHEET_ID).sheet1

conversations: dict[str, list[dict]] = {}  # keyed by WhatsApp phone number

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


def send_whatsapp_message(to: str, text: str) -> None:
    url = f"https://graph.facebook.com/v21.0/{WHATSAPP_PHONE_ID}/messages"
    headers = {"Authorization": f"Bearer {WHATSAPP_ACCESS_TOKEN}"}
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": text},
    }
    r = requests.post(url, headers=headers, json=payload, timeout=15)
    if not r.ok:
        log.error(f"WA send failed: {r.status_code} {r.text}")


def notify_faridun(msg: str) -> None:
    try:
        requests.post(
            f"https://api.telegram.org/bot{FARIDUN_TELEGRAM_BOT_TOKEN}/sendMessage",
            json={"chat_id": FARIDUN_CHAT_ID, "text": msg},
            timeout=10,
        )
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
@app.route("/whatsapp", methods=["GET"])
def verify():
    if (
        request.args.get("hub.mode") == "subscribe"
        and request.args.get("hub.verify_token") == VERIFY_TOKEN
    ):
        return request.args.get("hub.challenge"), 200
    return "Verification failed", 403


@app.route("/whatsapp", methods=["POST"])
def webhook():
    signature = request.headers.get("X-Hub-Signature-256", "")
    if not verify_signature(request.data, signature):
        abort(403)

    data = request.json

    for entry in data.get("entry", []):
        for change in entry.get("changes", []):
            value = change.get("value", {})
            messages = value.get("messages", [])
            contacts = value.get("contacts", [])

            for msg in messages:
                if msg.get("type") != "text":
                    continue

                from_number = msg["from"]
                text = msg["text"]["body"]
                contact_name = contacts[0]["profile"]["name"] if contacts else ""

                log.info(f"WA from {from_number} ({contact_name}): {text[:80]}")

                try:
                    reply, is_hot = ask_claude(from_number, text)
                except Exception as e:
                    log.error(f"Claude error: {e}")
                    reply = "Kechirasiz, bir oz kuting, tez javob beraman 🙏"
                    is_hot = False

                send_whatsapp_message(from_number, reply)

                log_to_sheet([
                    datetime.now().isoformat(timespec="seconds"),
                    "whatsapp",
                    from_number,
                    contact_name,
                    "",
                    text,
                    reply,
                    "HOT" if is_hot else "ACTIVE",
                ])

                if is_hot:
                    notify_faridun(
                        f"🔥 HOT LEAD (WhatsApp) 🔥\n\n"
                        f"Phone: +{from_number}\n"
                        f"Name: {contact_name}\n"
                        f"Last message: {text}\n\n"
                        f"Bot reply: {reply}"
                    )

    return "OK", 200


@app.route("/", methods=["GET"])
def health():
    return "SAT Samarkand WhatsApp bot running 🟢", 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8001)))
