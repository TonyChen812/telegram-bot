import os
from flask import Flask, request
from telegram import Bot, Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Load bot token from Render environment variables
TOKEN = os.getenv("BOT_TOKEN")

# Flask server (required for webhook)
app = Flask(__name__)

# Telegram Bot + Application
bot = Bot(TOKEN)
application = Application.builder().token(TOKEN).build()

# ---------------- HANDLERS ----------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Bot is alive 🚀")

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(update.message.text)

application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

# ---------------- ROUTES ----------------

@app.route("/")
def home():
    return "Bot is running"
    
@app.route("/webhook", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), bot)

    # Correct way to pass updates into python-telegram-bot v20+
    application.create_task(application.process_update(update))

    return "ok"

# ---------------- RUN SERVER ----------------

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
