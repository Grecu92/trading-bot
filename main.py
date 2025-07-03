import time
import requests
from binance.client import Client
from ta.momentum import RSIIndicator
import pandas as pd

# Configurări Binance
api_key = "YOUR_BINANCE_API_KEY"
api_secret = "YOUR_BINANCE_API_SECRET"
client = Client(api_key, api_secret)

# Configurări Telegram
telegram_token = "YOUR_TELEGRAM_BOT_TOKEN"
telegram_chat_id = "YOUR_TELEGRAM_CHAT_ID"

symbol = "PARTIUSDT"
interval = Client.KLINE_INTERVAL_15MINUTE

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{telegram_token}/sendMessage"
    data = {"chat_id": telegram_chat_id, "text": message}
    requests.post(url, data=data)

def fetch_data():
    klines = client.get_klines(symbol=symbol, interval=interval, limit=100)
    df = pd.DataFrame(klines, columns=[
        "timestamp", "open", "high", "low", "close", "volume",
        "close_time", "quote_asset_volume", "number_of_trades",
        "taker_buy_base_asset_volume", "taker_buy_quote_asset_volume", "ignore"
    ])
    df["close"] = df["close"].astype(float)
    df["open"] = df["open"].astype(float)
    return df

def analyze_and_alert():
    df = fetch_data()
    rsi = RSIIndicator(df["close"], window=18).rsi()
    last_rsi = rsi.iloc[-1]
    last_close = df["close"].iloc[-1]
    prev_close = df["close"].iloc[-2]
    prev_rsi = rsi.iloc[-2]

    if prev_rsi < 50 and last_rsi > 50 and last_close > prev_close:
        send_telegram_message("LONG signal (RSI crossed above 50 + Price rising)")
    elif prev_rsi > 50 and last_rsi < 50 and last_close < prev_close:
        send_telegram_message("SHORT signal (RSI crossed below 50 + Price falling)")

if __name__ == "__main__":
    while True:
        try:
            analyze_and_alert()
            time.sleep(60)
        except Exception as e:
            send_telegram_message(f"Error: {str(e)}")
            time.sleep(60)