from fastapi import FastAPI, Request
import requests
import os

# === 🔐 설정값 ===
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_IDS = os.getenv("CHAT_IDS", "").split(",")
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")

# === 🚀 FastAPI 앱 시작 ===
app = FastAPI()

# === ✉️ 텔레그램 메시지 전송 함수 ===
def send_telegram_message(message: str):
    for chat_id in CHAT_IDS:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": message,
            "parse_mode": "Markdown"
        }
        try:
            response = requests.post(url, json=payload, timeout=10)
            print("텔레그램 응답:", response.status_code, response.text)
        except Exception as e:
            print(f"[오류] 텔레그램 전송 실패: {e}")

# === ✉️ 슬랙 메시지 전송 함수 ===
def send_slack_message(message: str):
    try:
        response = requests.post(
            SLACK_WEBHOOK_URL,
            json={"text": message},
            timeout=10
        )
        print("슬랙 응답:", response.status_code, response.text)
    except Exception as e:
        print(f"[오류] 슬랙 전송 실패: {e}")

# === 🔁 POST: 수동추천 메시지 전송 엔드포인트 ===
@app.post("/send-message")
async def send_message(request: Request):
    data = await request.json()
    message = data.get("message", "")

    if not message:
        return {"status": "fail", "message": "❌ 메시지가 비어 있습니다"}

    send_telegram_message(message)
    send_slack_message(message)

    return {"status": "success", "message": "✅ 텔레그램 + 슬랙 전송 완료"}

# === 🟢 GET: 서버 연결 확인 라우트 ===
@app.get("/")
def root():
    return {"status": "OK", "message": "서버 연결되었습니다 ✅"}
