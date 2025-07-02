
import time
import requests
from binance.client import Client
from ta.momentum import RSIIndicator
import pandas as pd
from datetime import datetime
import pytz

BINANCE_API_KEY = "your_binance_api_key"
BINANCE_API_SECRET = "your_binance_api_secret"
TELEGRAM_BOT_TOKEN = "your_telegram_bot_token"
TELEGRAM_CHAT_ID = "your_chat_id"

SYMBOLS = [
    "USUALUSDT", "HIFTUSDT", "AGTUSDT", "HUSPOT", "GOATUSDT", "SQDUSDT", "VIRTUALUSDT",
    "AI162USDT", "DEGENUSDT", "ARKUSDT", "POPCATUSDT", "LRCUSDT", "SSVSUSDT", "JELLYJELLYUSDT",
    "VANRYUSDT", "MYROUSDT", "PONKEUSDT", "PNUTUSDT", "PNUTUSDC", "MUBARAKUSDT",
    "SKYAIUSDT", "SWARMSUSDT", "PLUMEUSDT", "AVAAIUSDT", "NEIROUSDT", "BIDUSDT", "GRIFFAINUSDT",
    "CHILLGUYUSDT", "MERLUSDT", "FIDAUSDT", "PORTALUSDT", "FISUSDT", "ARCUSDT", "SPXUSDT",
    "1000000MOGUSDT", "MOODENGUSDT", "1000000BOBUSDT"
]

client = Client(BINANCE_API_KEY, BINANCE_API_SECRET)

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    requests.post(url, data=payload)

def get_rsi(symbol):
    try:
        klines = client.get_klines(symbol=symbol, interval=Client.KLINE_INTERVAL_15MINUTE, limit=100)
        df = pd.DataFrame(klines, columns=[
            'timestamp', 'open', 'high', 'low', 'close', 'volume',
            'close_time', 'quote_asset_volume', 'number_of_trades',
            'taker_buy_base', 'taker_buy_quote', 'ignore'
        ])
        df['close'] = df['close'].astype(float)
        rsi = RSIIndicator(df['close'], window=18).rsi()
        return rsi.iloc[-2], rsi.iloc[-1]  # previous, current
    except Exception as e:
        return None, None

def main():
    sent_alerts = set()
    while True:
        for symbol in SYMBOLS:
            prev_rsi, curr_rsi = get_rsi(symbol)
            if prev_rsi is None or curr_rsi is None:
                continue

            key_70 = f"{symbol}_70"
            key_30 = f"{symbol}_30"

            if prev_rsi < 70 and curr_rsi >= 70 and key_70 not in sent_alerts:
                send_telegram_message(f"{symbol} 🔺 RSI crossed ABOVE 70 (Overbought)")
                sent_alerts.add(key_70)
            elif prev_rsi > 70 and curr_rsi <= 70 and key_70 in sent_alerts:
                sent_alerts.remove(key_70)

            if prev_rsi > 30 and curr_rsi <= 30 and key_30 not in sent_alerts:
                send_telegram_message(f"{symbol} 🔻 RSI crossed BELOW 30 (Oversold)")
                sent_alerts.add(key_30)
            elif prev_rsi < 30 and curr_rsi >= 30 and key_30 in sent_alerts:
                sent_alerts.remove(key_30)

        time.sleep(60)

if __name__ == "__main__":
    main()
