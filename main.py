import time
import requests
from binance.client import Client
from binance.enums import *
import os

symbol = os.getenv("SYMBOL", "SOLUSDT")
interval = Client.KLINE_INTERVAL_15MINUTE
api_key = os.getenv("BINANCE_API_KEY")
api_secret = os.getenv("BINANCE_API_SECRET")
telegram_token = os.getenv("TELEGRAM_BOT_TOKEN")
telegram_chat_id = os.getenv("TELEGRAM_CHAT_ID")

client = Client(api_key, api_secret)

def get_rsi(symbol, interval, period=18):
    klines = client.get_klines(symbol=symbol, interval=interval, limit=period + 1)
    closes = [float(kline[4]) for kline in klines]
    deltas = [closes[i+1] - closes[i] for i in range(period)]
    gains = [delta if delta > 0 else 0 for delta in deltas]
    losses = [-delta if delta < 0 else 0 for delta in deltas]
    avg_gain = sum(gains) / period
    avg_loss = sum(losses) / period
    rs = avg_gain / avg_loss if avg_loss != 0 else 0
    rsi = 100 - (100 / (1 + rs))
    return rsi

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{telegram_token}/sendMessage"
    data = {"chat_id": telegram_chat_id, "text": message}
    try:
        requests.post(url, data=data)
    except Exception as e:
        print(f"Telegram error: {e}")

last_signal = None

while True:
    try:
        rsi = get_rsi(symbol, interval)
        print(f"Current RSI(18): {rsi:.2f}")

        signal = None
        if rsi > 50 and last_signal != "LONG":
            signal = "LONG"
            last_signal = "LONG"
        elif rsi < 50 and last_signal != "SHORT":
            signal = "SHORT"
            last_signal = "SHORT"

        if signal:
            send_telegram_message(f"{signal} signal (RSI crossed 50)
Trailing stop: 0.20%")

    except Exception as e:
        print(f"Error in main loop: {e}")

    time.sleep(60)
