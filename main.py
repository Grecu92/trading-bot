
import time
import pandas as pd
from binance.client import Client
from ta.momentum import RSIIndicator
import requests

# Configurări Binance
API_KEY = 'YOUR_BINANCE_API_KEY'
API_SECRET = 'YOUR_BINANCE_API_SECRET'
client = Client(API_KEY, API_SECRET)

# Configurări Telegram
TOKEN = '7603921163:AAHQ5GFx_QAJ_cEu5LOwZAy0CYtW0REdXdI'
CHAT_ID = '1368917672'

# Simbol și timeframe
symbol = 'BTCDOMUSDT'
interval = Client.KLINE_INTERVAL_15MINUTE

def send_telegram_message(message):
    url = f'https://api.telegram.org/bot{TOKEN}/sendMessage'
    data = {'chat_id': CHAT_ID, 'text': message}
    requests.post(url, data=data)

def fetch_rsi():
    klines = client.get_klines(symbol=symbol, interval=interval, limit=100)
    df = pd.DataFrame(klines, columns=['timestamp', 'open', 'high', 'low', 'close',
                                       'volume', 'close_time', 'quote_asset_volume',
                                       'number_of_trades', 'taker_buy_base_asset_volume',
                                       'taker_buy_quote_asset_volume', 'ignore'])
    df['close'] = df['close'].astype(float)
    rsi = RSIIndicator(close=df['close'], window=18).rsi()
    return rsi.iloc[-2], rsi.iloc[-1]

def main():
    last_signal = None
    while True:
        try:
            prev_rsi, curr_rsi = fetch_rsi()
            signal = None
            if prev_rsi < 50 and curr_rsi > 50:
                signal = 'LONG'
            elif prev_rsi > 50 and curr_rsi < 50:
                signal = 'SHORT'
            if signal and signal != last_signal:
                send_telegram_message(f"{signal} signal (RSI crossed 50)")
                last_signal = signal
        except Exception as e:
            send_telegram_message(f"Error: {e}")
        time.sleep(60)

if __name__ == '__main__':
    main()
