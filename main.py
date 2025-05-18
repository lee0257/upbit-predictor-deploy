import asyncio
import websockets
import json
from datetime import datetime, timezone
import requests
from supabase import create_client

# Supabase 연결 정보
SUPABASE_URL = "https://fqtlxtdlynrhjurnjbrp.supabase.co"
SUPABASE_KEY = "picm5qYnJtIwiwcm9sZSI6ImFub241LCJpYXQiOjE3NDc1NTE1MDEsImV4cCI6MjA2MzEyNzUwMX0.xIpJ4qkyv7hcEFzcesbSJRHeiBvsfFAjzZ3KrQBNWq"
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# 텔레그램 정보
TELEGRAM_TOKEN = "6449398377:AAEAjaHL8uU-3AvD59TYv99gGHQHzDQhNXU"
CHAT_IDS = [1901931119]  # 친구 ID 제거됨

# 기준 값
VOLUME_THRESHOLD = 3.5
PRICE_THRESHOLD = 0.008
TRADE_AMOUNT_MIN = 1200000000

# 이전 체결 정보 저장
prev_data = {}

# 텔레그램 알림 함수
def send_telegram_message(message):
    for chat_id in CHAT_IDS:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        data = {"chat_id": chat_id, "text": message}
        try:
            requests.post(url, data=data)
        except Exception as e:
            print("텔레그램 전송 오류:", e)

# Supabase 저장 함수
def save_to_supabase(item):
    try:
        supabase.table("messages").insert(item).execute()
        print("✅ Supabase 삽입 성공")
    except Exception as e:
        print("❌ Supabase 삽입 실패:", e)

# 포맷 메시지 생성
def build_message(code, price, reason):
    return f"[선행급등포착]\n- 코인명: {code}\n- 현재가: {int(price)}원\n- 포착 사유: {reason}\n- 예상 수익 가능성: 높음 (선행포착)"

# 코인 목록 가져오기
def get_all_krw_tickers():
    try:
        response = requests.get("https://api.upbit.com/v1/market/all")
        tickers = response.json()
        krw_tickers = [t["market"] for t in tickers if t["market"].startswith("KRW-")]
        return krw_tickers
    except:
        return ["KRW-BTC"]

# WebSocket 처리
async def handle_socket():
    uri = "wss://api.upbit.com/websocket/v1"
    codes = get_all_krw_tickers()
    subscribe_data = [{"ticket":"test"}, {"type":"trade","codes":codes}]

    while True:
        try:
            async with websockets.connect(uri) as websocket:
                await websocket.send(json.dumps(subscribe_data))
                while True:
                    raw_data = await websocket.recv()
                    data = json.loads(raw_data)

                    code = data.get("code")
                    price = data.get("trade_price")
                    volume = data.get("trade_volume")
                    trade_time = datetime.now(timezone.utc)
                    amount = price * volume

                    if code not in prev_data:
                        prev_data[code] = {
                            "price": price,
                            "volume": volume,
                            "time": trade_time
                        }
                        continue

                    time_diff = (trade_time - prev_data[code]["time"]).total_seconds()
                    if time_diff < 2:
                        continue

                    vol_ratio = volume / (prev_data[code]["volume"] + 1e-6)
                    price_diff = (price - prev_data[code]["price"]) / prev_data[code]["price"]

                    if (vol_ratio > VOLUME_THRESHOLD or price_diff > PRICE_THRESHOLD) and amount > TRADE_AMOUNT_MIN:
                        msg = build_message(code, price, "체결량 급증 + 가격 돌파")
                        send_telegram_message(msg)
                        save_to_supabase({
                            "code": code,
                            "price": price,
                            "reason": "체결량 + 돌파",
                            "timestamp": str(trade_time)
                        })

                    prev_data[code] = {
                        "price": price,
                        "volume": volume,
                        "time": trade_time
                    }

        except Exception as e:
            print("에러 발생:", e)
            await asyncio.sleep(1)

if __name__ == "__main__":
    asyncio.run(handle_socket())
