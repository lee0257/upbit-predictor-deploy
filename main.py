import os
import requests
from flask import Flask
from datetime import datetime

app = Flask(__name__)

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

@app.route("/")
def home():
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    message = f"[Render 작동 확인] {now}"

    # Supabase 메시지 전송
    supabase_response = requests.post(
        f"{SUPABASE_URL}/rest/v1/messages",
        headers={
            "apikey": SUPABASE_ANON_KEY,
            "Authorization": f"Bearer {SUPABASE_ANON_KEY}",
            "Content-Type": "application/json",
            "Prefer": "return=representation"
        },
        json={"message": message}
    )

    # Telegram 메시지 전송
    telegram_response = requests.post(
        f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
        json={"chat_id": TELEGRAM_CHAT_ID, "text": message}
    )

    return {
        "message": message,
        "supabase_status": supabase_response.status_code,
        "telegram_status": telegram_response.status_code
    }

if __name__ == "__main__":
    app.run(debug=True)
