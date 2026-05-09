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
    import asyncio
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(
        bot.send_message(chat_id=chat_id, text=text)
    )
    loop.close()

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

    if text == "/start":
        send_message(chat_id, "👋 Welcome!")

    elif text == "/help":
        send_message(chat_id, "Commands: /start /help /status")

    elif text == "/status":
        uptime = int(time.time() - START_TIME)
        send_message(chat_id, f"🟢 Running\n⏱ {uptime}s")

    else:
        send_message(chat_id, f"You said: {text}")

    return "ok"


# ======================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
