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

SUPABASE_URL = "https://gzqpbywussubofgbsydw.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imd6cXBieXd1c3N1Ym9mZ2JzeWR3Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDgyMzAwMDMsImV4cCI6MjA2Mzc4NjAwM30.rkE-N_mBlSYOYQnXUTuodRCfAl6ogfwl3q-j_1xguB8"
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

async def fetch_ticker(session, market):
    url = f"https://api.upbit.com/v1/ticker?markets={market}"
    async with session.get(url) as res:
        return await res.json()

def already_sent_recently(market):
    now = datetime.datetime.now(KST)
    thirty_min_ago = now - datetime.timedelta(minutes=30)
    res = supabase.table("messages").select("timestamp", "content").eq("type", "선행급등포착").execute()
    for r in res.data:
        if market in r["content"]:
            ts = datetime.datetime.fromisoformat(r['timestamp']).astimezone(KST)
            if ts > thirty_min_ago:
                print(f"[중복차단] {market} 최근 전송됨 → 건너뜀", flush=True)
                return True
    return False

async def notify_recommendation(market, price, reason):
    coin_name = market.replace("KRW-", "")
    korean_name = symbol_map.get(market, "")
    timestamp = datetime.datetime.now(KST).isoformat()

    buy_price_range = f"{int(price*0.99)} ~ {int(price*1.01)}"
    target_price = round(price * 1.03, 2)
    profit_rate = round((target_price - price) / price * 100, 2)
    expected_time = "3분"

    msg = f"[추천코인1]\n- 코인명: {coin_name} ({korean_name})\n- 현재가: {int(price)}원\n- 매수 추천가: {buy_price_range}원\n- 목표 매도가: {target_price}원\n- 예상 수익률: {profit_rate}%\n- 예상 소요 시간: {expected_time}\n- 추천 이유: {reason}\n[선행급등포착]"

    for uid in TELEGRAM_IDS:
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            data={"chat_id": uid, "text": msg}
        )

    supabase.table("messages").insert({
        "content": msg,
        "type": "선행급등포착",
        "timestamp": timestamp
    }).execute()
    print(f"[전송완료] {market} 추천 메시지 전송됨", flush=True)

async def send_alive_message():
    while True:
        now = datetime.datetime.now(KST).strftime("%Y-%m-%d %H:%M:%S")
        msg = f"✅ 서버 정상 작동 중입니다 ({now} 기준)"
        for uid in TELEGRAM_IDS:
            requests.post(
                f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
                data={"chat_id": uid, "text": msg}
            )
        print(f"[상태메시지] {msg}", flush=True)
        await asyncio.sleep(7200)

async def send_test_message():
    msg = "✅ 텔레그램 연결 테스트 메시지입니다. 봇이 정상 작동 중입니다."
    for uid in TELEGRAM_IDS:
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            data={"chat_id": uid, "text": msg}
        )
    print("[DEBUG] 텔레그램 테스트 메시지 전송 완료", flush=True)

async def main():
    print("[DEBUG] main() 진입", flush=True)
    await load_market_info()
    print("[DEBUG] load_market_info() 완료", flush=True)

    await send_test_message()  # ✅ 텔레그램 연결 확인용 메시지

    asyncio.create_task(send_alive_message())
    markets = list(symbol_map.keys())
    print(f"[DEBUG] 순회 시작. 전체 마켓 수: {len(markets)}", flush=True)

    while True:
        async with aiohttp.ClientSession() as session:
            try:
                for i in range(0, len(markets), 30):
                    batch = markets[i:i+30]
                    ticker_data = await asyncio.gather(*[fetch_ticker(session, m) for m in batch])
                    for res in ticker_data:
                        if not res or 'error' in res[0]:
                            continue
                        data = res[0]
                        market = data['market']
                        price = data['trade_price']
                        acc_volume = data['acc_trade_price_24h']
                        change_rate = data['signed_change_rate']

                        if acc_volume < 800_000_000:
                            continue
                        if already_sent_recently(market):
                            continue
                        if change_rate > 0.015:
                            await notify_recommendation(market, price, "체결량 급증 + 매수 강세 포착")
                await asyncio.sleep(20)
            except Exception as e:
                print("[루프 오류]", e, flush=True)
                await asyncio.sleep(30)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print("[FATAL ERROR]", e, flush=True)
