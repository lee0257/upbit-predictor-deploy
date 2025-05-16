import asyncio
import websockets
import json
import requests
from datetime import datetime, timezone
import time
import os

from supabase import create_client

# ✅ 최신 Supabase 연결 정보
SUPABASE_URL = os.getenv("SUPABASE_URL") or "https://sjmdhxnvqnudjgqabsgd.supabase.co"
SUPABASE_API_KEY = os.getenv("SUPABASE_KEY") or "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InNqbWRoeG52cW51ZGpncXFic2dkIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDcyODA2MTQsImV4cCI6MjA2Mjg1NjYxNH0.f8dqoeYLlAg96oImoc9rUa4gVZR9qvWdDBZdhrHZC64"

supabase = create_client(SUPABASE_URL, SUPABASE_API_KEY)

async def upbit_websocket():
    uri = "wss://api.upbit.com/websocket/v1"
    async with websockets.connect(uri) as websocket:
        subscribe_fmt = [{"ticket": "test"}, {"type": "ticker", "codes": ["KRW-BTC"], "isOnlyRealtime": True}]
        await websocket.send(json.dumps(subscribe_fmt))

        while True:
            try:
                message = await websocket.recv()
                data = json.loads(message)

                code = data['code']
                trade_price = data['trade_price']
                timestamp = data['timestamp']
                now = datetime.now(timezone.utc)

                print(f"[{now}] {code}: {trade_price}원")

                # Supabase에 저장
                insert_data = {
                    "symbol": code,
                    "price": trade_price,
                    "timestamp": now.isoformat()
                }

                response = supabase.table("realtime_quotes").insert(insert_data).execute()
                print("✅ 저장 성공:", response)

            except Exception as e:
                print("[ERROR] 데이터 처리 실패:", e)
                time.sleep(1)

if __name__ == "__main__":
    print("📡 Upbit WebSocket 수집기 시작")
    asyncio.run(upbit_websocket())
