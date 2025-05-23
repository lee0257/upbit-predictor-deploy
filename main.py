import asyncio
import websockets
import json
import requests
from datetime import datetime, timedelta

TELEGRAM_TOKEN = "7287889681:AAHqKbipumgMmRQ8J4_Zu8Nlu_CYDnbCt0U"
CHAT_IDS = ["1901931119"]

# === 전체 업비트 KRW 마켓 코인 로드 ===
def load_krw_markets():
    url = "https://api.upbit.com/v1/market/all"
    try:
        res = requests.get(url, params={"isDetails": "true"})
        markets = res.json()
        krw_markets = {m['market']: m['korean_name'] for m in markets if m['market'].startswith("KRW-")}
        return krw_markets
    except Exception as e:
        print("[업비트 마켓 목록 오류]", e)
        return {}

# === 텔레그램 메시지 전송 ===
def send_telegram_message(message: str):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    for chat_id in CHAT_IDS:
        payload = {
            "chat_id": chat_id,
            "text": message,
            "parse_mode": "Markdown"
        }
        try:
            res = requests.post(url, json=payload, timeout=10)
            print("[텔레그램 전송]", res.status_code, res.text)
        except Exception as e:
            print("[오류] 텔레그램 전송 실패:", e)

# === 텔레그램 연결 확인 ===
def test_telegram_connectivity():
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getMe"
    print("[디버그] 요청 URL:", url)
    try:
        res = requests.get(url, timeout=10)
        print("[텔레그램 연결 상태]", res.status_code, res.text)
        if res.status_code != 200:
            raise Exception("Invalid response from Telegram API")
    except Exception as e:
        print("[오류] 텔레그램 연결 테스트 실패:", e)
        raise SystemExit("❌ 텔레그램 연결 실패로 시스템 종료")

# === 실시간 감시 ===
async def upbit_ws(krw_map):
    uri = "wss://api.upbit.com/websocket/v1"
    codes = list(krw_map.keys())
    subscribe_data = [
        {"ticket": "coin_alert"},
        {"type": "trade", "codes": codes, "isOnlyRealtime": True}
    ]

    recent_trades = {code: [] for code in codes}
    last_alert_time = {code: datetime.min for code in codes}

    async with websockets.connect(uri) as ws:
        await ws.send(json.dumps(subscribe_data))
        print("[연결됨] 업비트 전체 KRW 마켓 실시간 감시 중")

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
                    kor_name = krw_map.get(code, "")
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

# === 실행 ===
if __name__ == "__main__":
    test_telegram_connectivity()
    send_telegram_message("🔔 텔레그램 연결되었습니다 (실전 자동 포착 시스템 작동 중)")
    krw_map = load_krw_markets()
    asyncio.run(upbit_ws(krw_map))