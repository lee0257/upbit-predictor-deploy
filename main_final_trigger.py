from fastapi import FastAPI, Request
import requests
from supabase import create_client
import os

# === 🔐 설정값 ===
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_IDS = os.getenv("CHAT_IDS", "").split(",")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# === 🧩 Supabase 클라이언트 초기화 ===
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# === 🚀 FastAPI 앱 시작 ===
app = FastAPI()

# === ✉️ 텔레그램 메시지 전송 함수 ===
def send_telegram_message(message: str):
    for chat_id in CHAT_IDS:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {"chat_id": chat_id, "text": message, "parse_mode": "Markdown"}
        try:
            response = requests.post(url, json=payload, timeout=10)
            print("📨 텔레그램 응답:", response.status_code, response.text)
        except Exception as e:
            print(f"[오류] 텔레그램 전송 실패: {e}")

# === ✅ 서버 루트 접속 시 무조건 메시지 전송 ===
@app.get("/")
def root():
    try:
        send_telegram_message("✅ 서버가 실행 중이며 텔레그램 연결도 정상입니다. (/ 접속)")
    except Exception as e:
        print(f"[오류] 루트 전송 실패: {e}")
    return {"status": "OK", "message": "서버 연결 정상 ✅"}

# === 💾 Supabase 저장 함수 ===
def insert_to_supabase(message: str):
    try:
        supabase.table("messages").insert({"content": message}).execute()
        print("✅ Supabase 저장 성공")
    except Exception as e:
        print(f"[오류] Supabase 저장 실패: {e}")

# === 📩 메시지 전송 API (1~3개 추천) ===
@app.post("/send-message")
async def send_message(request: Request):
    data = await request.json()
    coin_list = data.get("coin_list", [])[:3]
    sent_messages = []

    for coin_data in coin_list:
        if is_valid_coin(coin_data):
            coin_name = coin_data.get("name", "알 수 없음")
            price = coin_data.get("price", 0)

            message = (
                f"[추천코인]\n"
                f"- 코인명: {coin_name}\n"
                f"- 현재가: {price}원\n"
                f"- 매수 추천가: {int(price*0.99)} ~ {int(price*1.01)}원\n"
                f"- 목표 매도가: {int(price*1.03)}원\n"
                f"- 예상 수익률: +3%\n"
                f"- 예상 소요 시간: 10~180분\n"
                f"- 추천 이유: 체결량 급증 + 매수 강세 포착\n"
                f"[선행급등포착]"
            )

            send_telegram_message(message)
            insert_to_supabase(message)
            sent_messages.append(coin_name)

    if not sent_messages:
        return {"status": "ignored", "message": "⛔️ 조건 만족 코인 없음"}

    return {"status": "success", "sent": sent_messages}

# === 💡 조건 감지 로직 ===
def is_valid_coin(coin_data):
    try:
        return (
            coin_data["trade_amount"] >= 1000000000 and
            coin_data["volume_ratio"] >= 3 and
            coin_data["buy_ratio"] >= 70 and
            coin_data["price_change"] < 10
        )
    except:
        return False
