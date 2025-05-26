from fastapi import FastAPI
import asyncio
import json
import websockets
import requests
import time
from datetime import datetime, timedelta
import os
import threading

print("🚀 단타 실전포착 전략 시스템 시작")

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_IDS = os.getenv("CHAT_IDS", "").replace("[", "").replace("]", "").replace('"', '').split(",")

coin_meta = {}
base_prices = {}
volume_window = {}
strength_window = {}
last_sent = {}

EXCLUDED_COINS = {"KRW-BTC", "KRW-ETH", "KRW-XRP", "KRW-DOGE"}

def send_telegram_message(msg):
    for chat_id in CHAT_IDS:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {"chat_id": chat_id, "text": msg, "parse_mode": "Markdown"}
        try:
            res = requests.post(url, json=payload)
            print("📤 텔레그램 전송:", res.status_code, res.text)
        except Exception as e:
            print("❌ 전송 실패:", e)

def fetch_market_codes():
    try:
        url = "https://api.upbit.com/v1/market/all?isDetails=true"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        markets = response.json()
        for market in markets:
            if market["market"].startswith("KRW-") and market["market"] not in EXCLUDED_COINS:
                code = market["market"]
                coin_meta[code] = {
                    "english_name": code.replace("KRW-", ""),
                    "korean_name": market["korean_name"]
                }
        print("✅ 종목 메타 수집 완료:", len(coin_meta), "종목")
    except Exception as e:
        print("❌ 메타 수집 실패:", e)

async def handle_socket():
    uri = "wss://api.upbit.com/websocket/v1"
    codes = list(coin_meta.keys())
    payload = [{"ticket": "live-trade"}, {"type": "ticker", "codes": codes}]
    os.makedirs("logs", exist_ok=True)
    today_str = (datetime.utcnow() + timedelta(hours=9)).strftime("%Y-%m-%d")
    log_path = f"logs/{today_str}.csv"

    async with websockets.connect(uri) as ws:
        await ws.send(json.dumps(payload))

        while True:
            msg = await ws.recv()
            data = json.loads(msg)
            market = data["code"]
            price = data["trade_price"]
            acc_volume = data["acc_trade_price_24h"]
            bid = data.get("acc_bid_volume", 1)
            ask = data.get("acc_ask_volume", 1)
            strength = ask / max(bid, 1) * 100
            now = time.time()

            if market not in base_prices:
                base_prices[market] = price
                volume_window[market] = []
                strength_window[market] = []

            rate = ((price - base_prices[market]) / base_prices[market]) * 100

            volume_window[market].append((now, acc_volume))
            volume_window[market] = [v for v in volume_window[market] if now - v[0] <= 30]
            volume_diff = volume_window[market][-1][1] - volume_window[market][0][1] if len(volume_window[market]) >= 2 else 0

            strength_window[market].append((now, strength))
            strength_window[market] = [s for s in strength_window[market] if now - s[0] <= 30]
            strength_diff = strength_window[market][-1][1] - strength_window[market][0][1] if len(strength_window[market]) >= 2 else 0

            if acc_volume > 1e8 or strength > 100:
                kst_now = datetime.utcnow() + timedelta(hours=9)
                with open(log_path, "a", encoding="utf-8") as f:
                    f.write(f"{kst_now.isoformat()},{market},{price},{acc_volume},{strength:.2f},{rate:.2f}\n")

            if (
                volume_diff >= 0.7e8 and
                strength_diff >= 20 and
                0.3 <= rate <= 4.5 and
                (market not in last_sent or now - last_sent[market] > 600)
            ):
                names = coin_meta[market]
                msg = f"[실전포착] {names['english_name']} ({names['korean_name']})\n" + \
                      f"- 현재가: {int(price):,}원 (+{rate:.2f}%)\n" + \
                      f"- 체결강도 변화: {strength_diff:.1f}%\n" + \
                      f"- 거래대금 증가: {volume_diff / 1e8:.2f}억 (30초 기준)\n" + \
                      f"- 판단: 상승 조짐 감지. 진입 여부 판단 요망."
                print("📡 조건 만족 → 메시지 전송")
                send_telegram_message(msg)
                last_sent[market] = now

def start_background_task():
    fetch_market_codes()
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(handle_socket())

app = FastAPI()

@app.on_event("startup")
def startup_event():
    threading.Thread(target=start_background_task).start()

@app.get("/")
def root():
    return {"status": "OK", "message": "실전 급등 포착 서버 작동 중 ✅"}
