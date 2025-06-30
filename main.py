
import time
import requests
import pandas as pd
from binance.client import Client
from ta.momentum import RSIIndicator
from datetime import datetime

# Setări Binance și Telegram
API_KEY = "YOUR_BINANCE_API_KEY"
API_SECRET = "YOUR_BINANCE_SECRET_KEY"
TELEGRAM_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"
CHAT_ID = "YOUR_TELEGRAM_CHAT_ID"
SYMBOLS = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT", "ADAUSDT", "AVAXUSDT", "DOGEUSDT", "MATICUSDT", "DOTUSDT",
           "TRXUSDT", "LTCUSDT", "BCHUSDT", "LINKUSDT", "XLMUSDT", "ATOMUSDT", "ETCUSDT", "FILUSDT", "ICPUSDT", "HBARUSDT",
           "NEARUSDT", "EGLDUSDT", "VETUSDT", "APEUSDT", "ARBUSDT", "SANDUSDT", "MANAUSDT", "RUNEUSDT", "AAVEUSDT", "GRTUSDT",
           "FTMUSDT", "XTZUSDT", "CROUSDT", "GALAUSDT", "DYDXUSDT", "GMXUSDT", "RNDRUSDT", "LDOUSDT", "FLOWUSDT", "TUSDT",
           "KAVAUSDT", "ENSUSDT", "IMXUSDT", "OPUSDT", "ZILUSDT", "CKBUSDT", "DASHUSDT", "PEPEUSDT", "SHIBUSDT", "STXUSDT"]

client = Client(API_KEY, API_SECRET)

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message}
    requests.post(url, data=payload)

def fetch_rsi(symbol):
    try:
        klines = client.get_klines(symbol=symbol, interval=Client.KLINE_INTERVAL_15MINUTE, limit=100)
        df = pd.DataFrame(klines, columns=["timestamp", "o", "h", "l", "c", "v", "ct", "q", "n", "taker_base", "taker_quote", "ignore"])
        df["c"] = df["c"].astype(float)
        rsi = RSIIndicator(df["c"], window=18).rsi().iloc[-1]
        return rsi
    except Exception as e:
        print(f"Eroare la {symbol}: {e}")
        return None

print("Botul a pornit. Se verifică RSI pentru 50 de monede...")

while True:
    for symbol in SYMBOLS:
        rsi = fetch_rsi(symbol)
        if rsi:
            if rsi > 70:
                send_telegram_message(f"{symbol}: RSI(18) peste 70 – posibil SHORT!")
            elif rsi < 30:
                send_telegram_message(f"{symbol}: RSI(18) sub 30 – posibil LONG!")
    time.sleep(60 * 15)
