import os
import requests
from supabase import create_client

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
TELEGRAM_CHAT_IDS = os.getenv("TELEGRAM_CHAT_IDS", "").split(",")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def send_telegram_message(text):
    for chat_id in TELEGRAM_CHAT_IDS:
        chat_id = chat_id.strip()
        if not chat_id:
            continue
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        data = {"chat_id": chat_id, "text": text}
        try:
            res = requests.post(url, json=data)
            print(f"📨 [{chat_id}] 응답: {res.text}")
        except Exception as e:
            print(f"❌ 텔레그램 전송 실패: {e}")

def insert_test_message():
    try:
        response = supabase.table("messages").insert({"text": "🚀 Render 서버 실행 시작"}).execute()
        print("✅ Supabase 삽입 성공")
    except Exception as e:
        print(f"❌ Supabase 삽입 실패: {e}")

def main():
    print("🚀 [main.py] Render 서버 실행 시작")
    insert_test_message()
    send_telegram_message("🔁 테스트 시작")
    send_telegram_message("🎯 모든 테스트 완료")

if __name__ == "__main__":
    main()
