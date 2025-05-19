import os
import requests
import time
from flask import Flask
from datetime import datetime
from threading import Thread
from upbit_realtime_collector import get_realtime_data  # 사용자 정의 모듈로 가정

app = Flask(__name__)

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

ALERT_INTERVAL = 60 * 30  # 30분 중복 알림 차단
last_alert_times = {}


def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": text}
    requests.post(url, json=payload)


def save_to_supabase(message):
    headers = {
        "apikey": SUPABASE_ANON_KEY,
        "Authorization": f"Bearer {SUPABASE_ANON_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation"
    }
    payload = {"content": message}
    requests.post(f"{SUPABASE_URL}/rest/v1/messages", headers=headers, json=payload)


def should_alert(coin, category):
    now = time.time()
    key = f"{coin}_{category}"
    if key not in last_alert_times or now - last_alert_times[key] > ALERT_INTERVAL:
        last_alert_times[key] = now
        return True
    return False


def analyze_and_alert():
    while True:
        data = get_realtime_data()

        for coin in data:
            price = data[coin]['price']
            volume = data[coin]['volume']
            change = data[coin]['change']
            prediction = data[coin].get('prediction', None)
            pattern = data[coin].get('pattern', '')

            # 선행급등포착
            if prediction == 'UP' and volume > 100000000 and should_alert(coin, 'rise'):
                message = f"[추천코인1]\n- 코인명: {coin}\n- 현재가: {price:,}원\n- 매수 추천가: {price:,} ~ {price*1.01:,.0f}원\n- 목표 매도가: {price*1.03:,.0f}원\n- 예상 수익률: 3% 이상\n- 예상 소요 시간: 10~30분\n- 추천 이유: 체결량 급증 + 매수 강세 포착\n[선행급등포착]\nhttps://upbit.com/exchange?code=CRIX.UPBIT.KRW-{coin}"
                send_telegram_message(message)
                save_to_supabase(message)

            # 급락감지
            elif change <= -3.0 and volume > 80000000 and should_alert(coin, 'drop'):
                message = f"[급락감지]\n- 코인명: {coin}\n- 현재가: {price:,}원\n- 3% 이상 단기 급락 발생\n- 매도세 급증 가능성 존재\nhttps://upbit.com/exchange?code=CRIX.UPBIT.KRW-{coin}"
                send_telegram_message(message)
                save_to_supabase(message)

            # 바닥다지기 패턴
            elif pattern == 'bottoming' and should_alert(coin, 'bottom'):
                message = f"[바닥다지기]\n- 코인명: {coin}\n- 현재가: {price:,}원\n- 저점 횡보 + 거래량 감소\n- 반등 가능성 포착\nhttps://upbit.com/exchange?code=CRIX.UPBIT.KRW-{coin}"
                send_telegram_message(message)
                save_to_supabase(message)

            # 세력포착
            elif pattern == 'whale_buy' and should_alert(coin, 'whale'):
                message = f"[세력포착]\n- 코인명: {coin}\n- 현재가: {price:,}원\n- 반복 매수 포착\n- 대량 자금 유입 징후\nhttps://upbit.com/exchange?code=CRIX.UPBIT.KRW-{coin}"
                send_telegram_message(message)
                save_to_supabase(message)

        time.sleep(10)


@app.route("/")
def home():
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return f"[Server Running] {now}"


if __name__ == "__main__":
    Thread(target=analyze_and_alert).start()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
