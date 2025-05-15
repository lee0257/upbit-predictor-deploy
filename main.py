
import asyncio
import websockets
import json
import requests
from datetime import datetime, timedelta
import time

SUPABASE_URL = "https://sjmdhxnvqnudjgqabsgd.supabase.co"
SUPABASE_API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InNqbWRoeG52cW51ZGpncXFic2dkIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDcyODA2MTQsImV4cCI6MjA2Mjg1NjYxNH0.f8dqoeYLlAg96oImoc9rUa4gVZR9qvWdDBZdhrHZC64"
TELEGRAM_TOKEN = "6385123522:AAG0qdyaPOv-Q_7d9Y3A3POyTSZKlvx9XZs"
TELEGRAM_IDS = [1901931119, 5790931119]

HEADERS = {
    "apikey": SUPABASE_API_KEY,
    "Authorization": f"Bearer {SUPABASE_API_KEY}",
    "Content-Type": "application/json"
}

last_sent = {}
recent_volume = {}

async def fetch_all_krw_symbols():
    url = "https://api.upbit.com/v1/market/all"
    res = requests.get(url)
    markets = res.json()
    return [m['market'] for m in markets if m['market'].startswith('KRW-')]

async def send_telegram_alert(symbol, price, reason):
    now = datetime.utcnow()
    if symbol in last_sent and now - last_sent[symbol] < timedelta(minutes=30):
        return
    last_sent[symbol] = now

    buy_min = int(price * 0.995)
    buy_max = int(price * 1.005)
    target = int(price * 1.03)

    msg = f"""
[급등포착]
- 코인명: {symbol}
- 현재가: {price:,}원
- 매수 추천가: {buy_min:,} ~ {buy_max:,}원
- 목표 매도가: {target:,}원
- 예상 수익률: +3%
- 예상 소요 시간: 10분
- 추천 이유: {reason}
"""
    for chat_id in TELEGRAM_IDS:
        requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", data={
            "chat_id": chat_id,
            "text": msg
        })

async def save_to_supabase(table, data):
    url = f"{SUPABASE_URL}/rest/v1/{table}"
    for _ in range(3):
        try:
            res = requests.post(url, headers=HEADERS, json=[data], timeout=3)
            if res.status_code < 300:
                return
            else:
                print(f"[ERROR] Supabase write error: {res.status_code} - {res.text}")
        except requests.exceptions.RequestException as e:
            print(f"[ERROR] Supabase connection retrying in {table}: {e}")
            await asyncio.sleep(2)

async def handle_message(message):
    try:
        data = json.loads(message)
        code = data['cd']
        price = int(data['tp'])
        vol = float(data['tv'])
        side = data.get('ab', '')
        now = datetime.utcnow()

        if data['ty'] == 'ticker':
            await save_to_supabase("realtime_quotes", {
                "code": code,
                "price": price,
                "volume": vol,
                "timestamp": now.isoformat()
            })

            if code not in recent_volume:
                recent_volume[code] = []
            recent_volume[code].append((now, vol))
            recent_volume[code] = [(t, v) for (t, v) in recent_volume[code] if (now - t).seconds <= 20]

            vol_10s = sum(v for (t, v) in recent_volume[code] if (now - t).seconds <= 10)
            vol_prev = sum(v for (t, v) in recent_volume[code] if 10 < (now - t).seconds <= 20)

            if vol_prev > 0 and vol_10s / vol_prev > 5 and vol_10s > 3e8:
                await send_telegram_alert(code, price, "10초 체결량 5배 급증 + 매수세 유입")

        elif data['ty'] == 'trade':
            await save_to_supabase("realtime_ticks", {
                "code": code,
                "price": price,
                "volume": vol,
                "side": side,
                "timestamp": now.isoformat()
            })
    except Exception as e:
        print(f"[ERROR] handle_message failed: {e}")

async def main():
    while True:
        try:
            uri = "wss://api.upbit.com/websocket/v1"
            codes = await fetch_all_krw_symbols()

            subscribe_data = [
                {"ticket": "realtime-krw-all"},
                {"type": "ticker", "codes": codes},
                {"type": "trade", "codes": codes},
                {"format": "SIMPLE"}
            ]

            async with websockets.connect(uri) as websocket:
                await websocket.send(json.dumps(subscribe_data))
                print("[INFO] WebSocket connected and subscribed to all KRW markets.")

                while True:
                    message = await websocket.recv()
                    await handle_message(message)

        except Exception as e:
            print(f"[ERROR] main loop crashed, retrying: {e}")
            await asyncio.sleep(5)

if __name__ == "__main__":
    asyncio.run(main())
