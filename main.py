import os
import time
import requests
from binance.client import Client
from binance.enums import *
import ta
import pandas as pd

# Config
symbol = os.getenv("SYMBOL", "SOLUSDT")
interval = Client.KLINE_INTERVAL_15MINUTE
api_key = os.getenv("BINANCE_API_KEY")
api_secret = os.getenv("BINANCE_API_SECRET")
telegram_token = os.getenv("TELEGRAM_BOT_TOKEN")
telegram_chat_id = os.getenv("TELEGRAM_CHAT_ID")

client = Client(api_key, api_secret)

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{telegram_token}/sendMessage"
    payload = {"chat_id": telegram_chat_id, "text": message}
    requests.post(url, data=payload)

def get_rsi_signal(df):
    rsi = ta.momentum.RSIIndicator(close=df["close"], window=18).rsi()
    df["rsi"] = rsi
    latest_rsi = df["rsi"].iloc[-1]
    prev_rsi = df["rsi"].iloc[-2]

    if prev_rsi < 50 and latest_rsi > 50:
        return "LONG"
    elif prev_rsi > 50 and latest_rsi < 50:
        return "SHORT"
    return None

def get_klines(symbol, interval, limit=100):
    klines = client.get_klines(symbol=symbol, interval=interval, limit=limit)
    df = pd.DataFrame(klines, columns=[
        "timestamp", "open", "high", "low", "close", "volume",
        "close_time", "quote_asset_volume", "number_of_trades",
        "taker_buy_base_asset_volume", "taker_buy_quote_asset_volume", "ignore"
    ])
    df["close"] = df["close"].astype(float)
    return df

send_telegram_message(f"Bot started for symbol: {symbol}")

while True:
    try:
        df = get_klines(symbol, interval)
        signal = get_rsi_signal(df)
        if signal:
            send_telegram_message(f"{signal} signal (RSI crossed 50)
Trailing Stop: 0.20%")
        time.sleep(60)
    except Exception as e:
        send_telegram_message(f"Error: {e}")
        time.sleep(60)