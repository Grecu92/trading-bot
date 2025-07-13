
import requests
import time
import pandas as pd
import numpy as np
import telegram

TOKEN = "PASTE_YOUR_BOT_TOKEN_HERE"
CHAT_ID = "1368917672"
bot = telegram.Bot(token=TOKEN)

SYMBOLS = [
    "BTCUSDT", "ETHUSDT", "SOLUSDT", "XRPUSDT", "DOGEUSDT", "BNBUSDT", "SUIUSDT", "ADAUSDT",
    "UNIUSDT", "AAVEUSDT", "LTCUSDT", "BCHUSDT", "ENAUSDT", "TRXUSDT", "AVAXUSDT", "LINKUSDT",
    "XLMUSDT", "WIFUSDT", "DOTUSDT", "HBARUSDT", "FILUSDT", "APTUSDT", "ARBUSDT", "NEARUSDT",
    "WLDUSDT", "TONUSDT", "FORMUSDT", "ONDOUSDT", "TAOUSDT", "TRUMPUSDT"
]

def get_klines(symbol, interval='15m', limit=51):
    url = f"https://fapi.binance.com/fapi/v1/klines?symbol={symbol}&interval={interval}&limit={limit}"
    response = requests.get(url)
    data = response.json()
    closes = [float(k[4]) for k in data]
    return closes

def calculate_sma(prices, period):
    return pd.Series(prices).rolling(window=period).mean().tolist()

def check_cross(symbol):
    try:
        closes = get_klines(symbol)
        sma20 = calculate_sma(closes, 20)
        sma50 = calculate_sma(closes, 50)

        if len(sma50) < 2:
            return

        if sma20[-2] <= sma50[-2] and sma20[-1] > sma50[-1]:
            message = f"🔔 SMA CROSSOVER DETECTED\n\n✅ Symbol: {symbol}\nTimeframe: 15m\n📈 SMA20 just crossed above SMA50\n📉 Previous: SMA20 < SMA50\n🕒 Time: {time.strftime('%H:%M UTC')}"
            bot.send_message(chat_id=CHAT_ID, text=message)
    except Exception as e:
        print(f"Error with {symbol}: {e}")

def main():
    while True:
        for symbol in SYMBOLS:
            check_cross(symbol)
        time.sleep(900)  # Wait 15 minutes

if __name__ == "__main__":
    main()
