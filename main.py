import os
import time
import requests
from binance.client import Client
from binance.enums import *
import ta
import pandas as pd
from datetime import datetime
from telegram import Bot

# Environment variables
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_USER_ID = os.getenv('TELEGRAM_USER_ID')
BINANCE_API_KEY = os.getenv('BINANCE_API_KEY')
BINANCE_API_SECRET = os.getenv('BINANCE_API_SECRET')
SYMBOL = os.getenv('SYMBOL', 'BTCDOMUSDT')
INTERVAL = Client.KLINE_INTERVAL_15MINUTE

# Init clients
client = Client(BINANCE_API_KEY, BINANCE_API_SECRET)
bot = Bot(token=TELEGRAM_TOKEN)

# Indicator settings
RSI_PERIOD = 18
EMA_PERIOD = 21

def get_klines(symbol, interval, limit=100):
    try:
        klines = client.get_klines(symbol=symbol, interval=interval, limit=limit)
        df = pd.DataFrame(klines, columns=[
            'timestamp', 'open', 'high', 'low', 'close', 'volume',
            'close_time', 'quote_asset_volume', 'number_of_trades',
            'taker_buy_base_volume', 'taker_buy_quote_volume', 'ignore'
        ])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df.set_index('timestamp', inplace=True)
        df = df.astype(float)
        return df
    except Exception as e:
        print(f"Kline error: {e}")
        return None

def calculate_indicators(df):
    df['rsi'] = ta.momentum.RSIIndicator(df['close'], RSI_PERIOD).rsi()
    df['ema'] = ta.trend.EMAIndicator(df['close'], EMA_PERIOD).ema_indicator()
    df['macd_diff'] = ta.trend.macd_diff(df['close'])
    df['volume_ma'] = df['volume'].rolling(20).mean()
    return df

def send_alert(text):
    try:
        bot.send_message(chat_id=TELEGRAM_USER_ID, text=text)
    except Exception as e:
        print(f"Telegram error: {e}")

def main_loop():
    last_signal = None
    while True:
        df = get_klines(SYMBOL, INTERVAL)
        if df is not None:
            df = calculate_indicators(df)
            rsi = df['rsi'].iloc[-1]
            macd = df['macd_diff'].iloc[-1]
            volume = df['volume'].iloc[-1]
            volume_avg = df['volume_ma'].iloc[-1]
            close = df['close'].iloc[-1]
            ema = df['ema'].iloc[-1]

            # Decision logic
            if rsi > 50 and macd > 0 and volume > volume_avg and close > ema and last_signal != 'LONG':
                send_alert(f"{SYMBOL} | LONG | RSI(18): {rsi:.2f} | Price: {close}")
                last_signal = 'LONG'
            elif rsi < 50 and macd < 0 and volume > volume_avg and close < ema and last_signal != 'SHORT':
                send_alert(f"{SYMBOL} | SHORT | RSI(18): {rsi:.2f} | Price: {close}")
                last_signal = 'SHORT'
            else:
                print(f"No signal | RSI: {rsi:.2f} | Price: {close}")
        time.sleep(60)

if __name__ == "__main__":
    main_loop()
