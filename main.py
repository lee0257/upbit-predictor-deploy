
from datetime import datetime, timedelta
import requests
import pytz
from supabase import create_client, Client
import time
import traceback

SUPABASE_URL = "https://gzqpbywussubofgbsydw.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
TELEGRAM_TOKEN = "7287889681:AAHqKbipumgMmRQ8J4_Zu8Nlu_CYDnbCt0U"
TELEGRAM_CHAT_IDS = ["1901931119"]
DB_TABLE = "messages"
SEND_INTERVAL_MINUTES = 30
LOOP_INTERVAL_SECONDS = 30

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
kst = pytz.timezone("Asia/Seoul")
last_sent_times = {}

def send_telegram_message(message: str):
    for chat_id in TELEGRAM_CHAT_IDS:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {"chat_id": chat_id, "text": message}
        try:
            requests.post(url, json=payload)
        except Exception as e:
            print("텔레그램 전송 오류:", e)

def log_error(message: str):
    now = datetime.now(kst).strftime("%Y-%m-%d %H:%M:%S")
    full_message = f"[에러 발생] {now}\n{message}"
    print(full_message)
    send_telegram_message(full_message)

def notify_system_status():
    now = datetime.now(kst).strftime("%Y-%m-%d %H:%M:%S")
    supabase_msg = "[시스템] ✅ Supabase에 연결되었습니다."
    telegram_msg = "[시스템] ✅ Telegram에 연결되었습니다."
    print(supabase_msg)
    print(telegram_msg)
    send_telegram_message(supabase_msg)
    send_telegram_message(telegram_msg)

def generate_recommendation():
    now = datetime.now(kst)
    recommendations = []

    example_coin = {
        "code": "DEEP",
        "name": "딥브레인체인",
        "price": 258.0,
        "buy_low": 254,
        "buy_high": 259,
        "target": 267,
        "profit": round((267 - 256.5) / 256.5 * 100, 2),
        "minutes": 12,
        "reason": "체결량 급증 + 매수 강세 포착"
    }

    if example_coin["code"] in last_sent_times:
        last_time = last_sent_times[example_coin["code"]]
        if now - last_time < timedelta(minutes=SEND_INTERVAL_MINUTES):
            return []

    last_sent_times[example_coin["code"]] = now

    recommendations.append(f"""[추천코인1]
- 코인명: {example_coin["code"]} ({example_coin["name"]})
- 현재가: {example_coin["price"]}원
- 매수 추천가: {example_coin["buy_low"]} ~ {example_coin["buy_high"]}원
- 목표 매도가: {example_coin["target"]}원
- 예상 수익률: {example_coin["profit"]}%
- 예상 소요 시간: {example_coin["minutes"]}분
- 추천 이유: {example_coin["reason"]}
[선행급등포착]
https://upbit.com/exchange?code=CRIX.UPBIT.{example_coin["code"]}""")

    return recommendations

def save_to_supabase(message: str):
    now = datetime.now(kst).isoformat()
    try:
        data = {"content": message, "timestamp": now}
        supabase.table(DB_TABLE).insert(data).execute()
    except Exception as e:
        log_error("Supabase 저장 오류:\n" + traceback.format_exc())

def main():
    try:
        notify_system_status()
        while True:
            try:
                messages = generate_recommendation()
                for msg in messages:
                    send_telegram_message(msg)
                    save_to_supabase(msg)
            except Exception as e:
                log_error(traceback.format_exc())
            time.sleep(LOOP_INTERVAL_SECONDS)
    except Exception as e:
        log_error("초기화 오류:\n" + traceback.format_exc())

main()
