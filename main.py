import time
import pandas as pd
from binance.client import Client
from ta.momentum import RSIIndicator
import requests

api_key = "API_KEY"
api_secret = "API_SECRET"
client = Client(api_key, api_secret)

symbols = [
    "BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "XRPUSDT", "ADAUSDT", "DOGEUSDT", "AVAXUSDT", "DOTUSDT", "MATICUSDT",
    "LTCUSDT", "TRXUSDT", "LINKUSDT", "BCHUSDT", "XLMUSDT", "ATOMUSDT", "UNIUSDT", "ETCUSDT", "HBARUSDT", "VETUSDT",
    "FILUSDT", "ICPUSDT", "NEARUSDT", "APEUSDT", "GRTUSDT", "QNTUSDT", "EGLDUSDT", "SANDUSDT", "MANAUSDT", "XTZUSDT",
    "AAVEUSDT", "THETAUSDT", "AXSUSDT", "RUNEUSDT", "SNXUSDT", "KAVAUSDT", "FLOWUSDT", "CHZUSDT", "CRVUSDT", "ENJUSDT",
    "1INCHUSDT", "BATUSDT", "ZILUSDT", "DYDXUSDT", "LRCUSDT", "STMXUSDT", "SKLUSDT", "XEMUSDT", "WAVESUSDT", "ANKRUSDT"
]

telegram_token = "YOUR_TELEGRAM_BOT_TOKEN"
telegram_chat_id = "YOUR_CHAT_ID"

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{telegram_token}/sendMessage"
    data = {"chat_id": telegram_chat_id, "text": message}
    requests.post(url, data=data)

def get_rsi(symbol):
    klines = client.get_klines(symbol=symbol, interval=Client.KLINE_INTERVAL_15MINUTE, limit=100)
    close_prices = [float(k[4]) for k in klines]
    df = pd.DataFrame(close_prices, columns=["close"])
    rsi = RSIIndicator(df["close"], window=18).rsi()
    return rsi.iloc[-1]

last_signal = {}

while True:
    for symbol in symbols:
        try:
            rsi = get_rsi(symbol)
            last = last_signal.get(symbol)

            if rsi > 70 and last != "overbought":
                send_telegram_message(f"{symbol}: RSI(18) peste 70 (overbought)")
                last_signal[symbol] = "overbought"
            elif rsi < 30 and last != "oversold":
                send_telegram_message(f"{symbol}: RSI(18) sub 30 (oversold)")
                last_signal[symbol] = "oversold"
        except Exception as e:
            print(f"Eroare la {symbol}: {e}")

    time.sleep(60)
