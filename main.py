import requests
import time
from datetime import datetime, timedelta
from flask import Flask
from supabase import create_client, Client
import telegram

app = Flask(__name__)

# ✅ Supabase 연동 정보
SUPABASE_URL = "https://gzqpbywussubofgbsydw.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imd6cXBieXd1c3N1Ym9mZ2JzeWR3Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDc1ODkzODIsImV4cCI6MjA2MzE2NTM4Mn0.jaMY_QSclIr50958NCpCv9CVt6Do50K_PHOvii0rArc"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ✅ Telegram 설정
TELEGRAM_TOKEN = "7287889681:AAGM2BXvqJSyzbCrF25hy_WzCL40Cute64A"
TELEGRAM_CHAT_ID = "1901931119"
bot = telegram.Bot(token=TELEGRAM_TOKEN)

# ✅ 한글 코인명 매핑용 전역 딕셔너리
KOR_NAME_MAP = {}

def update_kor_name_map():
    global KOR_NAME_MAP
    try:
        res = requests.get("https://api.upbit.com/v1/market/all").json()
        KOR_NAME_MAP = {
            item["market"]: item["korean_name"]
            for item in res if item["market"].startswith("KRW-")
        }
        print("✅ 한글 코인명 매핑 완료")
    except Exception as e:
        print("⚠️ 한글 코인명 매핑 실패:", e)

def get_current_time_kst():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def is_duplicate_message(message: str) -> bool:
    thirty_minutes_ago = (datetime.now() - timedelta(minutes=30)).isoformat()
    result = supabase.table("messages") \
        .select("*") \
        .gte("created_at", thirty_minutes_ago) \
        .eq("content", message) \
        .execute()
    return len(result.data) > 0

def save_message_to_supabase(message: str):
    if is_duplicate_message(message):
        print("⚠️ 중복 메시지 - 저장/전송 생략")
        return
    data = {
        "message": message,
        "content": message,
        "created_at": get_current_time_kst()
    }
    supabase.table("messages").insert(data).execute()
    print("✅ Supabase 저장 완료")

def send_telegram_message(message: str):
    bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
    print("✅ 텔레그램 전송 완료")

def build_coin_message(market: str, current_price: float, buy_range: tuple, target_price: float, expected_rate: float, minutes: int, reason: str):
    korean_name = KOR_NAME_MAP.get(market, "알 수 없음")
    message = f"""[추천코인1]
- 코인명: {market.replace("KRW-", "")} ({korean_name})
- 현재가: {int(current_price)}원
- 매수 추천가: {int(buy_range[0])} ~ {int(buy_range[1])}원
- 목표 매도가: {int(target_price)}원
- 예상 수익률: {expected_rate}%
- 예상 소요 시간: {minutes}분
- 추천 이유: {reason}
[선행급등포착]
https://upbit.com/exchange?code=CRIX.UPBIT.{market}
"""
    return message

def predict_and_alert():
    # 테스트용 예시 메시지
    market = "KRW-SAND"
    current_price = 516.0
    buy_range = (512, 518)
    target_price = 540.0
    expected_rate = 4.6
    minutes = 5
    reason = "체결량 급증 + 매수 강세 포착"

    message = build_coin_message(market, current_price, buy_range, target_price, expected_rate, minutes, reason)
    send_telegram_message(message)
    save_message_to_supabase(message)

@app.route("/")
def index():
    return "🔥 선행포착 서버 실행 중"

if __name__ == "__main__":
    update_kor_name_map()
    predict_and_alert()
    app.run(host="0.0.0.0", port=10000)
