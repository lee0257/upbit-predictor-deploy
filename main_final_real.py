from fastapi import FastAPI, Request
import requests
from supabase import create_client
import os

# === 🔐 Supabase 최신 설정 ===
SUPABASE_URL = "https://aoyrktsvybtuwsldpook.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImFveXJrdHN2eWJ0dXdzbGRwb29rIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDc5ODI5ODYsImV4cCI6MjA2MzU1ODk4Nn0.6YVuSOafiSKUrdIB6FufWWHWYc7utRjfcH-qktZ1_dA"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# === 🟢 FastAPI 앱 ===
app = FastAPI()

# === ✉️ 텔레그램 메시지 전송 함수 ===
def send_telegram_message(message: str):
    try:
        # 최신 토큰 Supabase에서 실시간 불러오기
        token_row = supabase.table("settings").select("telegram_token").limit(1).execute()
        TELEGRAM_TOKEN = token_row.data[0]["telegram_token"]

        CHAT_IDS = ["1901931119"]  # 수신자 리스트

        for chat_id in CHAT_IDS:
            url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
            payload = {
                "chat_id": chat_id,
                "text": message,
                "parse_mode": "Markdown"
            }
            response = requests.post(url, json=payload, timeout=10)
            print("텔레그램 응답:", response.status_code, response.text)

    except Exception as e:
        print(f"[오류] 텔레그램 전송 실패: {e}")

# === 💾 Supabase 메시지 저장 함수 ===
def insert_to_supabase(message: str):
    try:
        supabase.table("messages").insert({"content": message}).execute()
        print("✅ Supabase 저장 성공")
    except Exception as e:
        print(f"[오류] Supabase 저장 실패: {e}")

# === 🔁 POST: 메시지 전송 API ===
@app.post("/send-message")
async def send_message(request: Request):
    data = await request.json()
    message = data.get("message", "")

    if not message:
        return {"status": "fail", "message": "❌ 메시지가 비어 있습니다"}

    send_telegram_message(message)
    insert_to_supabase(message)

    return {"status": "success", "message": "✅ 텔레그램 및 Supabase 전송 완료"}

# === 🟢 GET: 서버 상태 확인
@app.get("/")
def root():
    return {"status": "OK", "message": "서버 연결 정상입니다 ✅"}
