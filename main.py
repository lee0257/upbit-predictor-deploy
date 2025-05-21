import asyncio
import aiohttp
import requests
from datetime import datetime
import pytz
import time
from supabase import create_client, Client

# 환경변수 설정 (최종 실전용)
SUPABASE_URL = "https://dsqknuytqrhbrztipamj.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImRzcWtudXl0cXJoYnJ6dGlwYW1qIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDc4MDI3MzQsImV4cCI6MjA2MzM3ODczNH0.qQgJmDDd61uNEahpIJVk60yY0uXbMV33g3baA9pJFEA"
TELEGRAM_TOKEN = "7287889681:AAHqKbipumgMmRQ8J4_Zu8Nlu_CYDnbCt0U"
TELEGRAM_CHAT_IDS = [1901931119]

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
sent = {}

async def fetch_market_codes(session):
    url = "https://api.upbit.com/v1/market/all"
    async with session.get(url) as response:
        return await response.json()

async def fetch_ticker(session, markets):
    url = f"https://api.upbit.com/v1/ticker?markets={','.join(markets)}"
    async with session.get(url) as response:
        return await response.json()

def generate_reason(data):
    reasons = []
    if data['acc_trade_price_24h'] > 1200000000:
        reasons.append("거래대금 폭발")
    if data['signed_change_rate'] * 100 > 2:
        reasons.append("순매수 급증")
    if data['high_price'] == data['trade_price']:
        reasons.append("당일 고가 돌파")
    if not reasons:
        return "체결량 급증 + 매수 강세 포착"
    return " + ".join(reasons)

async def check_and_alert():
    async with aiohttp.ClientSession() as session:
        markets = await fetch_market_codes(session)
        krw_markets = [m['market'] for m in markets if m['market'].startswith('KRW-')]
        market_names = {m['market']: m['korean_name'] for m in markets if m['market'].startswith('KRW-')]

        tickers = await fetch_ticker(session, krw_markets)
        now = time.time()

        for data in tickers:
            market = data['market']
            trade_price = data['trade_price']
            acc_trade_price = data['acc_trade_price_24h']
            signed_change_rate = data['signed_change_rate'] * 100

            if acc_trade_price < 800000000 or signed_change_rate < 1.0:
                continue

            coin_name = market_names.get(market, market)
            target_price = trade_price * 1.03
            buy_price_low = trade_price * 0.995
            profit_rate = (target_price - trade_price) / trade_price * 100
            reason_text = generate_reason(data)

            message = f"[추천코인1]\n"
            message += f"- 코인명: {coin_name} ({market.split('-')[1]})\n"
            message += f"- 현재가: {int(trade_price):,}원\n"
            message += f"- 매수 추천가: {int(buy_price_low):,} ~ {int(trade_price):,}원\n"
            message += f"- 목표 매도가: {int(target_price):,}원\n"
            message += f"- 예상 수익률: 약 {profit_rate:.1f}%\n"
            message += f"- 예상 소요 시간: 10분 내외\n"
            message += f"- 추천 이유: {reason_text}\n"
            message += f"[선행급등포착] 📈"

            if market not in sent or now - sent[market] > 1800:
                for chat_id in TELEGRAM_CHAT_IDS:
                    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
                    payload = {"chat_id": chat_id, "text": message}
                    requests.post(url, json=payload)
                try:
                    supabase.table("messages").insert({"created_at": datetime.now(pytz.timezone("Asia/Seoul")).isoformat()}).execute()
                except Exception as e:
                    print("[DB 저장 실패]", e)
                sent[market] = now
                print("▶ 알림 전송 완료:", coin_name)

async def main():
    while True:
        try:
            print("▶ 실행 시작 - 전체 로직 동작")
            await check_and_alert()
        except Exception as e:
            print("[예외 발생]", e)
        await asyncio.sleep(60)

if __name__ == '__main__':
    asyncio.run(main())
