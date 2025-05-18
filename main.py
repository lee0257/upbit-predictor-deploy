from flask import Flask, request
import requests
import json
from datetime import datetime

app = Flask(__name__)

# 텔레그램 설정
TELEGRAM_TOKEN = "7287889681:AAGM2BXvqJSyzbCrF25hy_WzCL40Cute64A"
CHAT_ID = "1901931119"

# Supabase 설정
SUPABASE_URL = "https://gzqpbywussubofgbsydw.supabase.co"
SUPABASE_ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imd6cXBieXd1c3N1Ym9mZ2JzeWR3Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDgyMzAwMDMsImV4cCI6MjA2Mzc4NjAwM30.rkE-N_mBlSYOYQnXUTuodRCfAl6ogfwl3q-j_1xguB8"

@app.route("/")
def home():
    return "Supabase + Telegram 연동 서버 실행 중"

@app.route("/send")
def send_message():
    message = "[통합 테스트] Supabase 기록 + Telegram 전송 성공 🎯"

    # Supabase로 메시지 저장
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

    # 텔레그램으로 메시지 전송
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
