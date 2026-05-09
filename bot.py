from groq import Groq
import os
import time
from flask import Flask, request
from telegram import Bot

# ======================
# ENV CHECK (IMPORTANT)
# ======================
client = Groq(api_key=os.getenv("GROQ_API_KEY"))
TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    raise Exception("BOT_TOKEN is missing in environment variables")

app = Flask(__name__)
bot = Bot(TOKEN)

# ======================
# GLOBAL STATE
# ======================
processed_updates = set()
START_TIME = time.time()

# ======================
# SAFE SEND
# ======================
def send_message(chat_id, text):
    import requests

    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text
    }

    requests.post(url, json=payload)

# ======================
def get_ai_response(text):
    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a helpful Telegram assistant. "
                        "Do NOT invent Telegram features, business modes, or APIs. "
                        "If unsure, say you are not sure."
                    )
                },
                {"role": "user", "content": text}
            ],
            temperature=0.7,
        )

        return response.choices[0].message.content

    except Exception as e:
        print("AI error:", e)
        return "⚠️ AI error. Try again later."

# ======================
@app.route("/")
def home():
    return "Bot is running"

# ======================
@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json(force=True)

    # ======================
    # SUPPORT ALL TELEGRAM UPDATE TYPES
    # ======================
    message = (
        data.get("message")
        or data.get("business_message")
        or data.get("channel_post")
    )

    if not message:
        return "ok"

    update_id = data.get("update_id")
    if update_id in processed_updates:
        return "ok"
    processed_updates.add(update_id)

    chat_id = message.get("chat", {}).get("id")
    text = message.get("text", "")

    if not chat_id or not text:
        return "ok"

    # ======================
    # COMMAND HANDLING
    # ======================
    if text.startswith("/"):
        cmd = text.split()[0].lower()

        if cmd == "/start":
            send_message(chat_id, "👋 Welcome! I am your AI assistant bot.")
            return "ok"

        elif cmd == "/help":
            send_message(chat_id, "Commands:\n/start\n/help\n/status")
            return "ok"

        elif cmd == "/status":
            uptime = int(time.time() - START_TIME)
            send_message(chat_id, f"🟢 Running\n⏱ {uptime}s")
            return "ok"

        return "ok"

    # ======================
    # AI RESPONSE
    # ======================
    reply = get_ai_response(text)
    send_message(chat_id, reply)

    return "ok"


# ======================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
