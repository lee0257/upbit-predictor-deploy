from flask import Flask, request
import requests
import json
import os
from datetime import datetime

app = Flask(__name__)

# 환경변수에서 설정값 불러오기
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_ANON_KEY = os.environ.get("SUPABASE_ANON_KEY")

@app.route("/")
def home():
    return "환경변수 기반 Supabase + Telegram 서버 실행 중"

@app.route("/send")
def send_message():
    message = "[환경변수 테스트] Supabase 기록 + Telegram 전송 성공 🎯"

    # Supabase에 저장
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

    # Telegram 전송
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

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
