import time
from binance.client import Client
import pandas as pd
from ta.momentum import RSIIndicator
import requests

API_KEY = 'API_KEY_TAU'
API_SECRET = 'SECRET_KEY_TAU'
symbol = "SOLUSDT"
interval = Client.KLINE_INTERVAL_15MINUTE
rsi_period = 18
telegram_token = "TOKENUL_TAU"
telegram_chat_id = "CHAT_ID_TAU"

client = Client(API_KEY, API_SECRET)

def get_klines(symbol, interval, limit=100):
    klines = client.get_klines(symbol=symbol, interval=interval, limit=limit)
    df = pd.DataFrame(klines, columns=[
        'timestamp', 'open', 'high', 'low', 'close', 'volume',
        'close_time', 'quote_asset_volume', 'number_of_trades',
        'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'
    ])
    df['close'] = pd.to_numeric(df['close'])
    return df

def calculate_rsi(data):
    rsi = RSIIndicator(close=data['close'], window=rsi_period).rsi()
    return rsi.iloc[-1]

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{telegram_token}/sendMessage"
    payload = {"chat_id": telegram_chat_id, "text": message}
    requests.post(url, data=payload)

print(f"Bot started for symbol: {symbol}")

last_signal = None

while True:
    try:
        df = get_klines(symbol, interval)
        rsi = calculate_rsi(df)

        if rsi > 50 and last_signal != "LONG":
            send_telegram_message(f"LONG signal (RSI crossed 50 ↑) — RSI: {rsi:.2f}")
            last_signal = "LONG"

        elif rsi < 50 and last_signal != "SHORT":
            send_telegram_message(f"SHORT signal (RSI crossed 50 ↓) — RSI: {rsi:.2f}")
            last_signal = "SHORT"

        time.sleep(60)

    except Exception as e:
        print(f"Error in main loop: {e}")
        time.sleep(60)
