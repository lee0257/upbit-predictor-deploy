import time
import requests
from datetime import datetime, timedelta
from supabase import create_client, Client
import threading

# --- Supabase 설정 ---
SUPABASE_URL = "https://ptifzaufskqkdleyfnwv.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InB0aWZ6YXVmc2txa2RsZXlmbnd2Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDU2MzMwMTYsImV4cCI6MjA2MTE4OTAxNn0.dOhcVi6m_xvJkP06Iv6NLZmw7m7fRmITN0jaFn2z0zE"
SUPABASE_TABLE_NAME = "messages"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# --- 텔레그램 설정 ---
TELEGRAM_TOKEN = "7287889681:AAHqKbipumgMmRQ8J4_Zu8Nlu_CYDnbCt0U"
TELEGRAM_CHAT_IDS = [1901931119]
SEND_HISTORY = {}

# --- 텔레그램 메시지 전송 ---
def send_telegram_message(text: str):
    for chat_id in TELEGRAM_CHAT_IDS:
        try:
            url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
            payload = {"chat_id": chat_id, "text": text}
            requests.post(url, data=payload)
        except Exception as e:
            print(f"[텔레그램 오류] {e}")

# --- Supabase 저장 ---
def send_to_supabase(data: dict):
    try:
        supabase.table(SUPABASE_TABLE_NAME).insert(data).execute()
        print("[Supabase 저장 성공]", data['coin_name'])
    except Exception as e:
        print(f"[Supabase 저장 실패] {e}")

# --- 메시지 포맷 ---
def build_message(data: dict) -> str:
    return f"""[추천코인1]
- 코인명: {data['coin_name']} ({data['korean_name']})
- 현재가: {data['current_price']}원
- 매수 추천가: {data['buy_range']}
- 목표 매도가: {data['target_price']}원
- 예상 수익률: {data['expected_profit']}%
- 예상 소요 시간: {data['expected_time']}분
- 추천 이유: {data['reason']}
[선행급등포착]
https://upbit.com/exchange?code=CRIX.UPBIT.KRW-{data['coin_name']}"""

# --- 중복 차단 ---
def is_recently_sent(key: str, minutes: int = 30):
    now = datetime.now()
    if key in SEND_HISTORY and now - SEND_HISTORY[key] < timedelta(minutes=minutes):
        return True
    SEND_HISTORY[key] = now
    return False

# --- 상태 메시지 2시간마다 전송 ---
def loop_heartbeat():
    while True:
        send_telegram_message("📡 연결되었습니다.")
        time.sleep(7200)  # 2시간 = 7200초

# --- 예시: 급등 포착 발생 시 실행될 본체 로직 ---
def trigger_alert():
    data = {
        "coin_name": "SUI",
        "korean_name": "슈이",
        "current_price": 902,
        "buy_range": "895 ~ 910",
        "target_price": 940,
        "expected_profit": 4.2,
        "expected_time": 12,
        "reason": "체결량 급증 + 매수 강세 포착",
        "alert_type": "선행급등포착",
        "created_at": datetime.now().isoformat()
    }

    key = f"{data['coin_name']}_{data['alert_type']}"
    if is_recently_sent(key):
        print("[중복 차단] 이미 전송됨:", key)
        return

    msg = build_message(data)
    send_telegram_message(msg)
    send_to_supabase(data)

# --- 메인 실행 ---
def main():
    print("[상태] 서버 실행 완료: 연결되었습니다.")
    send_telegram_message("📡 서버 실행 완료: Supabase 및 텔레그램 연결되었습니다.")

    # 2시간마다 상태 메시지 쓰레드 실행
    threading.Thread(target=loop_heartbeat, daemon=True).start()

    # 예시 트리거 (나중에 조건 포착 시점으로 대체)
    while True:
        now = datetime.now()
        if now.minute % 10 == 0 and now.second < 2:  # 예시로 10분마다 한 번 실행
            trigger_alert()
        time.sleep(1)

if __name__ == "__main__":
    main()
