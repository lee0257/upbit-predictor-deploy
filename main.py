import asyncio
import websockets
import json
from datetime import datetime, timezone
import requests
from supabase import create_client
import os

# 환경변수에서 설정값 읽기
SUPABASE_URL = os.getenv("SUPABASE_URL", "").strip()
SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY", "").strip()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "").strip()
CHAT_IDS = [int(os.getenv("TELEGRAM_CHAT_ID", "0"))]  # 여러 ID 지원 시 리스트 확장 가능

# Supabase 클라이언트 생성
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# 포착 기준 상수
VOLUME_SPIKE_THRESHOLD = 3.5   # 체결량 증가율 기준
PRICE_MOVE_THRESHOLD = 0.008   # 0.8% 돌파 시도 감지
TRADE_AMOUNT_MIN = 1200000000  # 거래대금 기준 (1,200백만 원)

# 체결 데이터 저장용
prev_data = {}

# 텔레그램 전송 함수
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

# 코인 포착 메시지 포맷
def build_message(code, price, reason):
    return (
        f"[선행급등포착]\n"
        f"- 코인명: {code}\n"
        f"- 현재가: {int(price)}원\n"
        f"- 포착 사유: {reason}\n"
        f"- 예상 수익 가능성: 높음 (선행포착)"
    )

# WebSocket 데이터 처리
async def handle_socket():
    uri = "wss://api.upbit.com/websocket/v1"
    codes = await get_all_krw_tickers()
    subscribe_data = [{"ticket": "test"}, {"type": "trade", "codes": codes}]

    while True:
        try:
            async with websockets.connect(uri) as websocket:
                await websocket.send(json.dumps(subscribe_data))
                while True:
                    raw_data = await websocket.recv()
                    data = json.loads(raw_data)

                    code = data.get("code")
                    trade_price = data.get("trade_price")
                    trade_volume = data.get("trade_volume")
                    trade_time = datetime.now(timezone.utc)

                    if code not in prev_data:
                        prev_data[code] = {
                            "last_price": trade_price,
                            "last_volume": trade_volume,
                            "last_time": trade_time
                        }
                        continue

                    time_diff = (trade_time - prev_data[code]["last_time"]).total_seconds()
                    if time_diff < 2:
                        continue

                    volume_ratio = trade_volume / (prev_data[code]["last_volume"] + 1e-6)
                    price_diff_ratio = (trade_price - prev_data[code]["last_price"]) / prev_data[code]["last_price"]

                    if volume_ratio > VOLUME_SPIKE_THRESHOLD or price_diff_ratio > PRICE_MOVE_THRESHOLD:
                        message = build_message(code, trade_price, "체결량 급증 + 가격 돌파 시도")
                        send_telegram_message(message)
                        save_to_supabase({
                            "code": code,
                            "price": trade_price,
                            "reason": "체결량 + 돌파",
                            "timestamp": str(trade_time)
                        })

                    prev_data[code] = {
                        "last_price": trade_price,
                        "last_volume": trade_volume,
                        "last_time": trade_time
                    }
        except Exception as e:
            print("에러 발생:", e)
            await asyncio.sleep(1)

# 업비트 KRW마켓 코인 리스트 불러오기
async def get_all_krw_tickers():
    try:
        response = requests.get("https://api.upbit.com/v1/market/all")
        tickers = response.json()
        krw_tickers = [t["market"] for t in tickers if t["market"].startswith("KRW-") and not t["market"].endswith("BTC")]
        return krw_tickers
    except:
        return ["KRW-BTC"]

# 실행
if __name__ == "__main__":
    asyncio.run(handle_socket())
