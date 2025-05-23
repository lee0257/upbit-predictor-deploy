import asyncio
import websockets
import json
import os
import requests
from datetime import datetime, timedelta

# === 🔐 환경변수 설정 ===
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# === ✉️ 텔레그램 전송 ===
def send_telegram_message(message: str):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    try:
        res = requests.post(url, json=payload, timeout=10)
        print("[텔레그램 전송]", res.status_code, res.text)
    except Exception as e:
        print("[오류] 텔레그램 전송 실패:", e)

# === 📡 업비트 WebSocket 실시간 감시 ===
async def upbit_ws():
    uri = "wss://api.upbit.com/websocket/v1"
    tracked_coins = ["KRW-SUI", "KRW-ARB", "KRW-HIFI", "KRW-SAND", "KRW-STRK"]
    subscribe_data = [
        {"ticket": "coin_alert"},
        {"type": "trade", "codes": tracked_coins, "isOnlyRealtime": True}
    ]

    recent_trades = {code: [] for code in tracked_coins}
    last_alert_time = {code: datetime.min for code in tracked_coins}

    async with websockets.connect(uri) as ws:
        await ws.send(json.dumps(subscribe_data))
        print("[연결됨] 업비트 실시간 감시 중")

        while True:
            try:
                data = await ws.recv()
                trade = json.loads(data)

                code = trade.get("code")
                trade_volume = float(trade.get("trade_volume", 0))
                trade_price = int(trade.get("trade_price", 0))
                timestamp = datetime.fromtimestamp(trade["timestamp"] / 1000)

                if not code or trade_volume == 0:
                    continue

                recent_trades[code].append((timestamp, trade_volume))
                recent_trades[code] = [t for t in recent_trades[code] if t[0] > datetime.now() - timedelta(seconds=10)]

                sum_volume = sum(v for _, v in recent_trades[code])

                # 조건: 10초간 체결량 급증 + 중복 알림 방지
                if sum_volume > 50 and datetime.now() - last_alert_time[code] > timedelta(minutes=30):
                    coin_name = code.replace("KRW-", "")
                    message = (
                        f"[추천코인1]\n"
                        f"- 코인명: {coin_name} ({code})\n"
                        f"- 현재가: {trade_price:,}원\n"
                        f"- 매수 추천가: {trade_price-1:,} ~ {trade_price+2:,}원\n"
                        f"- 목표 매도가: {int(trade_price * 1.03):,}원\n"
                        f"- 예상 수익률: 3% 이상\n"
                        f"- 예상 소요 시간: 10~30분\n"
                        f"- 추천 이유: 체결량 급증 + 매수 강세 포착\n"
                        f"[선행급등포착]"
                    )
                    send_telegram_message(message)
                    last_alert_time[code] = datetime.now()

            except Exception as e:
                print("[WebSocket 오류]", e)
                await asyncio.sleep(5)

# === 🚀 실행 ===
if __name__ == "__main__":
    asyncio.run(upbit_ws())
