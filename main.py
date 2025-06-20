import os
import time
import ccxt
import requests
import logging
import numpy as np
from datetime import datetime

# 🔧 Config din Railway (variabile de mediu)
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_USER_ID = os.getenv("TELEGRAM_USER_ID")
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")
BINANCE_API_SECRET = os.getenv("BINANCE_API_SECRET")
SYMBOL = os.getenv("SYMBOL", "BTCDOM/USDT")

# 📡 Setup Binance Futures
exchange = ccxt.binance({
    'apiKey': BINANCE_API_KEY,
    'secret': BINANCE_API_SECRET,
    'enableRateLimit': True,
    'options': {'defaultType': 'future'}
})

# 🧠 Indicatori tehnici
def rsi(values, period=18):
    delta = np.diff(values)
    gain = np.mean([d for d in delta if d > 0]) if len(delta) > 0 else 0
    loss = -np.mean([d for d in delta if d < 0]) if len(delta) > 0 else 0
    if loss == 0:
        return 100
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def ema(values, period=21):
    weights = np.exp(np.linspace(-1., 0., period))
    weights /= weights.sum()
    a = np.convolve(values, weights, mode='valid')
    return a[-1] if len(a) else None

def get_signal():
    ohlcv = exchange.fetch_ohlcv(SYMBOL, timeframe='15m', limit=50)
    closes = [c[4] for c in ohlcv]
    volumes = [c[5] for c in ohlcv]

    current_price = closes[-1]
    current_rsi = rsi(closes)
    current_ema = ema(closes)
    avg_volume = np.mean(volumes[:-1])
    current_volume = volumes[-1]

    if not current_ema:
        return None, current_price

    # Confirmări: EMA + volum
    if current_rsi > 50 and current_price > current_ema and current_volume > avg_volume:
        return "LONG", current_price
    elif current_rsi < 50 and current_price < current_ema and current_volume > avg_volume:
        return "SHORT", current_price
    return "WAIT", current_price

# 🔔 Alerte Telegram
def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_USER_ID, "text": message}
    try:
        requests.post(url, data=payload)
    except Exception as e:
        print("Telegram error:", e)

# 📈 Execuție ordine
def place_order(signal, amount=50):
    side = 'buy' if signal == 'LONG' else 'sell'
    try:
        order = exchange.create_market_order(SYMBOL.replace("/", ""), side, amount)
        return order
    except Exception as e:
        send_telegram(f"Eroare la ordin: {e}")
        return None

# ▶️ Main loop
def run_bot():
    last_signal = "WAIT"
    while True:
        try:
            signal, price = get_signal()
            if signal != last_signal and signal != "WAIT":
                order = place_order(signal)
                if order:
                    send_telegram(f"{signal} EXECUTAT la {price} pentru {SYMBOL}")
                    last_signal = signal
            else:
                print(f"[{datetime.now()}] {signal} - {price}")
            time.sleep(60)
        except Exception as e:
            send_telegram(f"Eroare: {e}")
            time.sleep(60)

if __name__ == "__main__":
    send_telegram("🤖 BOT PORNIT CU SUCCES!")
    run_bot()
