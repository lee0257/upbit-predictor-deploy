import time
from datetime import datetime, timedelta
import requests
from supabase import create_client

SUPABASE_URL = "https://fqtlxtdlynrhjurnjbrp.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZxdGx4dGRseW5yaGp1cm5qYnJwIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDgyMDUwOTEsImV4cCI6MjA2Mzc2MTA5MX0.GK1f0PPKjCL2hZpe17NF2HfwWeDdDY1a8TbHHbWxiGA"
TELEGRAM_TOKEN = "6343590063:AAH-V0BrkjFDqNV3Im2DdEny_7L9_Km-0uI"
TELEGRAM_CHAT_IDS = [1901931119]
SERVER_NAME = "[업비트-선행포착-실전]"
last_signal_time = None
last_status_time = datetime.now() - timedelta(hours=2)
alerted_coins = set()

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def send_telegram(message):
    for chat_id in TELEGRAM_CHAT_IDS:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        try:
            res = requests.post(url, json={"chat_id": chat_id, "text": message})
            print(f"[텔레그램] {res.status_code}, {res.text}", flush=True)
        except Exception as e:
            print(f"[텔레그램 오류]: {e}", flush=True)

def insert_message_to_db(data):
    try:
        supabase.table("messages").insert(data).execute()
        print("[DB] 삽입 성공", flush=True)
    except Exception as e:
        print("[DB 오류]:", e, flush=True)

def condition_matched():
    # 여기에 실전 조건 넣으면 됨 (예: 체결량 급증 + 거래대금 상위)
    # 지금은 예시로 3분마다 조건 만족처럼 시뮬레이션
    global last_signal_time
    if last_signal_time is None or (datetime.now() - last_signal_time) > timedelta(minutes=3):
        last_signal_time = datetime.now()
        return True
    return False

def run_main_logic():
    if condition_matched():
        coin = "SNT"
        if coin in alerted_coins:
            return
        alerted_coins.add(coin)

        coin_data = {
            "coin": coin,
            "signal": "선행급등포착",
            "price": 41.55,
            "created_at": datetime.now().isoformat()
        }
        insert_message_to_db(coin_data)

        message = "[추천코인1]\n- 코인명: SNT (스테이터스네트워크토큰)\n- 현재가: 41.55원\n- 매수 추천가: 41.20 ~ 41.60원\n- 목표 매도가: 44.00원\n- 예상 수익률: 5.8%\n- 예상 소요 시간: 10~30분\n- 추천 이유: 체결량 급증 + 볼린저 상단 돌파\n[선행급등포착]\nhttps://upbit.com/exchange?code=CRIX.UPBIT.KRW-SNT"
        send_telegram(message)

if __name__ == "__main__":
    send_telegram(f"{SERVER_NAME} 서버 시작됨 ✅")
    print(f"{SERVER_NAME} 서버 시작됨", flush=True)
    while True:
        try:
            run_main_logic()

            if datetime.now() - last_status_time > timedelta(hours=2):
                send_telegram(f"{SERVER_NAME} 정상 작동 중입니다 🟢")
                last_status_time = datetime.now()
        except Exception as e:
            err = f"{SERVER_NAME} 오류 ⚠️\n{str(e)}"
            print(err, flush=True)
            send_telegram(err)
        time.sleep(5)