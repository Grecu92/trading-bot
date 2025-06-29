import time
import requests
from binance.client import Client
from ta.momentum import RSIIndicator
import pandas as pd

import os

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")
BINANCE_API_SECRET = os.getenv("BINANCE_API_SECRET")

client = Client(BINANCE_API_KEY, BINANCE_API_SECRET)

SYMBOLS = [
    "ALPHAUSDT", "SOONUSDT", "DEXEUSDT", "BMTUSDT", "LEVERUSDT",
    "RESOLVUSDT", "HOOKUSDT", "DFUSDT", "ZKJUSDT", "CHESSUSDT",
    "LISTAUSDT", "FXSUSDT", "BSWUSDT", "KMNOUSDT", "MAVIAUSDT",
    "RELIUSDT", "WAXPUSDT", "PLUMEUSDT", "GUSDT", "MELANIAUSDT",
    "HUSDT", "DMCUSDT", "CTKUSDT", "BROCCOLI714USDT", "1000CATUSDT",
    "SAHARAUSDT", "PENGUSDT", "BIDUSDT", "SPKUSDT", "SIRENUSDT",
    "LPTUSDT", "CHILLGUYUSDT", "PROMUSDT", "HFTUSDT", "SQDUSDT",
    "OGNUSDT", "KOMAUSDT", "DRIFTUSDT", "CGPTUSDT", "FARTCOINUSDT",
    "CGPTUSDT", "MUBARAKUSDT", "EPTUSDT", "SUPERUSDT", "HOMEUSDT",
    "JUPUSDT", "BANKUSDT", "ARUSDT", "BUSDT", "A16ZUSDT"
]

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    requests.post(url, data=payload)

def get_rsi(symbol):
    klines = client.get_klines(symbol=symbol, interval=Client.KLINE_INTERVAL_15MINUTE, limit=100)
    df = pd.DataFrame(klines, columns=[
        "timestamp", "open", "high", "low", "close", "volume",
        "close_time", "quote_asset_volume", "number_of_trades",
        "taker_buy_base_asset_volume", "taker_buy_quote_asset_volume", "ignore"
    ])
    df["close"] = pd.to_numeric(df["close"])
    rsi = RSIIndicator(df["close"], window=18).rsi()
    return rsi.iloc[-1]

def main():
    print("Bot started monitoring RSI(18)...")
    sent_alerts = {}
    while True:
        for symbol in SYMBOLS:
            try:
                rsi = get_rsi(symbol)
                last_signal = sent_alerts.get(symbol)
                if rsi > 60 and last_signal != "LONG":
                    send_telegram_message(f"{symbol} - RSI crossed above 60 🚀 (LONG signal)")
                    sent_alerts[symbol] = "LONG"
                elif rsi < 30 and last_signal != "SHORT":
                    send_telegram_message(f"{symbol} - RSI crossed below 30 📉 (SHORT signal)")
                    sent_alerts[symbol] = "SHORT"
            except Exception as e:
                print(f"Error fetching RSI for {symbol}: {e}")
        time.sleep(60)

if __name__ == "__main__":
    main()