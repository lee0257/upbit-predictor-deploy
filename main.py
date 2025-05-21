import os
import time
import pytz
import asyncio
import aiohttp
import datetime
from supabase import create_client, Client

KST = pytz.timezone("Asia/Seoul")

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_IDS = [int(x) for x in os.getenv("TELEGRAM_CHAT_ID", "").split(",")]

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

async def send_telegram_message(message: str):
    async with aiohttp.ClientSession() as session:
        for chat_id in TELEGRAM_CHAT_IDS:
            try:
                url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
                payload = {"chat_id": chat_id, "text": message}
                async with session.post(url, data=payload) as response:
                    resp_json = await response.json()
                    print("[텔레그램 응답]", resp_json)
            except Exception as e:
                print("[텔레그램 전송 오류]", str(e))

async def insert_to_supabase(message: str):
    try:
        now = datetime.datetime.now(KST).isoformat()
        data = {"content": message, "created_at": now}
        result = supabase.table("messages").insert(data).execute()
        print("[DB 저장 결과]", result)
    except Exception as e:
        print("[DB 저장 실패]", str(e))

async def main():
    now = datetime.datetime.now(KST).strftime("%Y-%m-%d %H:%M:%S")
    message = (
        "[추천코인1]\n"
        "- 코인명: 카이토 (KAITO)\n"
        "- 현재가: 3,043원\n"
        "- 매수 추천가: 3,037 ~ 3,043원\n"
        "- 목표 매도가: 3,057원\n"
        "- 예상 수익률: 약 5%\n"
        "- 예상 소요 시간: 10분 이내\n"
        "- 추천 이유: 체결량 급증 + 매수 강세 포착\n"
        "[선행급등포착]\n\n"
        f"📊 {now} 기준"
    )
    print("[실전코드 실행 시작 - 전체 코인 대상]")
    await send_telegram_message(message)
    await insert_to_supabase(message)

if __name__ == "__main__":
    asyncio.run(main())
