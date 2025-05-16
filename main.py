# ✅ 업비트 실시간 급등/스윙/세력 선행포착 자동화 전체코드 (Supabase + Telegram 연동)

import asyncio
import websockets
import json
from datetime import datetime, timezone
import requests
import os
from supabase import create_client

# ✅ 환경변수 또는 직접 입력
SUPABASE_URL = "https://wiwdiwsjfzrilwhiexzi.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Indpd2Rpd3NqZnpyaWx3aWV4emkiLCJyb2xlIjoiYW5vbiIsImlhdCI6MTc0Nzk1MjIwNiwiZXhwIjoyMDYzNTA4MjA2fQ.iP4S6ckz7iOV8z9mbDCuZtIJccD6tdc8F5CW3z0y7Lo"
TELEGRAM_TOKEN = "6501322010:AAE..."  # 예시, 실제 토큰으로 교체
TELEGRAM_CHAT_IDS = ["1901931119"]  # 친구 ID 제거됨

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# ✅ 실시간 WebSocket 요청 메시지
subscribe_fmt = [{
    "ticket": "test",
    "type": "trade",
    "codes": ["KRW-BTC"],  # 처음에 KRW-BTC만 넣고 후에 전체 추가 예정
    "isOnlyRealtime": True
}]

# ✅ 업비트 전체 KRW마켓 티커 불러오기
def get_all_tickers():
    url = "https://api.upbit.com/v1/market/all"
    res = requests.get(url)
    return [item['market'] for item in res.json() if item['market'].startswith('KRW-')]

# ✅ 급등 조건 감지
last_prices = {}
async def handle_trade(msg):
    code = msg['code']
    price = msg['trade_price']
    vol = msg['trade_volume']
    timestamp = datetime.now(timezone.utc).isoformat()

    # 체결 강도 계산 (매수세 기반)
    if code not in last_prices:
        last_prices[code] = price
        return

    diff = price - last_prices[code]
    rate = diff / last_prices[code] * 100
    last_prices[code] = price

    # 🔥 급등 조건: 체결량 + 가격 상승률 (선행 감지)
    if rate > 0.8 and vol > 20000:
        text = f"[선행급등포착]\n- 코인명: {code}\n- 현재가: {price:,.0f}원\n- 조건: 체결량↑ + 가격급등 시도"
        print(text)
        send_telegram(text)
        insert_supabase(code, price, rate, vol, "급등")

# ✅ Supabase 저장
def insert_supabase(code, price, rate, vol, tag):
    try:
        data = {
            "code": code,
            "price": price,
            "rate": rate,
            "volume": vol,
            "tag": tag,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        supabase.table("messages").insert(data).execute()
        print("✅ Supabase 삽입 성공")
    except Exception as e:
        print("❌ Supabase 삽입 실패:", e)

# ✅ 텔레그램 전송
def send_telegram(text):
    for chat_id in TELEGRAM_CHAT_IDS:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {"chat_id": chat_id, "text": text}
        try:
            res = requests.post(url, json=payload)
            print(f"📨 [{chat_id}] 응답:", res.text)
        except Exception as e:
            print(f"❌ Telegram 전송 실패: {e}")

# ✅ 메인 실행
async def main():
    subscribe_fmt[0]['codes'] = get_all_tickers()
    uri = "wss://api.upbit.com/websocket/v1"
    while True:
        try:
            async with websockets.connect(uri) as websocket:
                await websocket.send(json.dumps(subscribe_fmt))
                while True:
                    data = await websocket.recv()
                    msg = json.loads(data)
                    await handle_trade(msg)
        except Exception as e:
            print("❌ WebSocket 연결 오류:", e)
            await asyncio.sleep(3)

if __name__ == '__main__':
    print("🚀 [main.py] Render 서버 실행 시작")
    asyncio.run(main())
