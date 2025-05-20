
import os
import asyncio
import traceback
from dotenv import load_dotenv
from supabase import create_client
import telegram

load_dotenv(dotenv_path="env.txt")

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

print(f"[환경변수 체크] SUPABASE_URL: {SUPABASE_URL}")
print(f"[환경변수 체크] TELEGRAM_BOT_TOKEN 존재 여부: {bool(TELEGRAM_BOT_TOKEN)}")

async def send_message(text):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("[오류] 텔레그램 토큰 또는 챗ID 누락됨")
        return
    try:
        bot = telegram.Bot(token=TELEGRAM_BOT_TOKEN)
        await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=text)
        print("[텔레그램 메시지 전송 성공]")
    except telegram.error.Unauthorized:
        print("[텔레그램 오류] Unauthorized - 잘못된 토큰")
    except Exception as e:
        print(f"[텔레그램 전송 오류]: {e}")

def log_supabase_status():
    if not SUPABASE_URL or not SUPABASE_ANON_KEY:
        print("[오류] Supabase URL 또는 키 누락")
        return
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
        response = supabase.table("messages").insert({
            "message": "✅ Supabase 삽입 테스트 - 상세 오류 로깅"
        }).execute()
        print("[DB 삽입 성공]", response)
    except Exception:
        print("[DB 오류 발생]:")
        print(traceback.format_exc())
        asyncio.run(send_message("[시스템 오류] Supabase 삽입 실패 - 관리자 확인 필요"))

if __name__ == "__main__":
    log_supabase_status()
    asyncio.run(send_message("✅ 시스템 실행됨: 로그 상세 모드"))
