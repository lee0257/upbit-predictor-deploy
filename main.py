import os
import requests
from datetime import datetime
from supabase import create_client, Client

# ✅ 환경변수 로딩
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_IDS = os.getenv("TELEGRAM_CHAT_IDS")  # 쉼표로 구분된 여러 ID 허용

print("[환경변수 디버깅]")
print("SUPABASE_URL:", SUPABASE_URL)
print("SUPABASE_KEY:", SUPABASE_KEY)

if not SUPABASE_URL or not SUPABASE_KEY:
    raise Exception("환경변수 SUPABASE_URL 또는 SUPABASE_KEY가 누락되었습니다.")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ✅ 메시지 생성 함수
def build_message(data):
    code = data.get("code", "")
    korean_name = data.get("korean_name", "")
    current_price = data.get("current_price", "")
    buy_price = data.get("buy_price", "")
    target_price = data.get("target_price", "")
    profit_rate = data.get("profit_rate", "")
    duration = data.get("duration", "")
    reason = data.get("reason", "체결량 급증 + 매수 강세 포착")

    code_suffix = code.replace("KRW-", "")
    upbit_url = f"https://upbit.com/exchange?code=CRIX.UPBIT.{code}"

    return (
        f"[추천코인1]\n"
        f"- 코인명: {code_suffix} ({korean_name})\n"
        f"- 현재가: {current_price}원\n"
        f"- 매수 추천가: {buy_price}원\n"
        f"- 목표 매도가: {target_price}원\n"
        f"- 예상 수익률: {profit_rate}%\n"
        f"- 예상 소요 시간: {duration}분\n"
        f"- 추천 이유: {reason}\n"
        f"[선행급등포착]\n"
        f"{upbit_url}"
    )

# ✅ 텔레그램 전송 함수
def send_telegram_message(message):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_IDS:
        print("[⚠️ 텔레그램 설정 누락]")
        return
    
    for chat_id in TELEGRAM_CHAT_IDS.split(","):
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {
            "chat_id": chat_id.strip(),
            "text": message
        }
        try:
            res = requests.post(url, json=payload)
            if res.status_code == 200:
                print("[텔레그램 메시지 전송 성공]")
            else:
                print("[❌ 텔레그램 메시지 전송 실패]", res.text)
        except Exception as e:
            print("[텔레그램 예외]", str(e))

# ✅ Supabase 기록 함수
def save_to_supabase(message):
    try:
        now = datetime.now().isoformat()
        response = supabase.table("messages").insert({"content": message, "timestamp": now}).execute()
        if response.data:
            print("[✅ Supabase 삽입 성공]")
        else:
            print("[❌ Supabase 응답 없음]")
    except Exception as e:
        print("[❌ Supabase 삽입 실패 - APIError]")
        print("에러 메시지:", str(e))

# ✅ 실전 데이터 예시 (자동 분석 결과로 대체 가능)
data = {
    "code": "KRW-NEO",
    "korean_name": "네오",
    "current_price": 14620,
    "buy_price": "14500 ~ 14620",
    "target_price": 15040,
    "profit_rate": 3.0,
    "duration": 3,
    "reason": "체결량 급증 + 매수 강세 포착"
}

message = build_message(data)
save_to_supabase(message)
send_telegram_message(message)
