import sys
import time
import requests
import datetime
import pytz
import asyncio
import aiohttp
from supabase import create_client, Client

print("[DEBUG] 실행 시작", flush=True)
print("Python 버전:", sys.version, flush=True)

SUPABASE_URL = "https://hqwyfqccghosrgynckhr.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzIiwicmVmIjoiaHF3eWZxY2NnaG9zcmd5bmNraHIiLCJyb2xlIjoiYW5vbiIsImlhdCI6MTc0ODI4MTI5NywiZXhwIjoyMDYzODM3Mjk3fQ.f2HGMZd2IgyN0Pb4iTkEflxFeI0af_8jAjz8W7zN6c8"
TELEGRAM_TOKEN = "6383142222:AAGgC5I1-F6sMArX9M4Tx8VtIHHr-hh1pHo"
TELEGRAM_IDS = [1901931119]

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
KST = pytz.timezone("Asia/Seoul")
symbol_map = {}

async def load_market_info():
    global symbol_map
    url = "https://api.upbit.com/v1/market/all"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as res:
            data = await res.json()
            symbol_map = {d['market']: d['korean_name'] for d in data if d['market'].startswith('KRW-')}
    print(f"[INFO] 마켓 불러오기 완료: {len(symbol_map)}개", flush=True)

def already_sent_recently(market):
    now = datetime.datetime.now(KST)
    thirty_min_ago = now - datetime.timedelta(minutes=30)
    try:
        res = supabase.table("messages").select("timestamp", "content").eq("type", "선행급등포착").execute()
        for r in res.data:
            if market in r["content"]:
                ts = datetime.datetime.fromisoformat(r['timestamp']).astimezone(KST)
                if ts > thirty_min_ago:
                    print(f"[중복차단] {market} 최근 전송됨 → 건너뜀", flush=True)
                    return True
    except Exception as e:
        print("[중복 확인 오류]", e, flush=True)
    return False

async def send_message(msg):
    for uid in TELEGRAM_IDS:
        try:
            requests.post(
                f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
                data={"chat_id": uid, "text": msg}
            )
        except Exception as e:
            print("[텔레그램 전송 오류]", e, flush=True)

async def notify_recommendation(market, price, reason):
    coin_name = market.replace("KRW-", "")
    korean_name = symbol_map.get(market, "")
    timestamp = datetime.datetime.now(KST).isoformat()

    buy_price_range = f"{int(price*0.99)} ~ {int(price*1.01)}"
    target_price = round(price * 1.03, 2)
    profit_rate = round((target_price - price) / price * 100, 2)
    expected_time = "3분"

    msg = f"[추천코인1]\n- 코인명: {coin_name} ({korean_name})\n- 현재가: {int(price)}원\n- 매수 추천가: {buy_price_range}원\n- 목표 매도가: {target_price}원\n- 예상 수익률: {profit_rate}%\n- 예상 소요 시간: {expected_time}\n- 추천 이유: {reason}\n[선행급등포착]"

    await send_message(msg)

    try:
        supabase.table("messages").insert({
            "content": msg,
            "type": "선행급등포착",
            "timestamp": timestamp
        }).execute()
        print(f"[전송완료] {market} 추천 메시지 전송됨", flush=True)
    except Exception as e:
        print("[DB 저장 실패]", e, flush=True)

async def send_alive_message():
    while True:
        now = datetime.datetime.now(KST).strftime("%Y-%m-%d %H:%M:%S")
        msg = f"✅ 서버 정상 작동 중입니다 ({now} 기준)"
        await send_message(msg)
        print(f"[상태메시지] {msg}", flush=True)
        await asyncio.sleep(7200)

async def send_test_message():
    msg = "✅ 텔레그램 연결 테스트 메시지입니다. 봇이 정상 작동 중입니다."
    await send_message(msg)
    print("[DEBUG] 텔레그램 테스트 메시지 전송 완료", flush=True)

async def main():
    print("[DEBUG] main() 진입", flush=True)
    await load_market_info()
    await send_test_message()
    asyncio.create_task(send_alive_message())

    # 조건 강제 추천용 더미 실행 (1회성)
    dummy_market = "KRW-XRP"
    dummy_price = 715
    if not already_sent_recently(dummy_market):
        await notify_recommendation(dummy_market, dummy_price, "강제 추천: 기능 확인용")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print("[FATAL ERROR]", e, flush=True)
