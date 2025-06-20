
import time
import requests
from binance.client import Client
from binance.enums import *
import ta
import pandas as pd
import numpy as np
import os

api_key = os.getenv("BINANCE_API_KEY")
api_secret = os.getenv("BINANCE_API_SECRET")
symbol = os.getenv("SYMBOL", "BTCDOMUSDT")
client = Client(api_key, api_secret)

def get_klines(symbol, interval='15m', limit=100):
    klines = client.get_klines(symbol=symbol, interval=interval, limit=limit)
    df = pd.DataFrame(klines, columns=[
        'timestamp', 'open', 'high', 'low', 'close', 'volume',
        'close_time', 'quote_asset_volume', 'number_of_trades',
        'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'
    ])
    df['close'] = pd.to_numeric(df['close'])
    df['volume'] = pd.to_numeric(df['volume'])
    return df

def signal_generator(df):
    df['rsi'] = ta.momentum.RSIIndicator(df['close'], window=18).rsi()
    df['ema21'] = ta.trend.EMAIndicator(df['close'], window=21).ema_indicator()
    macd = ta.trend.MACD(df['close'])
    df['macd_diff'] = macd.macd_diff()

    latest = df.iloc[-1]
    volume_mean = df['volume'].rolling(10).mean().iloc[-1]

    if latest['rsi'] > 50 and latest['macd_diff'] > 0 and latest['close'] > latest['ema21'] and latest['volume'] > volume_mean:
        return "LONG"
    elif latest['rsi'] < 50 and latest['macd_diff'] < 0 and latest['close'] < latest['ema21'] and latest['volume'] > volume_mean:
        return "SHORT"
    else:
        return "WAIT"

def execute_order(signal):
    balance = float(client.futures_account_balance()[1]['balance'])
    qty = round((balance * 0.5 * 10) / float(client.futures_symbol_ticker(symbol=symbol)['price']), 1)
    try:
        if signal == "LONG":
            order = client.futures_create_order(symbol=symbol, side=SIDE_BUY, type=ORDER_TYPE_MARKET, quantity=qty)
        elif signal == "SHORT":
            order = client.futures_create_order(symbol=symbol, side=SIDE_SELL, type=ORDER_TYPE_MARKET, quantity=qty)
    except Exception as e:
        print("Order failed:", str(e))

while True:
    try:
        df = get_klines(symbol)
        signal = signal_generator(df)
        print(f"Signal: {signal}")
        if signal in ["LONG", "SHORT"]:
            execute_order(signal)
        time.sleep(60)
    except Exception as e:
        print("Error in main loop:", str(e))
        time.sleep(60)
