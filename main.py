import os
import json
import time
import threading
from datetime import datetime, timedelta
from collections import deque, defaultdict

import requests
import websocket
from flask import Flask

app = Flask(__name__)

# Supabase and Telegram 환경 변수
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# 알림 중복 방지 설정
ALERT_INTERVAL = 60 * 30
last_alert_times = {}

# 한글 코인명 매핑 (필요 시 확장)
KOR_NAME_MAP = {
    "KRW-SUI": "수이",
    "KRW-ARB": "아비트럼",
    "KRW-HIFI": "하이파이",
    "KRW-STRK": "스트라이크"
}

# 실시간 거래 체결 데이터 저장 (최근 3분)
trade_data = defaultdict(lambda: deque())

# Upbit WebSocket 설정
WS_URL = "wss://api.upbit.com/websocket/v1"


def get_kor_name(market):
    return KOR_NAME_MAP.get(market, "")


def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": text})


def save_to_supabase(message):
    headers = {
        "apikey": SUPABASE_ANON_KEY,
        "Authorization": f"Bearer {SUPABASE_ANON_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation"
    }
    requests.post(f"{SUPABASE_URL}/rest/v1/messages", headers=headers, json={"content": message})


def should_alert(market, category):
    now = time.time()
    key = f"{market}_{category}"
    if key not in last_alert_times or now - last_alert_times[key] > ALERT_INTERVAL:
        last_alert_times[key] = now
        return True
    return False


def fetch_krw_markets():
    resp = requests.get("https://api.upbit.com/v1/market")
    return [m["market"] for m in resp.json() if m["market"].startswith("KRW-")]


def on_open(ws):
    markets = fetch_krw_markets()
    subscribe = [{"ticket": "ticker"}, {"type": "trade", "codes": markets}, {"format": "SIMPLE"}]
    ws.send(json.dumps(subscribe))


def on_message(ws, message):
    msg = json.loads(message)
    # SIMPLE format: ["trade", market, timestamp, price, side, volume]
    _, market, timestamp, price, side, volume = msg
    now = datetime.now()
    trade_data[market].append((now, price, side, volume))
    cutoff = now - timedelta(minutes=3)
    dq = trade_data[market]
    while dq and dq[0][0] < cutoff:
        dq.popleft()


def start_ws():
    ws = websocket.WebSocketApp(WS_URL, on_open=on_open, on_message=on_message)
    ws.run_forever()


def analyze_and_alert():
    while True:
        now = datetime.now()
        for market, dq in trade_data.items():
            if not dq:
                continue
            # 최근 3분 데이터
            data = list(dq)
            prices = [p for _, p, _, _ in data]
            volumes = [v for _, _, _, v in data]
            sides = [s for _, _, s, _ in data]

            # 1) 체결량 증가율 (최근 10초 vs 이전 1분)
            t10 = [v for t, _, _, v in data if t > now - timedelta(seconds=10)]
            t60 = [v for t, _, _, v in data if now - timedelta(seconds=70) < t <= now - timedelta(seconds=10)]
            vol_ratio = (sum(t10) / (sum(t60)/6)) if t60 else 0

            # 2) 매수강도 (매수체결 비율)
            buy_vol = sum(v for t, _, s, v in data if s == 'BID')
            total_vol = sum(volumes)
            buy_ratio = buy_vol / total_vol if total_vol else 0

            # 3) 고점 돌파 시도
            high3 = max(prices)
            curr_price = prices[-1]
            is_breaking = curr_price >= high3 * 0.995

            # 4) 변동성 압축 후 확장
            highs = prices[-6:]  # 최근 1분
            lows = prices[-6:]
            band1 = max(highs) - min(lows)
            band3 = max(prices) - min(prices)
            volatility = 'expanding' if band1 > band3 * 0.5 else 'stable'

            # 5) 예측값: 실시간 트렌드는 price 상승 기울기로 단순 판정
            slope = (prices[-1] - prices[0]) / prices[0]
            prediction = 'UP' if slope > 0.001 else 'HOLD'

            # 포착 판단
            conds = [vol_ratio > 2.0, buy_ratio > 0.7, is_breaking,
                     volatility == 'expanding', prediction == 'UP']
            if sum(conds) >= 3 and should_alert(market, 'rise'):
                kor = get_kor_name(market)
                msg = (
                    f"[추천코인1]\n"
                    f"- 코인명: {market.replace('KRW-','')} ({kor})\n"
                    f"- 현재가: {curr_price:,.0f}원\n"
                    f"- 매수 추천가: {curr_price:,.0f} ~ {curr_price*1.01:,.0f}원\n"
                    f"- 목표 매도가: {curr_price*1.03:,.0f}원\n"
                    f"- 예상 수익률: 3% 이상\n"
                    f"- 예상 소요 시간: 10~30분\n"
                    f"- 추천 이유: 체결량 증가율 {vol_ratio:.2f}배 + 매수강도 {buy_ratio:.2f}\n"
                    f"[선행급등포착]\n"
                    f"https://upbit.com/exchange?code=CRIX.UPBIT.KRW-{market.replace('KRW-','')}"
                )
                send_telegram_message(msg)
                save_to_supabase(msg)
        time.sleep(5)

@app.route("/")
def home():
    return f"[Server Running] {datetime.now():%Y-%m-%d %H:%M:%S}"

if __name__ == "__main__":
    threading.Thread(target=start_ws, daemon=True).start()
    threading.Thread(target=analyze_and_alert, daemon=True).start()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
