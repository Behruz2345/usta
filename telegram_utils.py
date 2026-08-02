import requests
from config import BOT_TOKEN

API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"


def send_message(chat_id, text, reply_markup=None):
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
    if reply_markup:
        payload["reply_markup"] = reply_markup
    try:
        r = requests.post(f"{API_URL}/sendMessage", json=payload, timeout=10)
        data = r.json()
        if data.get("ok"):
            return data["result"]["message_id"]
    except Exception as e:
        print("Telegram send_message xatosi:", e)
    return None


def edit_message(chat_id, message_id, text, reply_markup=None):
    payload = {"chat_id": chat_id, "message_id": message_id, "text": text, "parse_mode": "HTML"}
    if reply_markup:
        payload["reply_markup"] = reply_markup
    try:
        requests.post(f"{API_URL}/editMessageText", json=payload, timeout=10)
    except Exception as e:
        print("Telegram edit_message xatosi:", e)


def order_keyboard(order_id):
    return {
        "inline_keyboard": [
            [
                {"text": "✅ Qabul qilish", "callback_data": f"accept_{order_id}"},
                {"text": "❌ Bekor qilish", "callback_data": f"decline_{order_id}"},
            ]
        ]
    }
