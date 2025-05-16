import os
import requests
from supabase import create_client
from datetime import datetime

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def insert_message(msg):
    now = datetime.now().isoformat()
    try:
        supabase.table("messages").insert({"msg": msg, "time": now}).execute()
        return True
    except Exception as e:
        print("Supabase 삽입 실패:", e)
        return False

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": msg}
    try:
        res = requests.post(url, data=data)
        print("텔레그램 응답:", res.text)
    except Exception as e:
        print("텔레그램 전송 실패:", e)

if __name__ == "__main__":
    msg = "✅ 서버 작동 확인됨"
    if insert_message(msg):
        send_telegram("✅ Supabase 연동 성공 + 메시지 저장 완료")
    else:
        send_telegram("❌ Supabase 삽입 실패 - 설정 확인 필요")