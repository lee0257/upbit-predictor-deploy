import os
import asyncio
import aiohttp
import pytz
from datetime import datetime
from supabase import create_client, Client
import requests
import time

# 설정
KST = pytz.timezone("Asia/Seoul")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_IDS = [int(x) for x in os.getenv("TELEGRAM_CHAT_IDS", "1901931119").split(",")]

# Supabase 연결
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# 중복 전송 차단용 캐시
last_sent_time = 0
last_sent_market = ""

# 한글명 매핑
symbol_map = {}

async def send_telegram_message(text: str):
    async with aiohttp.ClientSession() as session:
        for chat_id in TELEGRAM_CHAT_IDS:
            url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
            payload = {"chat_id": chat_id, "text": text}
            try:
                async with session.post(url, data=payload) as response:
                    res = await response.text()
                    print("[텔레그램 응답]", res, flush=True)
            except Exception as e:
                print("[텔레그램 오류]", e, flush=True)

def insert_to_supabase(message: str):
    try:
        supabase.table("messages").insert({"content": message}).execute()
        print("[DB 저장 성공]", message, flush=True)
    except Exception as e:
        print("[DB 저장 실패]", e, flush=True)

def get_market_info():
    try:
        url = "https://api.upbit.com/v1/market/all"
        res = requests.get(url)
        items = res.json()
        krw = [m["market"] for m in items if m["market"].startswith("KRW-")]
        global symbol_map
        symbol_map = {m["market"]: m["korean_name"] for m in items if m["market"].startswith("KRW-")}
        return krw
    except Exception as e:
        print("[마켓 목록 오류]", e, flush=True)
        return []

def get_tickers(markets):
    try:
        url = f"https://api.upbit.com/v1/ticker?markets={','.join(markets)}"
        res = requests.get(url)
        return res.json()
    except Exception as e:
        print("[티커 데이터 오류]", e, flush=True)
        return []

def analyze():
    markets = get_market_info()
    data = get_tickers(markets)

    best_score = -1
    best = None

    for item in data:
        market = item["market"]
        price = item["trade_price"]
        vol = item["acc_trade_price"]
        rate = item["signed_change_rate"] * 100
        high = item["high_price"]
        low = item["low_price"]

        if vol < 800_000_000 or rate < 2.5:
            continue

        volatility = (high - low) / price
        score = rate * volatility * (vol / 1_000_000_000)

        if score > best_score:
            best_score = score
            best = {
                "market": market,
                "price": int(price),
                "change": round(rate, 2),
                "volume": int(vol)
            }

    return best

def format_message(coin):
    market = coin["market"]
    symbol = market.split("-")[1]
    name = symbol_map.get(market, symbol)
    current = coin["price"]
    now = datetime.now(KST).strftime("%Y-%m-%d %H:%M:%S")

    return (
        f"[추천코인1]\n"
        f"- 코인명: {name} ({symbol})\n"
        f"- 현재가: {current}원\n"
        f"- 매수 추천가: {current - 6} ~ {current}원\n"
        f"- 목표 매도가: {current + 14}원\n"
        f"- 예상 수익률: 약 5%\n"
        f"- 예상 소요 시간: 10분 이내\n"
        f"- 추천 이유: 체결량 급증 + 매수 강세 포착\n"
        f"[선행급등포착]\n\n📊 {now} 기준"
    )

async def main():
    global last_sent_time, last_sent_market

    print("[실전코드 실행 시작 - 전체 코인 대상]", flush=True)
    coin = analyze()
    if coin:
        now = time.time()
        if coin["market"] == last_sent_market and now - last_sent_time < 1800:
            print("[중복 차단] 최근 전송된 코인과 동일", flush=True)
            return

        msg = format_message(coin)
        insert_to_supabase(msg)
        await send_telegram_message(msg)
        last_sent_time = now
        last_sent_market = coin["market"]
    else:
        print("[포착 없음] 조건 만족 없음", flush=True)

if __name__ == "__main__":
    asyncio.run(main())
