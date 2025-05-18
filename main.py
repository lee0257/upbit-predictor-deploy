import asyncio
import websockets
import json
from datetime import datetime, timezone
import requests
from supabase import create_client

# Supabase 설정
SUPABASE_URL = "https://fqtlxtdlynrhjurnjbrp.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZxdGx4dGRseW5yaGp1cm5qYnJwIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDgyMDUwOTEsImV4cCI6MjA2Mzc2MTA5MX0.GK1f0PPKjCL2hZpe17NF2HfwWeDdDY1a8TbHHbWxiGA"
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# 텔레그램 설정
TELEGRAM_TOKEN = "6449398377:AAEAjaHL8uU-3AvD59TYv99gGHQHzDQhNXU"
CHAT_IDS = [1901931119]

# 기준값
VOLUME_SPIKE_THRESHOLD = 3.5
PRICE_MOVE_THRESHOLD = 0.008
TRADE_AMOUNT_MIN = 1200000000

prev_data = {}

# 메시지 생성 함수
def generate_message(coin_name, current_price, buy_range, target_price, profit_rate, estimated_time, reason, is_urgent=False):
    header = "[긴급추천]" if is_urgent else "[추천코인1]"
    message = (
        f"{header}\n"
        f"- 코인명: {coin_name}\n"
        f"- 현재가: {current_price}원\n"
        f"- 매수 추천가: {buy_range[0]} ~ {buy_range[1]}원\n"
        f"- 목표 매도가: {target_price}원\n"
        f"- 예상 수익률: {profit_rate}%\n"
        f"- 예상 소요 시간: {estimated_time}분\n"
        f"- 추천 이유: {reason}\n"
        f"[선행급등포착]\n"
        f"- 실시간 차트 보기: https://upbit.com/exchange?code=CRIX.UPBIT.{coin_name}\n"
    )
    return message

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

# 업비트 티커 목록 가져오기
def get_all_krw_tickers():
    try:
        response = requests.get("https://api.upbit.com/v1/market/all")
        tickers = response.json()
        return [t["market"] for t in tickers if t["market"].startswith("KRW-") and not t["market"].endswith("BTC")]
    except:
        return ["KRW-BTC"]

# 메인 함수
async def handle_socket():
    uri = "wss://api.upbit.com/websocket/v1"
    codes = get_all_krw_tickers()
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
                        message = generate_message(
                            coin_name=code,
                            current_price=trade_price,
                            buy_range=(int(trade_price * 0.98), int(trade_price * 1.01)),
                            target_price=int(trade_price * 1.08),
                            profit_rate=round(8.0, 1),
                            estimated_time=5,
                            reason="체결량 급증 + 매수 강세 포착",
                            is_urgent=True
                        )
                        send_telegram_message(message)
                        save_to_supabase({"code": code, "price": trade_price, "reason": "체결량+돌파", "timestamp": str(trade_time)})

                    prev_data[code] = {
                        "last_price": trade_price,
                        "last_volume": trade_volume,
                        "last_time": trade_time
                    }

        except Exception as e:
            print("에러 발생:", e)
            await asyncio.sleep(1)

if __name__ == "__main__":
    asyncio.run(handle_socket())
