from fastapi import FastAPI, Request
import requests
import os

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "")
CHAT_IDS = os.getenv("CHAT_IDS", "")
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL", "")

app = FastAPI()

def send_telegram_message(message: str):
    if not TELEGRAM_TOKEN or not CHAT_IDS:
        print("[텔레그램 누락] 전송 생략")
        return
    for chat_id in CHAT_IDS.split(","):
        try:
            url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
            payload = {"chat_id": chat_id, "text": message, "parse_mode": "Markdown"}
            response = requests.post(url, json=payload, timeout=10)
            print("텔레그램 응답:", response.status_code)
        except Exception as e:
            print(f"[텔레그램 실패] {e}")

def send_slack_message(message: str):
    if not SLACK_WEBHOOK_URL:
        print("[슬랙 Webhook 누락] 전송 생략")
        return
    try:
        response = requests.post(SLACK_WEBHOOK_URL, json={"text": message}, timeout=10)
        print("슬랙 응답:", response.status_code)
    except Exception as e:
        print(f"[슬랙 실패] {e}")

@app.on_event("startup")
async def auto_message():
    send_telegram_message("🚀 서버 시작됨 - 자동 메시지 전송")
    send_slack_message("🚀 서버 시작됨 - 자동 메시지 전송")

@app.post("/send-message")
async def send_message(request: Request):
    try:
        data = await request.json()
        message = data.get("message", "")
        if not message:
            return {"status": "fail", "message": "❌ 메시지 없음"}
        send_telegram_message(message)
        send_slack_message(message)
        return {"status": "success", "message": "✅ 메시지 전송됨"}
    except Exception as e:
        return {"status": "error", "message": f"❌ 예외 발생: {e}"}

@app.get("/")
def root():
    return {"status": "OK", "message": "서버 작동 중 ✅"}
