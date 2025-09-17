import os
import requests
from flask import Flask, request
import openai

# -----------------------------
# Environment Variables
# -----------------------------
BOT_TOKEN = os.environ.get("BOT_TOKEN")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

WEBHOOK_URL = f"https://your-bot-domain.com/{BOT_TOKEN}"  # Change to your deployed URL
API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/"

app = Flask(__name__)

# -----------------------------
# User conversation context
# -----------------------------
user_context = {}  # {user_id: [messages]}

# -----------------------------
# OpenAI Chat Function
# -----------------------------
def chat_with_ai(user_id, prompt: str) -> str:
    try:
        messages = user_context.get(user_id, [])
        messages.append({"role": "user", "content": prompt})

        response = openai.ChatCompletion.create(
            model="gpt-5-mini",
            messages=messages,
            api_key=OPENAI_API_KEY
        )

        answer = response.choices[0].message.content
        messages.append({"role": "assistant", "content": answer})

        # Save only last 10 messages per user to reduce memory
        user_context[user_id] = messages[-10:]
        return answer
    except Exception as e:
        return f"⚠ GPT Error: {e}"

# -----------------------------
# Send message helper
# -----------------------------
def send_message(chat_id, text, buttons=None):
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown"
    }
    if buttons:
        payload["reply_markup"] = {"inline_keyboard": buttons}
    try:
        requests.post(API_URL + "sendMessage", json=payload, timeout=5)
    except Exception as e:
        print("Telegram send error:", e)

# -----------------------------
# Menu Buttons
# -----------------------------
main_menu = [
    [{"text": "💬 Ask AI", "switch_inline_query_current_chat": ""}],
    [{"text": "ℹ️ About Bot", "callback_data": "about"}],
    [{"text": "❓ Help", "callback_data": "help"}],
    [{"text": "👤 Credits", "callback_data": "credits"}],
    [{"text": "🔄 Reset Chat", "callback_data": "reset"}]
]

# -----------------------------
# Flask Routes
# -----------------------------
@app.route("/")
def home():
    return "🤖 Professional ChatGPT Telegram Bot Running!"

@app.route(f"/{BOT_TOKEN}", methods=["POST"])
def webhook():
    update = request.get_json()

    # -----------------------------
    # Handle messages
    # -----------------------------
    if "message" in update:
        message = update["message"]
        chat_id = message["chat"]["id"]
        user_id = message["from"]["id"]
        text = message.get("text", "")

        # -----------------------------
        # Commands
        # -----------------------------
        if text == "/start":
            send_message(
                chat_id,
                "👋 Welcome to *Professional ChatGPT Bot* 🤖\n\n"
                "Type anything to chat with the AI or use the menu below ⬇️",
                main_menu
            )

        elif text == "/help":
            send_message(
                chat_id,
                "⚡ *Help Menu* ⚡\n\n"
                "- Type your message and get AI response.\n"
                "- Use the menu buttons for quick actions.\n"
                "- /reset : Reset your conversation memory.",
                main_menu
            )

        elif text == "/about":
            send_message(
                chat_id,
                "ℹ️ *About Professional ChatGPT Bot*\n\n"
                "This bot uses OpenAI GPT API to chat like ChatGPT.\n"
                "Developer: SHADOW JOKER",
                main_menu
            )

        elif text == "/reset":
            user_context[user_id] = []
            send_message(chat_id, "♻️ Your conversation memory has been reset.", main_menu)

        else:
            # Treat any other message as AI chat
            reply = chat_with_ai(user_id, text)
            send_message(chat_id, reply, main_menu)

    # -----------------------------
    # Handle callback queries
    # -----------------------------
    elif "callback_query" in update:
        query = update["callback_query"]
        chat_id = query["message"]["chat"]["id"]
        user_id = query["from"]["id"]
        data = query["data"]

        if data == "about":
            send_message(
                chat_id,
                "ℹ️ *About Professional ChatGPT Bot*\n\n"
                "This bot uses OpenAI GPT API to chat like ChatGPT.\n"
                "Developer: SHADOW JOKER",
                main_menu
            )
        elif data == "credits":
            send_message(
                chat_id,
                "👤 *Credits*\n\n"
                "Developer: SHADOW JOKER\n"
                "Powered by OpenAI GPT-5 mini",
                main_menu
            )
        elif data == "help":
            send_message(
                chat_id,
                "⚡ *Help Menu* ⚡\n\n"
                "- Type anything to chat with the AI.\n"
                "- Use the buttons to navigate.\n"
                "- /reset : Clear conversation memory",
                main_menu
            )
        elif data == "reset":
            user_context[user_id] = []
            send_message(chat_id, "♻️ Your conversation memory has been reset.", main_menu)

    return "ok"

# -----------------------------
# Set Webhook Automatically
# -----------------------------
def set_webhook():
    res = requests.get(API_URL + "setWebhook", params={"url": WEBHOOK_URL})
    print("Webhook setup response:", res.json())

# -----------------------------
if __name__ == "__main__":
    set_webhook()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)