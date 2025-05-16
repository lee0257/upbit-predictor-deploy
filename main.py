import os
from datetime import datetime
from supabase import create_client, Client
import requests

print("🚀 [main.py] Render 서버 실행 시작")

# ---------------- Supabase 연결 ----------------
SUPABASE_URL = os.getenv("SUPABASE_URL") or "https://ulggfjvrpixgxcwithhx.supabase.co"
SUPABASE_KEY = os.getenv("SUPABASE_KEY") or "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InVsZ2dmanZycGl4Z3hjd2l0aGh4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDc5MzE2NjEsImV4cCI6MjA2MzQ2NzY2MX0.LnufUEKAH9sCq6KgJGLjLGwJj_RiLRKTCm01Xoi2dBk"

# ---------------- 텔레그램 설정 ----------------
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN") or "7287889681:AAGM2BXvqJSyzbCrF25hy_WzCL40Cute64A"
TELEGRAM_CHAT_IDS = [
    "1901931119",     # 너
    "6437712196"      # 친구
]

# ---------------- Supabase 연결 시도 ----------------
try:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    print("✅ Supabase 연결 성공")
except Exception as e:
    print(f"❌ Supabase 연결 실패: {e}")
    exit()

# ---------------- Supabase 삽입 테스트 ----------------
def test_supabase_insert():
    try:
        now = datetime.now().isoformat()
        result = supabase.table("test_table").insert({
            "msg": "✅ 새 토큰으로 삽입 성공 🎉",
            "time": now
        }).execute()
        print("📝 Supabase 삽입 성공:", result)
    except Exception as e:
        print("❌ Supabase 삽입 실패:", e)

# ---------------- 텔레그램 메시지 전송 ----------------
def test_telegram_send():
    for chat_id in TELEGRAM_CHAT_IDS:
        try:
            url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
            message = f"✅ 새 토큰 적용 성공\n🚀 Render 서버 연결 정상\n📡 Supabase 연동도 완료됨"
            response = requests.post(url, data={
                "chat_id": chat_id,
                "text": message
            })
            print(f"📨 [{chat_id}] 응답:", response.text)
        except Exception as e:
            print(f"❌ [{chat_id}] 텔레그램 전송 실패:", e)

# ---------------- 실행 ----------------
if __name__ == "__main__":
    print("🔁 테스트 시작")
    test_supabase_insert()
    test_telegram_send()
    print("🎯 모든 테스트 완료")
