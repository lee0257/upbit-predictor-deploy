import asyncio
import websockets
import json
from datetime import datetime, timezone
import os
import requests
from supabase import create_client

# 📡 환경변수 또는 기본값 설정
SUPABASE_URL = os.getenv("SUPABASE_URL") or "https://cucqadflyerohqhwnver.supabase.co"
SUPABASE_KEY = os.getenv("SUPABASE_KEY") or "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImN1Y3FhZGZseWVyb2hxaHdudmVyIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDc3NDkzNDAsImV4cCI6MjA2MzI4NTM0MH0.8HPxuVJ4CJqRMCjHu0UWWBLHv3B9IxXnb6PncOCeJ6g"

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN") or "6520035957:AAGTXYK2KfUwXOMFgL-ytikgY3EKpKUe4UQ"
TELEGRAM_CHAT_IDS = os.getenv("TELEGRAM_CHAT_IDS") or "1901931119,친구ID"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# 📬 텔레그램 메시지 전송 함수
def send_telegram_message(message: str):
    for chat_id in TELEGRAM_CHAT_IDS.split(","):
        try:
            url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
            payload = {
                "chat_id": chat_id.strip(),
                "text": message,
                "parse_mode": "HTML"
            }
            requests.post(url, data=payload)
        except Exception as e:
            print(f"[❌ 텔레그램 전송 실패] {e}")

# 💾 Supabase 저장
async def save_to_supabase(symbol, trade_price, timestamp):
    try:
        data = {
            "symbol": symbol,
            "price": trade_price,
            "timestamp": timestamp
        }
        response = supabase.table("realtime_prices").insert(data).execute()
        print(f"[✅ 저장 성공] {symbol}: {trade_price}원 ({timestamp})")
    except Exception as e:
        print(f"[❌ 저장 실패] {symbol} | 오류: {e}")

# 🔄 Upbit WebSocket 수신 루프
async def upbit_websocket():
    uri = "wss://api.upbit.com/websocket/v1"
    symbols = ["KRW-BTC", "KRW-ETH", "KRW-XRP", "KRW-SOL", "KRW-DOGE"]
    subscribe_data = [{"ticket": "test"}] + [{"type": "trade", "codes": symbols}]

    async with websockets.connect(uri) as websocket:
        await websocket.send(json.dumps(subscribe_data))
        print("📡 Upbit WebSocket 수집기 시작")

        while True:
            try:
                message = await websocket.recv()
                data = json.loads(message)

                symbol = data.get("code")
                trade_price = data.get("trade_price")
                timestamp = datetime.fromtimestamp(data.get("timestamp") / 1000, tz=timezone.utc).isoformat()

                print(f"[📥 수신] {symbol}: {trade_price}원")

                await save_to_supabase(symbol, trade_price, timestamp)

                send_telegram_message(
                    f"📈 <b>{symbol}</b>\n가격: <b>{int(trade_price):,}원</b>\n시간: {timestamp}"
                )

            except Exception as e:
                print(f"[에러 발생] WebSocket 처리 오류: {e}")
                await asyncio.sleep(1)

# 🚀 메인 실행
if __name__ == "__main__":
    asyncio.run(upbit_websocket())
