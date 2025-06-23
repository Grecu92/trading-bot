import os
import time
import requests
import pandas as pd
from binance.client import Client
from ta.momentum import RSIIndicator

api_key = os.getenv("BINANCE_API_KEY")
api_secret = os.getenv("BINANCE_API_SECRET")
symbol = os.getenv("SYMBOL", "SOLUSDT")
telegram_token = os.getenv("TELEGRAM_BOT_TOKEN")
telegram_chat_id = os.getenv("TELEGRAM_CHAT_ID")

client = Client(api_key, api_secret)
last_signal = None

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{telegram_token}/sendMessage"
    data = {"chat_id": telegram_chat_id, "text": message}
    requests.post(url, data=data)

def get_klines(symbol, interval='15m', limit=100):
    klines = client.get_klines(symbol=symbol, interval=interval, limit=limit)
    df = pd.DataFrame(klines, columns=[
        'timestamp', 'open', 'high', 'low', 'close', 'volume',
        'close_time', 'quote_asset_volume', 'number_of_trades',
        'taker_buy_base_volume', 'taker_buy_quote_volume', 'ignore'
    ])
    df['close'] = pd.to_numeric(df['close'])
    return df

def main():
    global last_signal
    while True:
        try:
            df = get_klines(symbol)
            rsi = RSIIndicator(df['close'], window=18).rsi()
            current_rsi = rsi.iloc[-1]

            if current_rsi > 50 and last_signal != "LONG":
                last_signal = "LONG"
                send_telegram_message("LONG signal (RSI crossed above 50)")
            elif current_rsi < 50 and last_signal != "SHORT":
                last_signal = "SHORT"
                send_telegram_message("SHORT signal (RSI crossed below 50)")

        except Exception as e:
            send_telegram_message(f"Error: {e}")

        time.sleep(60)

if __name__ == "__main__":
    main()