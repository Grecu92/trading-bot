import os
import time
import requests
import pandas as pd
from binance.client import Client
from binance.enums import *
from telegram import Bot
import ta

# Configurare variabile de mediu
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_USER_ID = os.getenv('TELEGRAM_USER_ID')
BINANCE_API_KEY = os.getenv('BINANCE_API_KEY')
BINANCE_API_SECRET = os.getenv('BINANCE_API_SECRET')
SYMBOL = os.getenv('SYMBOL', 'BTCDOMUSDT')
INTERVAL = Client.KLINE_INTERVAL_15MINUTE

client = Client(api_key=BINANCE_API_KEY, api_secret=BINANCE_API_SECRET)
bot = Bot(token=TELEGRAM_TOKEN)

RSI_PERIOD = 18
EMA_PERIOD = 21

position = None
entry_price = None
max_price = None
min_price = None

def send_alert(msg):
    try:
        bot.send_message(chat_id=TELEGRAM_USER_ID, text=msg)
    except Exception as e:
        print(f"Telegram error: {e}")

def get_klines(symbol, interval, limit=100):
    klines = client.futures_klines(symbol=symbol, interval=interval, limit=limit)
    df = pd.DataFrame(klines, columns=[
        'timestamp', 'open', 'high', 'low', 'close', 'volume',
        'close_time', 'quote_asset_volume', 'number_of_trades',
        'taker_buy_base_volume', 'taker_buy_quote_volume', 'ignore'
    ])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    df.set_index('timestamp', inplace=True)
    df = df.astype(float)
    return df

def calculate_indicators(df):
    df['rsi'] = ta.momentum.RSIIndicator(df['close'], RSI_PERIOD).rsi()
    df['ema'] = ta.trend.EMAIndicator(df['close'], EMA_PERIOD).ema_indicator()
    df['macd_diff'] = ta.trend.macd_diff(df['close'])
    df['volume_ma'] = df['volume'].rolling(20).mean()
    return df

def open_position(side, quantity, price):
    global entry_price, max_price, min_price, position
    try:
        client.futures_create_order(symbol=SYMBOL, side=side, type=ORDER_TYPE_MARKET, quantity=quantity)
        position = 'LONG' if side == SIDE_BUY else 'SHORT'
        entry_price = price
        max_price = price
        min_price = price
        send_alert(f"{position} order opened at {price}")
    except Exception as e:
        send_alert(f"Order error: {e}")

def close_position(position_side, quantity, current_price, reason):
    global position, entry_price
    try:
        close_side = SIDE_SELL if position_side == 'LONG' else SIDE_BUY
        client.futures_create_order(symbol=SYMBOL, side=close_side, type=ORDER_TYPE_MARKET, quantity=quantity)
        send_alert(f"{position_side} position closed at {current_price} due to {reason}")
        position = None
        entry_price = None
    except Exception as e:
        send_alert(f"Close error: {e}")

def main():
    global position, entry_price, max_price, min_price

    while True:
        try:
            df = get_klines(SYMBOL, INTERVAL)
            df = calculate_indicators(df)
            rsi = df['rsi'].iloc[-1]
            close = df['close'].iloc[-1]
            ema = df['ema'].iloc[-1]
            macd = df['macd_diff'].iloc[-1]
            volume = df['volume'].iloc[-1]
            vol_ma = df['volume_ma'].iloc[-1]

            balance = float(client.futures_account_balance()[0]['balance'])
            qty = round((balance * 0.5 * 10) / close, 3)

            # Entry logic
            if position is None:
                if rsi > 50 and macd > 0 and close > ema and volume > vol_ma:
                    open_position(SIDE_BUY, qty, close)
                elif rsi < 50 and macd < 0 and close < ema and volume > vol_ma:
                    open_position(SIDE_SELL, qty, close)

            # Trailing stop logic
            elif position == 'LONG':
                max_price = max(max_price, close)
                if close <= entry_price * 0.995:
                    close_position(position, qty, close, "stop loss")
                elif max_price >= entry_price * 1.003 and close <= max_price * 0.998:
                    close_position(position, qty, close, "trailing stop")
                elif df['close'].iloc[-3] < entry_price * 1.007 and df['close'].iloc[-1] < entry_price:
                    close_position(position, qty, close, "breakeven")

            elif position == 'SHORT':
                min_price = min(min_price, close)
                if close >= entry_price * 1.005:
                    close_position(position, qty, close, "stop loss")
                elif min_price <= entry_price * 0.997 and close >= min_price * 1.002:
                    close_position(position, qty, close, "trailing stop")
                elif df['close'].iloc[-3] > entry_price * 0.993 and df['close'].iloc[-1] > entry_price:
                    close_position(position, qty, close, "breakeven")

        except Exception as e:
            print(f"Main error: {e}")
        time.sleep(60)

if __name__ == "__main__":
    main()
