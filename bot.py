from groq import Groq
import os
import time
from flask import Flask, request
from telegram import Bot

# ======================
# ENV CHECK (IMPORTANT)
# ======================
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

def get_ai_response(text):
    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": "You are a helpful Telegram bot assistant."},
                {"role": "user", "content": text}
            ],
            temperature=0.7,
        )

        return response.choices[0].message.content

    except Exception as e:
        return "⚠️ AI error. Try again later."

# ======================
@app.route("/")
def home():
    return "Bot is running"

# ======================
@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json(force=True)

    if "message" not in data:
        return "ok"

    update_id = data.get("update_id")

    # prevent duplicates
    if update_id in processed_updates:
        return "ok"
    processed_updates.add(update_id)

    message = data["message"]
    chat_id = message["chat"]["id"]
    text = message.get("text", "")

    if not text:
        return "ok"

    if text.startswith("/"):
        return "ok"

    if text == "/start":
        send_message(chat_id, "👋 Welcome!")

    elif text == "/help":
        send_message(chat_id, "Commands: /start /help /status")

    elif text == "/status":
        uptime = int(time.time() - START_TIME)
        send_message(chat_id, f"🟢 Running\n⏱ {uptime}s")

    else:
        reply = get_ai_response(text)
        send_message(chat_id, reply)

    return "ok"


# ======================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
