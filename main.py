import asyncio
import websockets
import json
import requests
from datetime import datetime, timedelta
import telegram
from supabase import create_client, Client
import pytz
import time

# 기본 설정
SUPABASE_URL = "https://gzqpbywussubofgbsydw.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
TELEGRAM_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"
TELEGRAM_CHAT_IDS = [1901931119]  # 친구 ID 제외됨
korea = pytz.timezone('Asia/Seoul')

# Telegram, Supabase 설정
bot = telegram.Bot(token=TELEGRAM_TOKEN)
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# 한글 코인명 매핑 (일부 예시, 전체는 코드에서 자동 수집 가능)
KOREAN_NAMES = {
    "KRW-SUI": "수이",
    "KRW-HIFI": "하이파이",
    "KRW-ORBS": "오브스",
    # ... 전체 종목 자동 매핑 필요
}

# 최근 전송 기록
last_sent = {}

# 중복 차단 로직
def is_duplicate(market, now):
    key = f"{market}"
    if key in last_sent and (now - last_sent[key]).total_seconds() < 1800:
        return True
    last_sent[key] = now
    return False

# 실시간 현재가 가져오기
def get_current_price(market):
    try:
        url = f"https://api.upbit.com/v1/ticker?markets={market}"
        res = requests.get(url)
        return res.json()[0]["trade_price"]
    except:
        return None

# Telegram + Supabase 메시지 전송
def send_alert(market, price, reason):
    now = datetime.now(korea)
    if is_duplicate(market, now):
        return

    name_kr = KOREAN_NAMES.get(market, market)
    current_price = get_current_price(market)
    if not current_price:
        return

    buy_price_min = int(current_price * 0.985)
    buy_price_max = int(current_price * 1.005)
    target_price = int(current_price * 1.03)
    return_rate = round((target_price - current_price) / current_price * 100, 2)

    msg = f"""[추천코인1]
- 코인명: {name_kr} ({market.split('-')[1]})
- 현재가: {current_price:,}원
- 매수 추천가: {buy_price_min:,} ~ {buy_price_max:,}원
- 목표 매도가: {target_price:,}원
- 예상 수익률: {return_rate}%
- 예상 소요 시간: 10~30분
- 추천 이유: {reason}
[선행급등포착]
https://upbit.com/exchange?code=CRIX.UPBIT.{market}"""

    for chat_id in TELEGRAM_CHAT_IDS:
        bot.send_message(chat_id=chat_id, text=msg)

    supabase.table("messages").insert({
        "market": market,
        "price": current_price,
        "message": msg,
        "timestamp": now.isoformat()
    }).execute()

# 체결 데이터 분석
async def handle_socket():
    url = "wss://api.upbit.com/websocket/v1"
    subscribe = [{"ticket": "test"},
                 {"type": "trade", "codes": ["KRW-BTC", "KRW-SUI", "KRW-HIFI", "KRW-ORBS"]},  # 전체 종목 적용 가능
                 {"format": "DEFAULT"}]

    async with websockets.connect(url) as ws:
        await ws.send(json.dumps(subscribe))
        volume_dict = {}

        while True:
            try:
                raw = await ws.recv()
                data = json.loads(raw)
                market = data["code"]
                price = data["trade_price"]
                volume = data["trade_volume"]
                timestamp = datetime.fromtimestamp(data["timestamp"] / 1000, tz=korea)

                # 체결량 누적
                if market not in volume_dict:
                    volume_dict[market] = []
                volume_dict[market].append((timestamp, volume))

                # 최근 30초 내 체결량 기준
                cutoff = timestamp - timedelta(seconds=30)
                volume_dict[market] = [v for v in volume_dict[market] if v[0] >= cutoff]
                total_volume = sum(v[1] for v in volume_dict[market])

                if total_volume > 20000:  # 포착 조건
                    send_alert(market, price, "체결량 급증 + 매수 강세 포착")

            except Exception as e:
                print("WebSocket 오류:", e)
                continue

# 상태 메시지 2시간마다
async def status_message():
    while True:
        now = datetime.now(korea).strftime("%Y-%m-%d %H:%M:%S")
        for chat_id in TELEGRAM_CHAT_IDS:
            bot.send_message(chat_id, f"[상태] 서버 작동 중 - {now}")
        await asyncio.sleep(7200)

# 실행
async def main():
    await asyncio.gather(handle_socket(), status_message())

if __name__ == "__main__":
    asyncio.run(main())
