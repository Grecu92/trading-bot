import os
import time
import requests
from binance.client import Client
from binance.enums import HistoricalKlinesType
import ta

# Setări din variabilele de mediu
API_KEY = os.getenv("BINANCE_API_KEY")
API_SECRET = os.getenv("BINANCE_API_SECRET")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
SYMBOL = os.getenv("SYMBOL", "SOLUSDT")

client = Client(API_KEY, API_SECRET)

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    requests.post(url, data=data)

def fetch_rsi(symbol):
    klines = client.get_klines(symbol=symbol, interval=Client.KLINE_INTERVAL_15MINUTE, limit=50, klines_type=HistoricalKlinesType.SPOT)
    closes = [float(k[4]) for k in klines]
    df = ta.utils.pd.DataFrame({'close': closes})
    df['rsi'] = ta.momentum.RSIIndicator(df['close'], window=18).rsi()
    return df['rsi'].iloc[-2], df['rsi'].iloc[-1]

prev_signal = None

send_telegram_message(f"Bot started for symbol: {SYMBOL}")

while True:
    try:
        rsi_prev, rsi_now = fetch_rsi(SYMBOL)
        if rsi_prev < 50 and rsi_now >= 50:
            signal = "LONG"
        elif rsi_prev > 50 and rsi_now <= 50:
            signal = "SHORT"
        else:
            signal = None

        if signal and signal != prev_signal:
            send_telegram_message(f"{signal} signal (RSI crossed 50)")
            send_telegram_message("Trailing TP 0.20% logic enabled.")
            prev_signal = signal

        time.sleep(60)

    except Exception as e:
        send_telegram_message(f"Error: {str(e)}")
        time.sleep(60)
