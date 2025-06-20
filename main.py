import os
import ccxt
import time
import requests

symbol = os.getenv("SYMBOL", "BTCDOMUSDT")
api_key = os.getenv("BINANCE_API_KEY")
api_secret = os.getenv("BINANCE_API_SECRET")
telegram_token = os.getenv("TELEGRAM_TOKEN")
telegram_user_id = os.getenv("TELEGRAM_USER_ID")

exchange = ccxt.binance({
    'apiKey': api_key,
    'secret': api_secret,
    'enableRateLimit': True,
    'options': {
        'defaultType': 'future'
    }
})

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{telegram_token}/sendMessage"
    payload = {
        "chat_id": telegram_user_id,
        "text": message
    }
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print("Telegram error:", e)

def get_rsi(data, period=18):
    deltas = [data[i] - data[i - 1] for i in range(1, len(data))]
    gains = [delta if delta > 0 else 0 for delta in deltas]
    losses = [-delta if delta < 0 else 0 for delta in deltas]
    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period
    rsi = 100 - (100 / (1 + avg_gain / avg_loss)) if avg_loss != 0 else 100
    return rsi

def main_loop():
    while True:
        try:
            ohlcv = exchange.fetch_ohlcv(symbol, timeframe='15m', limit=20)
            closes = [x[4] for x in ohlcv]
            rsi = get_rsi(closes)
            price = closes[-1]
            message = f"{symbol} | RSI(18): {rsi:.2f} | Price: {price}"
            print(message)
            send_telegram_message(message)
            time.sleep(60)
        except Exception as e:
            print("Error:", e)
            send_telegram_message(f"Error: {str(e)}")
            time.sleep(60)

if __name__ == "__main__":
    main_loop()
