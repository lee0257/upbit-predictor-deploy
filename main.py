import os
from datetime import datetime
from supabase import create_client, Client
import requests

print("🚀 [main.py] Render 서버 실행 시작")

# ---------------- Supabase 설정 ----------------
SUPABASE_URL = os.getenv("SUPABASE_URL") or "https://ulggfjvrpixgxcwithhx.supabase.co"
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# ---------------- Telegram 설정 ----------------
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN") or "6368267307:AAEHz-kub2s-ZKeVDb94FZVD5DyJrPZjN3o"
TELEGRAM_CHAT_IDS = [
    "1901931119",     # 너
    "6437712196"      # 친구 ID (자동 포함)
]

# ---------------- Supabase 연결 ----------------
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
            "msg": "Render Supabase 삽입 테스트",
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
            msg = f"✅ Render 서버에서 메시지 전송 테스트 완료\n수신자: {chat_id}"
            response = requests.post(url, data={
                "chat_id": chat_id,
                "text": msg
            })
            print(f"📨 [{chat_id}] 응답: {response.text}")
        except Exception as e:
            print(f"❌ [{chat_id}] 텔레그램 전송 실패:", e)

# ---------------- 실행 ----------------
if __name__ == "__main__":
    print("🔁 테스트 시작")
    test_supabase_insert()
    test_telegram_send()
    print("🎯 모든 테스트 완료")
