from fastapi import FastAPI, Request
import requests
from supabase import create_client
import os
import datetime

# === 🔐 설정값 ===
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_IDS = os.getenv("CHAT_IDS", "").split(",")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# === 🧩 Supabase 클라이언트 초기화 ===
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# === 🚀 FastAPI 앱 시작 ===
app = FastAPI()

# === ✉️ 텔레그램 메시지 전송 함수 ===
def send_telegram_message(message: str):
    for chat_id in CHAT_IDS:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {"chat_id": chat_id, "text": message, "parse_mode": "Markdown"}
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

# === 📩 메시지 전송 API ===
@app.post("/send-message")
async def send_message(request: Request):
    data = await request.json()
    message = data.get("message", "")
    if not message:
        return {"status": "fail", "message": "❌ 메시지가 비어 있음"}
    send_telegram_message(message)
    insert_to_supabase(message)
    return {"status": "success", "message": "✅ 메시지 전송 및 기록 완료"}

# === 🟢 서버 상태 확인 ===
@app.get("/")
def root():
    return {"status": "OK", "message": "서버 연결 정상 ✅"}
