from flask import Flask
from threading import Thread
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes
import os

BOT_TOKEN = os.getenv("BOT_TOKEN")

app_web = Flask(__name__)

@app_web.route("/")
def home():
    return "Bot is running!"

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(update.message.text)

bot = Application.builder().token(BOT_TOKEN).build()

bot.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

def run_bot():
    print("Bot running...")
    bot.run_polling()

Thread(target=run_bot).start()

port = int(os.environ.get("PORT", 10000))
app_web.run(host="0.0.0.0", port=port)
