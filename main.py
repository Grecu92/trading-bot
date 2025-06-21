
import time
import os
from binance.client import Client
from binance.exceptions import BinanceAPIException
import pandas as pd
from datetime import datetime
from binance.enums import *

api_key = os.getenv("BINANCE_API_KEY")
api_secret = os.getenv("BINANCE_API_SECRET")
symbol = os.getenv("SYMBOL", "SOLUSDT")
leverage = int(os.getenv("LEVERAGE", 10))

client = Client(api_key, api_secret)

def get_klines(symbol, interval, limit=100):
    klines = client.futures_klines(symbol=symbol, interval=interval, limit=limit)
    df = pd.DataFrame(klines, columns=[
        'timestamp', 'open', 'high', 'low', 'close', 'volume',
        'close_time', 'quote_asset_volume', 'number_of_trades',
        'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'
    ])
    df['close'] = df['close'].astype(float)
    df['rsi'] = compute_rsi(df['close'], 18)
    return df

def compute_rsi(series, period):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def get_balance():
    balance = client.futures_account_balance()
    for b in balance:
        if b['asset'] == 'USDT':
            return float(b['balance'])
    return 0

def set_leverage(symbol, leverage):
    try:
        client.futures_change_leverage(symbol=symbol, leverage=leverage)
    except BinanceAPIException as e:
        print(f"Leverage error: {e}")

def place_order(position, quantity):
    try:
        side = SIDE_BUY if position == 'LONG' else SIDE_SELL
        order = client.futures_create_order(
            symbol=symbol,
            side=side,
            type=ORDER_TYPE_MARKET,
            quantity=quantity
        )
        print(f"Order placed: {position}")
        return order
    except BinanceAPIException as e:
        print(f"Order error: {e}")
        return None

def calculate_quantity(price, usdt_amount):
    return round(usdt_amount / price, 2)

def run():
    set_leverage(symbol, leverage)
    while True:
        try:
            df = get_klines(symbol, '15m')
            last_rsi = df['rsi'].iloc[-1]
            price = df['close'].iloc[-1]
            balance = get_balance()
            usdt_trade = balance * 0.5
            qty = calculate_quantity(price, usdt_trade)

            if last_rsi > 50:
                place_order('LONG', qty)
            elif last_rsi < 50:
                place_order('SHORT', qty)
            else:
                print("WAIT - No signal")

            time.sleep(60)
        except Exception as e:
            print(f"Error in main loop: {e}")
            time.sleep(60)

if __name__ == "__main__":
    print(f"Bot started for symbol: {symbol}")
    run()
