import os
import requests
import base64
from flask import Flask, request

# -----------------------------
# Environment Variables
# -----------------------------
BOT_TOKEN = os.environ.get("BOT_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
PORT = int(os.environ.get("PORT", 5000))

WEBHOOK_URL = f"https://gpt-premium-shadow.onrender.com/{BOT_TOKEN}"  # Change if needed
API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/"

# Gemini API
GEMINI_MODEL = "gemini-2.0-flash"
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}"
IMAGEN_URL = f"https://generativelanguage.googleapis.com/v1beta/models/imagen-3.0:generateImage?key={GEMINI_API_KEY}"

app = Flask(__name__)

# -----------------------------
# User conversation context
# -----------------------------
user_context = {}  # {user_id: [messages]}

# -----------------------------
# Gemini Chat Function
# -----------------------------
def chat_with_ai(user_id, prompt: str) -> str:
    try:
        messages = user_context.get(user_id, [])
        messages.append({"role": "user", "content": prompt})

        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": prompt}
                    ]
                }
            ]
        }

        response = requests.post(
            GEMINI_URL,
            headers={"Content-Type": "application/json"},
            json=payload,
            timeout=10
        )

        if response.status_code == 200:
            data = response.json()
            answer = data["candidates"][0]["content"]["parts"][0]["text"]

            messages.append({"role": "assistant", "content": answer})
            user_context[user_id] = messages[-10:]
            return answer
        else:
            return f"⚠ Gemini API Error: {response.text}"

    except Exception as e:
        return f"⚠ Gemini Exception: {e}"

# -----------------------------
# Gemini Image Function
# -----------------------------
def generate_image(prompt: str):
    try:
        payload = {
            "prompt": {"text": prompt},
            "sampleCount": 1,
            "imageFormat": "PNG"
        }

        response = requests.post(
            IMAGEN_URL,
            headers={"Content-Type": "application/json"},
            json=payload,
            timeout=20
        )

        if response.status_code == 200:
            data = response.json()
            img_base64 = data["images"][0]["imageBytes"]
            return base64.b64decode(img_base64)  # raw image bytes
        else:
            return None
    except Exception as e:
        print("Image generation error:", e)
        return None

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

def send_photo(chat_id, image_bytes, caption=""):
    try:
        files = {"photo": ("image.png", image_bytes)}
        data = {"chat_id": chat_id, "caption": caption}
        requests.post(API_URL + "sendPhoto", data=data, files=files, timeout=15)
    except Exception as e:
        print("Telegram photo send error:", e)

# -----------------------------
# Menu Buttons
# -----------------------------
main_menu = [
    [{"text": "💬 Ask AI", "switch_inline_query_current_chat": ""}],
    [{"text": "🖼 Generate Image", "callback_data": "image_help"}],
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
    return "🤖 Professional Gemini Telegram Bot Running!"

@app.route(f"/{BOT_TOKEN}", methods=["POST"])
def webhook():
    update = request.get_json()
    print("Request JSON:", update)

    if "message" in update:
        message = update["message"]
        chat_id = message["chat"]["id"]
        user_id = message["from"]["id"]
        text = message.get("text", "")

        if text == "/start":
            send_message(
                chat_id,
                "👋 Welcome to *Professional Gemini Bot* 🤖\n\n"
                "Type anything to chat with AI or use the menu below ⬇️\n\n"
                "━━━━━━━━━━━━━━━\n"
                "👤 *Credits: SHADOW JOKER*",
                main_menu
            )

        elif text.startswith("/image"):
            prompt = text.replace("/image", "").strip()
            if not prompt:
                send_message(chat_id, "✍️ Usage: `/image your prompt`", main_menu)
            else:
                send_message(chat_id, "🎨 Generating image... Please wait ⏳")
                img_bytes = generate_image(prompt)
                if img_bytes:
                    send_photo(chat_id, img_bytes, caption=f"🖼 Prompt: {prompt}")
                else:
                    send_message(chat_id, "⚠ Failed to generate image. Try again later.", main_menu)

        elif text == "/help":
            send_message(
                chat_id,
                "⚡ *Help Menu* ⚡\n\n"
                "- Type your message and get AI response.\n"
                "- /image <prompt> : Generate AI image.\n"
                "- Use the menu buttons for quick actions.\n"
                "- /reset : Reset your conversation memory.",
                main_menu
            )

        elif text == "/about":
            send_message(
                chat_id,
                "ℹ️ *About Professional Gemini Bot*\n\n"
                "This bot uses Google Gemini API (Text + Image).\n"
                "Developer: SHADOW JOKER",
                main_menu
            )

        elif text == "/reset":
            user_context[user_id] = []
            send_message(chat_id, "♻️ Your conversation memory has been reset.", main_menu)

        else:
            reply = chat_with_ai(user_id, text)
            send_message(chat_id, reply, main_menu)

    elif "callback_query" in update:
        query = update["callback_query"]
        chat_id = query["message"]["chat"]["id"]
        user_id = query["from"]["id"]
        data = query["data"]

        if data == "about":
            send_message(
                chat_id,
                "ℹ️ *About Professional Gemini Bot*\n\n"
                "This bot uses Google Gemini API (Text + Image).\n"
                "Developer: SHADOW JOKER",
                main_menu
            )
        elif data == "credits":
            send_message(
                chat_id,
                "👤 *Credits*\n\n"
                "Developer: SHADOW JOKER\n"
                "Powered by Google Gemini",
                main_menu
            )
        elif data == "help":
            send_message(
                chat_id,
                "⚡ *Help Menu* ⚡\n\n"
                "- Type anything to chat with AI.\n"
                "- /image <prompt> : Generate AI image.\n"
                "- /reset : Clear conversation memory",
                main_menu
            )
        elif data == "image_help":
            send_message(
                chat_id,
                "🖼 *Image Generation Help*\n\n"
                "Use command:\n`/image your prompt`\n\n"
                "Example: `/image A hacker Joker sitting at neon computer desk`",
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
    try:
        res = requests.get(API_URL + "setWebhook", params={"url": WEBHOOK_URL})
        print("Webhook setup response:", res.json())
    except Exception as e:
        print("Webhook setup error:", e)

if __name__ == "__main__":
    set_webhook()
    app.run(host="0.0.0.0", port=PORT)
