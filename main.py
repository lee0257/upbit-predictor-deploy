
import os
import asyncio
from dotenv import load_dotenv
from supabase import create_client, Client
import telegram

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Debug logs
print(f"SUPABASE_URL: {SUPABASE_URL}")
print(f"SUPABASE_ANON_KEY valid: {bool(SUPABASE_ANON_KEY)}")
print(f"TELEGRAM_BOT_TOKEN valid: {bool(TELEGRAM_BOT_TOKEN)}")
print(f"TELEGRAM_CHAT_ID: {TELEGRAM_CHAT_ID}")

try:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
    response = supabase.table("messages").select("*").limit(1).execute()
    print("[DB 연결 성공]", response)
except Exception as e:
    print("[DB 오류]:", e)

async def send_message(text):
    try:
        bot = telegram.Bot(token=TELEGRAM_BOT_TOKEN)
        await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=text)
        print("[텔레그램 메시지 전송 성공]")
    except telegram.error.Unauthorized as e:
        print("[텔레그램 오류]: Unauthorized - 토큰 오류")
    except Exception as e:
        print("[텔레그램 오류]:", e)

asyncio.run(send_message("[시스템 알림] 서버가 정상적으로 시작되었습니다."))
