from groq import Groq
import os
import time
from flask import Flask, request

# ======================
# ENV CHECK
# ======================
client = Groq(api_key=os.getenv("GROQ_API_KEY"))
TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    raise Exception("BOT_TOKEN is missing in environment variables")

app = Flask(__name__)

# ======================
# GLOBAL STATE
# ======================
processed_updates = set()
START_TIME = time.time()

# 🔥 MEMORY (with limit to avoid RAM crash on Render)
user_memory = {}
MAX_MEMORY = 20  # keep last 20 messages per user

# ======================
# SAFE SEND
# ======================
def send_message(chat_id, text):
    import requests

    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, json={
        "chat_id": chat_id,
        "text": text
    })

# ======================
# TYPING EFFECT
# ======================
def send_typing(chat_id):
    import requests

    url = f"https://api.telegram.org/bot{TOKEN}/sendChatAction"
    requests.post(url, json={
        "chat_id": chat_id,
        "action": "typing"
    })

# small delay so typing is visible
def safe_typing(chat_id):
    send_typing(chat_id)
    time.sleep(0.8)

# ======================
# MEMORY BUILDER (safe)
# ======================
def build_messages(user_id, text):
    if user_id not in user_memory:
        user_memory[user_id] = []

    history = user_memory[user_id]

    messages = [
        {
            "role": "system",
            "content": (
    "You are a Telegram chat assistant running inside a Python Flask bot. "
    "You do NOT know server specs, RAM, CPU, or system configuration unless explicitly provided. "
    "If asked about memory, limits, infrastructure, or system behavior: "
    "respond with 'I do not have access to system-level details'. "
    "Never guess numbers like MB, GB, or limits. "
    "Be consistent across responses."
)
        }
    ]

    messages.extend(history[-10:])
    messages.append({"role": "user", "content": text})

    return messages

# ======================
def get_ai_response(user_id, text):
    try:
        messages = build_messages(user_id, text)

        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=messages,
            temperature=0.7,
        )

        reply = response.choices[0].message.content

        # 🔥 memory cap (prevents RAM overflow)
        if user_id not in user_memory:
            user_memory[user_id] = []

        user_memory[user_id].append({"role": "user", "content": text})
        user_memory[user_id].append({"role": "assistant", "content": reply})

        # trim memory
        user_memory[user_id] = user_memory[user_id][-MAX_MEMORY:]

        return reply

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
    # COMMANDS
    # ======================
    if text.startswith("/"):
        cmd = text.split()[0].lower()

        if cmd == "/start":
            send_message(chat_id, "👋 Welcome!")
        elif cmd == "/help":
            send_message(chat_id, "Commands: /start /help /status")
        elif cmd == "/status":
            uptime = int(time.time() - START_TIME)
            send_message(chat_id, f"🟢 Running\n⏱ {uptime}s")

        return "ok"

    # ======================
    # AI RESPONSE + TYPING
    # ======================
    safe_typing(chat_id)

    reply = get_ai_response(chat_id, text)
    send_message(chat_id, reply)

    return "ok"


# ======================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
