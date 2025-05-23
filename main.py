import asyncio
import websockets
import json
import os
import requests
from datetime import datetime, timedelta

# === 🔐 환경변수 설정 ===
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_IDS = os.getenv("CHAT_IDS", "").split(",")

# === 📘 한글 코인명 매핑 ===
KOREAN_NAMES = {
    "KRW-SUI": "수이",
    "KRW-ARB": "아비트럼",
    "KRW-HIFI": "하이파이",
    "KRW-SAND": "샌드박스",
    "KRW-STRK": "스트라이크"
}

# === ✉️ 텔레그램 전송 ===
def send_telegram_message(message: str):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    for chat_id in CHAT_IDS:
        payload = {
            "chat_id": chat_id.strip(),
            "text": message,
            "parse_mode": "Markdown"
        }
        try:
            res = requests.post(url, json=payload, timeout=10)
            print("[텔레그램 전송]", res.status_code, res.text)
        except Exception as e:
            print("[오류] 텔레그램 전송 실패:", e)

# === 🔍 텔레그램 연결 확인 ===
def test_telegram_connectivity():
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getMe"
    try:
        res = requests.get(url, timeout=10)
        print("[텔레그램 연결 상태]", res.status_code, res.text)
    except Exception as e:
        print("[오류] 텔레그램 연결 테스트 실패:", e)

# === 📡 업비트 WebSocket 실시간 감시 ===
async def upbit_ws():
    uri = "wss://api.upbit.com/websocket/v1"
    tracked_coins = list(KOREAN_NAMES.keys())
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
                timestamp = datetime.fromtimestamp(trade["timestamp"] / 1000)

                if not code or trade_volume == 0:
                    continue

                recent_trades[code].append((timestamp, trade_volume))
                recent_trades[code] = [t for t in recent_trades[code] if t[0] > datetime.now() - timedelta(seconds=10)]

                sum_volume = sum(v for _, v in recent_trades[code])

                if sum_volume > 50 and datetime.now() - last_alert_time[code] > timedelta(minutes=30):
                    symbol = code.replace("KRW-", "")
                    kor_name = KOREAN_NAMES.get(code, "")
                    message = (
                        f"[급등포착]\n"
                        f"- 코인: {symbol} ({kor_name})\n"
                        f"- 조건: 체결량 급증 + 매수세 유입"
                    )
                    send_telegram_message(message)
                    last_alert_time[code] = datetime.now()

            except Exception as e:
                print("[WebSocket 오류]", e)
                await asyncio.sleep(5)

# === 🚀 실행 ===
if __name__ == "__main__":
    test_telegram_connectivity()
    send_telegram_message("🔔 텔레그램 연결되었습니다 (Render 실전 자동 포착 시스템 작동 중)")
    asyncio.run(upbit_ws())
