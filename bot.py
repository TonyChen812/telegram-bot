import os
import time
from flask import Flask, request
from telegram import Bot

TOKEN = os.getenv("BOT_TOKEN")

app = Flask(__name__)
bot = Bot(TOKEN)

# ======================
# SAFE SEND FUNCTION
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
# BOT START TIME (for /status)
# ======================
START_TIME = time.time()

# ======================
# ROUTES
# ======================
@app.route("/")
def home():
    return "Bot is running"

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

    text_lower = text.lower()

    if text_lower == "/start":
        send_message(chat_id, "👋 Welcome!")

    elif text_lower == "/help":
        send_message(chat_id, "Commands: /start /help /status")

    elif text_lower == "/status":
        send_message(chat_id, "🟢 Bot running")

    else:
        send_message(chat_id, f"You said: {text}")

    return "ok"

    # ======================
    # COMMANDS
    # ======================
    if text_lower == "/start":
        send_message(chat_id,
            "👋 Welcome! I'm your bot.\n\nType /help to see commands."
        )

    elif text_lower == "/help":
        send_message(chat_id,
            "📌 Commands:\n"
            "/start - Start bot\n"
            "/help - Show commands\n"
            "/status - Bot status"
        )

    elif text_lower == "/status":
        uptime = int(time.time() - START_TIME)
        send_message(chat_id,
            f"🟢 Bot is running\n⏱ Uptime: {uptime} seconds"
        )

    else:
        # default reply
        send_message(chat_id, f"You said: {text}")

    return "ok"


# ======================
# OPTIONAL WEBHOOK SET
# ======================
@app.before_first_request
def set_webhook():
    base_url = os.getenv("RENDER_EXTERNAL_URL")
    if base_url:
        bot.set_webhook(url=f"{base_url}/webhook")


# ======================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
