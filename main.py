import os
import requests
import time
from binance.client import Client
from binance.enums import *
import talib
import numpy as np
import pandas as pd
import logging

# Setări de logare
logging.basicConfig(level=logging.INFO)

# Variabile de mediu
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_USER_ID = os.getenv("TELEGRAM_USER_ID")
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")
BINANCE_API_SECRET = os.getenv("BINANCE_API_SECRET")
SYMBOL = os.getenv("SYMBOL", "BTCDOMUSDT")

client = Client(BINANCE_API_KEY, BINANCE_API_SECRET)

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {"chat_id": TELEGRAM_USER_ID, "text": message}
    requests.post(url, data=data)

def get_klines(symbol, interval="15m", limit=100):
    data = client.get_klines(symbol=symbol, interval=interval, limit=limit)
    df = pd.DataFrame(data, columns=[
        'timestamp', 'open', 'high', 'low', 'close', 'volume',
        'close_time', 'quote_asset_volume', 'number_of_trades',
        'taker_buy_base_volume', 'taker_buy_quote_volume', 'ignore'
    ])
    df["close"] = df["close"].astype(float)
    df["volume"] = df["volume"].astype(float)
    return df

def analyze():
    df = get_klines(SYMBOL)
    closes = df["close"].values
    volumes = df["volume"].values

    rsi = talib.RSI(closes, timeperiod=18)
    macd, macdsignal, _ = talib.MACD(closes, fastperiod=12, slowperiod=26, signalperiod=9)
    ema21 = talib.EMA(closes, timeperiod=21)

    last_close = closes[-1]
    last_rsi = rsi[-1]
    last_macd = macd[-1]
    last_macdsignal = macdsignal[-1]
    last_ema = ema21[-1]
    avg_vol = np.mean(volumes[-6:-1])
    vol_spike = volumes[-1] > avg_vol

    if last_rsi > 50 and last_macd > last_macdsignal and last_close > last_ema and vol_spike:
        send_telegram(f"✅ LONG SIGNAL: {SYMBOL}\nRSI(18): {round(last_rsi, 2)}\nClose: {last_close}\nEMA(21): {round(last_ema, 5)}\nVolume Spike: ✅")
        execute_trade("BUY")
    elif last_rsi < 50 and last_macd < last_macdsignal and last_close < last_ema and vol_spike:
        send_telegram(f"🔻 SHORT SIGNAL: {SYMBOL}\nRSI(18): {round(last_rsi, 2)}\nClose: {last_close}\nEMA(21): {round(last_ema, 5)}\nVolume Spike: ✅")
        execute_trade("SELL")

def execute_trade(direction):
    balance = float(client.futures_account_balance()[1]["balance"])
    amount_usdt = balance * 0.5
    mark_price = float(client.futures_mark_price(symbol=SYMBOL)["markPrice"])
    quantity = round((amount_usdt * 10) / mark_price, 3)

    side = SIDE_BUY if direction == "BUY" else SIDE_SELL

    order = client.futures_create_order(
        symbol=SYMBOL,
        side=side,
        type=ORDER_TYPE_MARKET,
        quantity=quantity
    )
    logging.info(f"Order Executed: {order}")
    send_telegram(f"💸 Executed {direction} order: {quantity} {SYMBOL}")

while True:
    try:
        analyze()
        time.sleep(60)
    except Exception as e:
        send_telegram(f"❌ Error: {str(e)}")
        time.sleep(60)
