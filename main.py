
import pandas as pd
import ta
import time
from binance.client import Client
from binance.enums import HistoricalKlinesType
import requests

# === CONFIGURARE ===
symbol = "SOLUSDT"
interval = Client.KLINE_INTERVAL_15MINUTE
rsi_period = 18
telegram_token = "7603921163:AAHQ5GFx_QAJ_cEu5LOwZAy0CYtW0REdXdI"
telegram_chat_id = "1368917672"
api_key = "your_api_key_here"
api_secret = "your_api_secret_here"

client = Client(api_key, api_secret)

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{telegram_token}/sendMessage"
    data = {"chat_id": telegram_chat_id, "text": message}
    try:
        requests.post(url, data=data)
    except Exception as e:
        print("Telegram Error:", e)

last_signal = None

while True:
    try:
        klines = client.get_historical_klines(
            symbol=symbol,
            interval=interval,
            start_str="3 days ago UTC",
            klines_type=HistoricalKlinesType.FUTURES
        )
        df = pd.DataFrame(klines, columns=[
            "timestamp", "open", "high", "low", "close", "volume",
            "close_time", "quote_asset_volume", "number_of_trades",
            "taker_buy_base_volume", "taker_buy_quote_volume", "ignore"
        ])
        df["close"] = pd.to_numeric(df["close"])
        df["rsi"] = ta.momentum.RSIIndicator(df["close"], rsi_period).rsi()

        current_rsi = df["rsi"].iloc[-1]
        prev_rsi = df["rsi"].iloc[-2]

        if prev_rsi < 50 and current_rsi > 50 and last_signal != "LONG":
            last_signal = "LONG"
            send_telegram_message(f"LONG signal (RSI crossed 50 ↑) for {symbol}")
        elif prev_rsi > 50 and current_rsi < 50 and last_signal != "SHORT":
            last_signal = "SHORT"
            send_telegram_message(f"SHORT signal (RSI crossed 50 ↓) for {symbol}")

    except Exception as e:
        print("Error in main loop:", e)

    time.sleep(60)
