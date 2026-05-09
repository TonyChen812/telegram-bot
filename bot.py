import os
from flask import Flask
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

TOKEN = os.getenv("BOT_TOKEN")

# ---------------- TELEGRAM BOT ----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Bot is alive")

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(update.message.text)

bot = Application.builder().token(TOKEN).build()
bot.add_handler(CommandHandler("start", start))
bot.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

# ---------------- FLASK ----------------
app = Flask(__name__)

@app.route("/")
def home():
    return "Bot is running"

# ---------------- RUN ----------------
if __name__ == "__main__":
    import threading

    def run_bot():
        bot.run_polling()

    threading.Thread(target=run_bot, daemon=True).start()

    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
