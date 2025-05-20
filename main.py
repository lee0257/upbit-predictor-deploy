# upbit_predictor_realtime.py
import time
import requests
import datetime
import pytz
import asyncio
import aiohttp
from supabase import create_client, Client

SUPABASE_URL = "https://gzqpbywussubofgbsydw.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imd6cXBieXd1c3N1Ym9mZ2JzeWR3Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDgyMzAwMDMsImV4cCI6MjA2Mzc4NjAwM30.rkE-N_mBlSYOYQnXUTuodRCfAl6ogfwl3q-j_1xguB8"
TELEGRAM_TOKEN = "6383142222:AAGgC5I1-F6sMArX9M4Tx8VtIHHr-hh1pHo"
TELEGRAM_IDS = [1901931119]

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
KST = pytz.timezone("Asia/Seoul")

# 업비트 종목명 한글 매핑용
symbol_map = {}

async def load_market_info():
    global symbol_map
    url = "https://api.upbit.com/v1/market/all"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as res:
            data = await res.json()
            symbol_map = {d['market']: d['korean_name'] for d in data if d['market'].startswith('KRW-')}

async def fetch_ticker(session, market):
    url = f"https://api.upbit.com/v1/ticker?markets={market}"
    async with session.get(url) as res:
        return await res.json()

sent_cache = {}

async def notify_recommendation(market, price, reason):
    coin_name = market.replace("KRW-", "")
    korean_name = symbol_map.get(market, "")
    timestamp = datetime.datetime.now(KST).isoformat()

    buy_price_range = f"{int(price*0.99)} ~ {int(price*1.01)}"
    target_price = int(price * 1.03)
    expected_profit = "3% 이상"
    expected_time = "3분"

    msg = f"[추천코인1]\n- 코인명: {coin_name} ({korean_name})\n- 현재가: {int(price)}원\n- 매수 추천가: {buy_price_range}원\n- 목표 매도가: {target_price}원\n- 예상 수익률: {expected_profit}\n- 예상 소요 시간: {expected_time}\n- 추천 이유: {reason}\n[선행급등포착]"

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

async def main():
    await load_market_info()
    markets = list(symbol_map.keys())

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

                        if acc_volume < 800_000_000:
                            continue

                        now = datetime.datetime.now(KST)
                        minute = now.minute

                        if sent_cache.get(market) and (now - sent_cache[market]).seconds < 1800:
                            continue

                        change_rate = data['signed_change_rate']
                        if change_rate > 0.015:
                            sent_cache[market] = now
                            await notify_recommendation(market, price, "체결량 급증 + 매수 강세 포착")

                await asyncio.sleep(20)

            except Exception as e:
                print("[오류 발생]", e)
                await asyncio.sleep(30)

if __name__ == "__main__":
    asyncio.run(main())
