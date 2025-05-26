
from fastapi import FastAPI, Request
import requests
import os

app = FastAPI()

TELEGRAM_TOKEN = "7287889681:AAHqKbipumgMmRQ8J4_Zu8Nlu_CYDnbCt0U"
CHAT_IDS = ["1901931119"]

def send_telegram_message(message: str):
    for chat_id in CHAT_IDS:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {"chat_id": chat_id, "text": message, "parse_mode": "Markdown"}
        try:
            response = requests.post(url, json=payload, timeout=10)
            print("텔레그램 응답:", response.status_code, response.text)
        except Exception as e:
            print(f"[오류] 텔레그램 전송 실패: {e}")

@app.post("/send-message")
async def send_message(request: Request):
    data = await request.json()
    message = data.get("message", "")
    if not message:
        return {"status": "fail", "message": "❌ 메시지가 비어 있습니다"}
    send_telegram_message(message)
    return {"status": "success", "message": "✅ 텔레그램 전송 완료"}

@app.get("/")
def root():
    return {"status": "OK", "message": "서버 연결됨 ✅"}
