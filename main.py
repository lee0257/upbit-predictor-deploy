import asyncio
import websockets
import json
import os
from datetime import datetime
import requests
from supabase import create_client

# 환경변수에서 정보 읽기
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Supabase 클라이언트 설정
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# 텔레그램 메시지 전송 함수
def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message
    }
    try:
        res = requests.post(url, data=payload)
        print(f"📨 [{TELEGRAM_CHAT_ID}] 응답:", res.json())
    except Exception as e:
        print("텔레그램 전송 오류:", e)

# Supabase 저장 함수
def save_to_supabase(message):
    try:
        now = datetime.utcnow().isoformat()
        data = {"msg": message, "time": now}
        supabase.table("messages").insert(data).execute()
        print("✅ Supabase 저장 성공")
    except Exception as e:
        print("❌ Supabase 삽입 실패:", e)

# 테스트 실행
if __name__ == "__main__":
    print("🚀 [main.py] Render 서버 실행 시작")

    # Supabase 연결 테스트
    try:
        supabase.table("messages").select("*").limit(1).execute()
        print("✅ Supabase 연결 성공")
    except Exception as e:
        print("❌ Supabase 연결 실패:", e)

    print("🔁 테스트 시작")

    message = "✅ 새 토큰 적용 성공\n🚀 Render 서버 연결 정상\n📡 Supabase 연동도 완료됨"
    send_telegram_message(message)
    save_to_supabase(message)

    print("🎯 모든 테스트 완료")
