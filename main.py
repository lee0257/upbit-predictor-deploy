from flask import Flask, request
import requests

app = Flask(__name__)

TELEGRAM_TOKEN = "7287889681:AAGM2BXvqJSyzbCrF25hy_WzCL40Cute64A"
CHAT_ID = "1901931119"

@app.route("/")
def home():
    return "Telegram test server running"

@app.route("/send")
def send_message():
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": "[Render 테스트] 텔레그램 메시지 전송 성공 🎉",
    }
    res = requests.post(url, data=payload)
    return {
        "status_code": res.status_code,
        "response": res.json()
    }

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
