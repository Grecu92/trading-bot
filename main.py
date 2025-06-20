
import time
from binance.client import Client
from binance.enums import *
import requests
import pandas as pd
import numpy as np
import os

api_key = os.getenv("BINANCE_API_KEY")
api_secret = os.getenv("BINANCE_API_SECRET")
symbol = os.getenv("SYMBOL", "SOLUSDT")
leverage = 10

client = Client(api_key, api_secret)

def get_klines(symbol, interval, limit=100):
    try:
        klines = client.futures_klines(symbol=symbol, interval=interval, limit=limit)
        df = pd.DataFrame(klines, columns=[
            'timestamp', 'open', 'high', 'low', 'close', 'volume',
            'close_time', 'quote_asset_volume', 'number_of_trades',
            'taker_buy_base_vol', 'taker_buy_quote_vol', 'ignore'
        ])
        df['close'] = df['close'].astype(float)
        df['volume'] = df['volume'].astype(float)
        return df
    except Exception as e:
        print("Error getting klines:", e)
        return pd.DataFrame()

def calculate_rsi(data, period=18):
    delta = data['close'].diff()
    gain = np.where(delta > 0, delta, 0)
    loss = np.where(delta < 0, -delta, 0)

    avg_gain = pd.Series(gain).rolling(window=period).mean()
    avg_loss = pd.Series(loss).rolling(window=period).mean()

    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def get_signal(rsi_series):
    if rsi_series.iloc[-2] < 50 and rsi_series.iloc[-1] >= 50:
        return "LONG"
    elif rsi_series.iloc[-2] > 50 and rsi_series.iloc[-1] <= 50:
        return "SHORT"
    return None

def place_order(side, quantity):
    try:
        order = client.futures_create_order(
            symbol=symbol,
            side=SIDE_BUY if side == "LONG" else SIDE_SELL,
            type=ORDER_TYPE_MARKET,
            quantity=quantity
        )
        print(f"Order placed: {side}")
        return order
    except Exception as e:
        print("Order error:", e)
        return None

def calculate_quantity(usdt_amount):
    price = float(client.futures_symbol_ticker(symbol=symbol)['price'])
    qty = round(usdt_amount / price, 3)
    return qty

def monitor_trade(entry_price, side):
    while True:
        price = float(client.futures_symbol_ticker(symbol=symbol)['price'])
        change = ((price - entry_price) / entry_price) * 100 if side == "LONG" else ((entry_price - price) / entry_price) * 100

        if change >= 0.7:
            client.futures_create_order(symbol=symbol, side=SIDE_SELL if side == "LONG" else SIDE_BUY,
                                        type=ORDER_TYPE_MARKET,
                                        quantity=calculate_quantity(used_capital))
            print("TP hit")
            break
        elif change <= -0.5:
            client.futures_create_order(symbol=symbol, side=SIDE_SELL if side == "LONG" else SIDE_BUY,
                                        type=ORDER_TYPE_MARKET,
                                        quantity=calculate_quantity(used_capital))
            print("SL hit")
            break
        elif change >= 0.3:
            trail_price = entry_price * (1.002 if side == "LONG" else 0.998)
            while True:
                price = float(client.futures_symbol_ticker(symbol=symbol)['price'])
                if (side == "LONG" and price < trail_price) or (side == "SHORT" and price > trail_price):
                    client.futures_create_order(symbol=symbol, side=SIDE_SELL if side == "LONG" else SIDE_BUY,
                                                type=ORDER_TYPE_MARKET,
                                                quantity=calculate_quantity(used_capital))
                    print("Trailing stop hit")
                    return
                time.sleep(5)
        time.sleep(10)

client.futures_change_leverage(symbol=symbol, leverage=leverage)
capital = float(client.futures_account_balance()[1]['balance'])
used_capital = capital * 0.5

print(f"Bot started for symbol: {symbol}")
while True:
    df = get_klines(symbol, '15m')
    if df.empty:
        time.sleep(10)
        continue
    df['rsi'] = calculate_rsi(df)
    signal = get_signal(df['rsi'])
    if signal:
        qty = calculate_quantity(used_capital)
        if qty > 0:
            order = place_order(signal, qty)
            if order:
                entry_price = float(order['fills'][0]['price'])
                monitor_trade(entry_price, signal)
    time.sleep(60)
