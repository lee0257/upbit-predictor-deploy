from flask import Flask, request
import requests
import json
import os
from datetime import datetime

app = Flask(__name__)

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_ANON_KEY = os.environ.get("SUPABASE_ANON_KEY")

@app.route("/")
def home():
    return "🔥 업비트 예측기 서버 정상 작동 중입니다!"

@app.route("/send")
def send_message():
    try:
        message = "[환경변수 테스트] Supabase 기록 + Telegram 전송 성공 🎯"
        headers = {
            "apikey": SUPABASE_ANON_KEY,
            "Authorization": f"Bearer {SUPABASE_ANON_KEY}",
            "Content-Type": "application/json",
        }
        data = {
            "message": message,
            "timestamp": datetime.utcnow().isoformat()
        }
        supabase_res = requests.post(
            f"{SUPABASE_URL}/rest/v1/messages",
            headers=headers,
            data=json.dumps(data)
        )
        telegram_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        telegram_payload = {
            "chat_id": CHAT_ID,
            "text": message
        }
        telegram_res = requests.post(telegram_url, data=telegram_payload)

        return {
            "supabase_status": supabase_res.status_code,
            "telegram_status": telegram_res.status_code,
            "message": message
        }

    except Exception as e:
        return {"error": str(e)}, 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
