import os
from datetime import datetime
from supabase import create_client, Client
import time
import requests

# 환경변수에서 Supabase 정보 불러오기
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# 디버깅 출력
print("[환경변수 디버깅]")
print("SUPABASE_URL:", SUPABASE_URL)
print("SUPABASE_KEY:", SUPABASE_KEY)

# Supabase 클라이언트 생성
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Supabase에 상태 메시지 삽입
try:
    data = {
        "content": "서버 상태 정상 ✅",
        "timestamp": datetime.utcnow().isoformat()  # ← NOT NULL 컬럼 대응
    }
    res = supabase.table("messages").insert(data).execute()
    print("[✅ Supabase 삽입 성공]")
except Exception as e:
    print("[❌ Supabase 삽입 실패 - APIError]")
    print("에러 메시지:", str(e))

# 텔레그램 메시지 전송
try:
    message = "🔔 서버 작동 중입니다. Supabase 삽입 시도 완료"
    telegram_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message
    }
    telegram_res = requests.post(telegram_url, data=payload)
    if telegram_res.status_code == 200:
        print("[텔레그램 메시지 전송 성공]")
    else:
        print("[텔레그램 메시지 전송 실패]")
        print(telegram_res.text)
except Exception as e:
    print("[텔레그램 오류]", str(e))
