import time
import traceback
from datetime import datetime
import requests
from supabase import create_client

SERVER_NAME = "[업비트-선행포착]"
SUPABASE_URL = "https://gzqpbywussubofgbsydw.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
TELEGRAM_TOKEN = "6343590063:AAH-V0BrkjFDqNV3Im2DdEny_7L9_Km-0uI"
TELEGRAM_CHAT_IDS = [1901931119]

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def check_env_keys():
    errors = []
    if not SUPABASE_URL.startswith("https://"):
        errors.append("❌ Supabase URL 형식 오류")
    if not SUPABASE_KEY or len(SUPABASE_KEY) < 30:
        errors.append("❌ Supabase 키 누락 또는 형식 오류")
    if not TELEGRAM_TOKEN or not TELEGRAM_TOKEN.startswith("6"):
        errors.append("❌ 텔레그램 토큰 형식 오류")
    if not TELEGRAM_CHAT_IDS:
        errors.append("❌ 수신 대상(chat_id) 설정 안 됨")
    if errors:
        for err in errors:
            print(err)
        raise ValueError("⛔ 환경변수 설정 오류: 서버 실행 중단")

def log_error(message):
    print(f"[ERROR] {message}")
    try:
        with open("error_log.txt", "a") as f:
            f.write(f"{datetime.now()} - {message}\n")
    except:
        pass

def send_telegram(message):
    for chat_id in TELEGRAM_CHAT_IDS:
        try:
            url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
            res = requests.post(url, json={"chat_id": chat_id, "text": message})
            if res.status_code == 401:
                log_error("❌ 텔레그램 인증 오류 (토큰 문제)")
        except Exception as e:
            log_error(f"텔레그램 전송 실패 ({chat_id}): {e}")

def insert_message_to_db(message_dict):
    try:
        response = supabase.table("messages").insert(message_dict).execute()
        if response.status_code in [401, 403]:
            send_telegram("❌ Supabase 인증 오류 발생 (키 만료 또는 권한 부족)")
        elif not (200 <= response.status_code < 300):
            log_error(f"Supabase 삽입 실패: {response}")
    except Exception as e:
        log_error(f"Supabase 삽입 오류: {e}")

def send_status():
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    send_telegram(f"{SERVER_NAME} 서버 작동 중 ✅\n{now}")

def generate_recommendation(coin, name, price, buy_range, target, profit_rate, reason, link):
    return f"""\n[추천코인1]
- 코인명: {coin} ({name})
- 현재가: {price}원
- 매수 추천가: {buy_range}
- 목표 매도가: {target}원
- 예상 수익률: {profit_rate}%
- 예상 소요 시간: 10~20분
- 추천 이유: {reason}
[선행급등포착]
{link}
"""

def run_main_logic():
    try:
        coin_data = {
            "coin": "DEEP",
            "signal": "선행급등포착",
            "price": 258,
            "created_at": datetime.now().isoformat()
        }
        insert_message_to_db(coin_data)
        msg = generate_recommendation(
            coin="DEEP",
            name="딥북",
            price=258,
            buy_range="255 ~ 259원",
            target=278,
            profit_rate=7.8,
            reason="체결량 급증 + 매수세 유입",
            link="https://upbit.com/exchange?code=CRIX.UPBIT.KRW-DEEP"
        )
        send_telegram(msg)
    except Exception as e:
        tb = traceback.format_exc()
        log_error(f"run_main_logic 오류 발생: {e}\n{tb}")
        send_telegram(f"{SERVER_NAME} 메인 로직 오류 ⚠️\n{e}")

if __name__ == "__main__":
    try:
        check_env_keys()
        print(f"{SERVER_NAME} 서버 실행 중...")
        send_status()
        while True:
            try:
                run_main_logic()
            except Exception as e:
                tb = traceback.format_exc()
                log_error(f"전체 실행 오류: {e}\n{tb}")
                send_telegram(f"{SERVER_NAME} 전체 실행 오류 ⚠️\n{e}")
            time.sleep(30)
    except Exception as e:
        tb = traceback.format_exc()
        log_error(f"서버 시작 실패: {e}\n{tb}")
        send_telegram(f"{SERVER_NAME} 서버 시작 실패 ❌\n{e}")