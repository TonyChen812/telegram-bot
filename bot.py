import os
from flask import Flask, request
from telegram import Bot

TOKEN = os.getenv("BOT_TOKEN")

app = Flask(__name__)
bot = Bot(TOKEN)

@app.route("/")
def home():
    return "Bot is running"

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json(force=True)

    chat_id = data["message"]["chat"]["id"]
    text = data["message"].get("text", "")

    bot.send_message(chat_id=chat_id, text=f"You said: {text}")

    return "ok"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
