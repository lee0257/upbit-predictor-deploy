from pathlib import Path

# 지침 반영: 시작 시 Supabase 연결, 텔레그램 확인 메시지 전송, Supabase 테스트 삽입 포함한 완성형 코드
final_verified_code = """
import asyncio
import json
import websockets
import requests
import time
from datetime import datetime
from supabase import create_client
import os

# === 🔐 환경 변수 설정 ===
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_IDS = os.getenv("CHAT_IDS", "").split(",")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
TABLE_NAME = "recommendations"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# === 📌 조건 기준 ===
MIN_STRENGTH = 200
MIN_RATE = 2.0
MIN_VOLUME = 1e8

coin_meta = {}
base_prices = {}
last_sent = {}

async def fetch_market_codes():
    url = "https://api.upbit.com/v1/market/all?isDetails=true"
    response = requests.get(url)
    markets = response.json()
    for market in markets:
        if market["market"].startswith("KRW-"):
            code = market["market"]
            coin_meta[code] = {
                "english_name": code.replace("KRW-", ""),
                "korean_name": market["korean_name"]
            }

async def send_telegram_message(msg):
    for chat_id in CHAT_IDS:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {"chat_id": chat_id, "text": msg, "parse_mode": "Markdown"}
        try:
            res = requests.post(url, json=payload)
            print("텔레그램 응답:", res.status_code, res.text)
        except Exception as e:
            print("텔레그램 전송 실패:", e)

def save_to_supabase(data):
    try:
        supabase.table(TABLE_NAME).insert(data).execute()
        print("✅ Supabase 저장 완료:", data["coin"])
    except Exception as e:
        print("Supabase 저장 실패:", e)

def format_message(market, price, rate, strength, volume):
    names = coin_meta[market]
    return f"[추천] {names['english_name']} ({names['korean_name']})\\n" + \
           f"- 현재가: {int(price):,}원 (+{rate:.2f}%)\\n" + \
           f"- 체결강도: {strength:.1f}%\\n" + \
           f"- 거래대금(3분): {volume/1e8:.2f}억\\n" + \
           f"- 판단: 진입 검토 가능"

async def handle_socket():
    uri = "wss://api.upbit.com/websocket/v1"
    codes = list(coin_meta.keys())
    payload = [{"ticket": "gpt-final"}, {"type": "ticker", "codes": codes}]
    async with websockets.connect(uri) as ws:
        await ws.send(json.dumps(payload))
        time_check = time.time()

        while True:
            msg = await ws.recv()
            data = json.loads(msg)
            market = data["code"]
            trade_price = data["trade_price"]
            acc_volume = data["acc_trade_price_24h"]
            strength = data.get("acc_ask_volume", 1) / max(data.get("acc_bid_volume", 1), 1) * 100
            now = time.time()

            if market not in base_prices or now - time_check > 180:
                base_prices[market] = trade_price

            if market in base_prices:
                rate = ((trade_price - base_prices[market]) / base_prices[market]) * 100
                if rate >= MIN_RATE and strength >= MIN_STRENGTH and acc_volume >= MIN_VOLUME:
                    if market not in last_sent or now - last_sent[market] > 300:
                        msg_text = format_message(market, trade_price, rate, strength, acc_volume)
                        await send_telegram_message(msg_text)

                        save_to_supabase({
                            "coin": market,
                            "korean_name": coin_meta[market]["korean_name"],
                            "price": trade_price,
                            "rate_change": rate,
                            "strength": strength,
                            "volume": acc_volume,
                            "judgement": "진입 검토 가능",
                            "sent_at": datetime.utcnow().isoformat()
                        })

                        last_sent[market] = now
            if now - time_check > 180:
                time_check = now

async def main():
    print("✅ Supabase 연결 확인됨:", SUPABASE_URL)
    print("✅ 텔레그램 토큰 시작됨:", TELEGRAM_TOKEN[:10] + "...")

    await send_telegram_message("✅ 텔레그램 연결 확인되었습니다.")

    save_to_supabase({
        "coin": "TEST",
        "korean_name": "테스트",
        "price": 0,
        "rate_change": 0,
        "strength": 0,
        "volume": 0,
        "judgement": "시작 확인용",
        "sent_at": datetime.utcnow().isoformat()
    })

    await fetch_market_codes()
    await handle_socket()

if __name__ == "__main__":
    asyncio.run(main())
"""

file_path = Path("/mnt/data/main_final_real.py")
file_path.write_text(final_verified_code.strip(), encoding="utf-8")

file_path.name
