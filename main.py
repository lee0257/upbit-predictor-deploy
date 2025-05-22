from fastapi import FastAPI, Request
import requests
from supabase import create_client
import os

# === 🔐 설정값 ===
TELEGRAM_TOKEN = "7287889681:AAHqKbipumgMmRQ8J4_Zu8Nlu_CYDnbCt0U"
CHAT_IDS = ["1901931119"]  # 수신 대상자 리스트 (친구 제외됨)

SUPABASE_URL = "https://gzqpbywussubofgbsydw.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imd6cXBieXd1c3N1Ym9mZ2JzeWR3Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDgyMzAwMDMsImV4cCI6MjA2Mzc4NjAwM30.rkE-N_mBlSYOYQnXUTuodRCfAl6ogfwl3q-j_1xguB8"

# === 🧩 Supabase 클라이언트 초기화 ===
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# === 🚀 FastAPI 앱 시작 ===
app = FastAPI()

# === ✉️ 텔레그램 메시지 전송 함수 ===
def send_telegram_message(message: str):
    for chat_id in CHAT_IDS:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": message,
            "parse_mode": "Markdown"
        }
        try:
            response = requests.post(url, json=payload, timeout=10)
            print("텔레그램 응답:", response.status_code, response.text)
        except Exception as e:
            print(f"[오류] 텔레그램 전송 실패: {e}")

# === 💾 Supabase 저장 함수 ===
def insert_to_supabase(message: str):
    try:
        supabase.table("messages").insert({"content": message}).execute()
        print("✅ Supabase 저장 성공")
    except Exception as e:
        print(f"[오류] Supabase 저장 실패: {e}")

# === 🔁 POST: 수동추천 메시지 전송 엔드포인트 ===
@app.post("/send-message")
async def send_message(request: Request):
    data = await request.json()
    message = data.get("message", "")

    if not message:
        return {"status": "fail", "message": "❌ 메시지가 비어 있습니다"}

    send_telegram_message(message)
    insert_to_supabase(message)

    return {"status": "success", "message": "✅ 텔레그램 및 Supabase 전송 완료"}

# === 🟢 GET: 서버 연결 확인 라우트 ===
@app.get("/")
def root():
    return {"status": "OK", "message": "서버 연결되었습니다 ✅"}
