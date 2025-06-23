
import time
import requests
import numpy as np
import pandas as pd
from binance.client import Client
from binance.enums import *
from ta.momentum import RSIIndicator
from ta.trend import EMAIndicator, MACD

API_KEY = 'your_api_key_here'
API_SECRET = 'your_api_secret_here'
symbol = "SOLUSDT"
quantity_pct = 0.8  # 80% din capital
leverage = 50

telegram_token = "your_telegram_token"
telegram_chat_id = "your_telegram_chat_id"

client = Client(API_KEY, API_SECRET)
client.futures_change_leverage(symbol=symbol, leverage=leverage)

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{telegram_token}/sendMessage"
    data = {"chat_id": telegram_chat_id, "text": msg}
    requests.post(url, data=data)

def get_data(symbol):
    klines = client.futures_klines(symbol=symbol, interval=Client.KLINE_INTERVAL_15MINUTE, limit=100)
    df = pd.DataFrame(klines, columns=[
        'timestamp', 'open', 'high', 'low', 'close', 'volume',
        'close_time', 'quote_asset_volume', 'number_of_trades',
        'taker_buy_base_volume', 'taker_buy_quote_volume', 'ignore'
    ])
    df['close'] = pd.to_numeric(df['close'])
    df['volume'] = pd.to_numeric(df['volume'])
    return df

def signal_generator(df):
    rsi = RSIIndicator(df['close'], window=18).rsi()
    ema = EMAIndicator(df['close'], window=21).ema_indicator()
    macd = MACD(df['close']).macd_diff()

    if rsi.iloc[-1] > 50 and df['close'].iloc[-1] > ema.iloc[-1] and macd.iloc[-1] > 0:
        return "LONG"
    elif rsi.iloc[-1] < 50 and df['close'].iloc[-1] < ema.iloc[-1] and macd.iloc[-1] < 0:
        return "SHORT"
    return "WAIT"

def get_balance():
    bal = client.futures_account_balance()
    usdt = float([x for x in bal if x['asset'] == 'USDT'][0]['balance'])
    return usdt * quantity_pct

def execute_order(direction):
    usdt = get_balance()
    mark_price = float(client.futures_mark_price(symbol=symbol)['markPrice'])
    qty = round(usdt * leverage / mark_price, 2)
    try:
        side = SIDE_BUY if direction == "LONG" else SIDE_SELL
        client.futures_create_order(symbol=symbol, side=side, type=ORDER_TYPE_MARKET, quantity=qty)
        send_telegram(f"✅ {direction} order executed: {qty} {symbol}")
    except Exception as e:
        send_telegram(f"❌ Order error: {str(e)}")

last_signal = ""

while True:
    try:
        df = get_data(symbol)
        signal = signal_generator(df)

        if signal != last_signal and signal in ["LONG", "SHORT"]:
            send_telegram(f"📡 {signal} signal (RSI crossed 50 with full confirmation)")
            execute_order(signal)
            last_signal = signal
        time.sleep(60)
    except Exception as e:
        send_telegram(f"⚠️ Error: {str(e)}")
        time.sleep(60)
