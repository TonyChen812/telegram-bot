from groq import Groq
import os
import time
from flask import Flask, request
import requests
import re

# ======================
# ENV CHECK
# ======================
client = Groq(api_key=os.getenv("GROQ_API_KEY"))
TOKEN = os.getenv("BOT_TOKEN")
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")

if not TOKEN:
    raise Exception("BOT_TOKEN is missing in environment variables")

app = Flask(__name__)

# ======================
# GLOBAL STATE
# ======================
processed_updates = set()
START_TIME = time.time()

user_memory = {}
MAX_MEMORY = 20

# ======================
# 🌐 WEB SEARCH
# ======================
def search_web(query):
    try:
        url = "https://api.duckduckgo.com/"
        params = {
            "q": query,
            "format": "json",
            "no_html": 1,
            "skip_disambig": 1
        }

        r = requests.get(url, params=params, timeout=5)
        data = r.json()

        return {
            "answer": data.get("AbstractText", ""),
            "source": data.get("AbstractURL", ""),
            "related": [t["Text"] for t in data.get("RelatedTopics", [])[:5] if isinstance(t, dict)]
        }

    except Exception as e:
        print("Web search error:", e)
        return {"answer": "", "source": "", "related": []}

# ======================
# 🎥 YOUTUBE SEARCH
# ======================
def search_youtube(query):
    if not YOUTUBE_API_KEY:
        return None

    try:
        url = "https://www.googleapis.com/youtube/v3/search"
        params = {
            "part": "snippet",
            "q": query,
            "type": "video",
            "maxResults": 1,
            "key": YOUTUBE_API_KEY
        }

        r = requests.get(url, params=params, timeout=5)
        data = r.json()

        if "items" not in data or not data["items"]:
            return None

        video = data["items"][0]
        video_id = video["id"]["videoId"]

        return {
            "title": video["snippet"]["title"],
            "url": f"https://www.youtube.com/watch?v={video_id}"
        }

    except Exception as e:
        print("YouTube error:", e)
        return None

# ======================
# SAFE SEND
# ======================
def send_message(chat_id, text):
    requests.post(
        f"https://api.telegram.org/bot{TOKEN}/sendMessage",
        json={"chat_id": chat_id, "text": text}
    )

# ======================
# TYPING
# ======================
def send_typing(chat_id):
    requests.post(
        f"https://api.telegram.org/bot{TOKEN}/sendChatAction",
        json={"chat_id": chat_id, "action": "typing"}
    )

def safe_typing(chat_id):
    send_typing(chat_id)
    time.sleep(0.8)

# ======================
# MEMORY + PROMPT
# ======================
def build_messages(user_id, text, web_data=None, youtube_data=None):
    if user_id not in user_memory:
        user_memory[user_id] = []

    messages = [
        {
            "role": "system",
            "content": (
                "You are a Telegram assistant. "
                "DO NOT generate or guess any URLs or links. "
                "Never output fake links. "
                "Only describe content. "
                "All links will be added by system."
            )
        }
    ]

    if web_data:
        messages.append({"role": "system", "content": f"Web: {web_data}"})

    if youtube_data:
        messages.append({"role": "system", "content": f"YouTube: {youtube_data}"})

    messages.extend(user_memory[user_id][-10:])
    messages.append({"role": "user", "content": text})

    return messages

# ======================
def get_ai_response(user_id, text):
    try:
        web_data = None
        youtube_data = None

        lower = text.lower()

        if any(w in lower for w in ["youtube", "song", "video", "music"]):
            youtube_data = search_youtube(text)

        elif any(w in lower for w in ["news", "search", "what is", "latest"]):
            web_data = search_web(text)

        messages = build_messages(user_id, text, web_data, youtube_data)

        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=messages,
            temperature=0.7,
        )

        reply = response.choices[0].message.content

        # strip fake links
        reply = re.sub(r"https?://\S+", "", reply).strip()

        user_memory[user_id].append({"role": "user", "content": text})
        user_memory[user_id].append({"role": "assistant", "content": reply})

        user_memory[user_id] = user_memory[user_id][-MAX_MEMORY:]

        if youtube_data:
            reply += f"\n\n▶️ Watch: {youtube_data['url']}"

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
    # COMMANDS (FIXED INDENTATION)
    # ======================
    if text.startswith("/"):
        cmd = text.split()[0].lower()

        if cmd == "/start":
            send_message(
                chat_id,
                "👋 Welcome!\n\n"
                "I’m Nova, your AI assistant bot.\n"
                "Just send me a message and I’ll respond.\n\n"
                "Type /help to see commands."
            )

        elif cmd == "/help":
            send_message(
                chat_id,
                "📌 Commands:\n"
                "/start - start the bot\n"
                "/help - show this menu\n"
                "/status - check uptime\n"
                "/clear - clear AI's Memory\n\n"
                "💬 You can also chat normally with me."
            )

        elif cmd == "/status":
            uptime = int(time.time() - START_TIME)
            minutes = uptime // 60
            seconds = uptime % 60

            send_message(
                chat_id,
                f"🟢 Bot is running\n"
                f"⏱ Uptime: {minutes}m {seconds}s"
            )
            
        elif cmd == "/clear":
            user_memory[chat_id] = []
            send_message(chat_id, "🧹 Memory cleared.")
            
        else:
            send_message(chat_id, "❓ Unknown command. Type /help")

        return "ok"

    # ======================
    # AI RESPONSE
    # ======================
    safe_typing(chat_id)
    reply = get_ai_response(chat_id, text)
    send_message(chat_id, reply)

    return "ok"


# ======================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
