
import time
from binance.client import Client
from binance.enums import *
import os

api_key = os.getenv("BINANCE_API_KEY")
api_secret = os.getenv("BINANCE_API_SECRET")
symbol = os.getenv("SYMBOL", "SOLUSDT")
leverage = 10

client = Client(api_key, api_secret)

client.futures_change_leverage(symbol=symbol, leverage=leverage)

def get_rsi(symbol, interval='15m', limit=100):
    klines = client.futures_klines(symbol=symbol, interval=interval, limit=limit)
    closes = [float(k[4]) for k in klines]
    deltas = [closes[i] - closes[i - 1] for i in range(1, len(closes))]
    gains = [delta if delta > 0 else 0 for delta in deltas]
    losses = [-delta if delta < 0 else 0 for delta in deltas]
    avg_gain = sum(gains[-14:]) / 14
    avg_loss = sum(losses[-14:]) / 14
    rs = avg_gain / avg_loss if avg_loss != 0 else 0
    rsi = 100 - (100 / (1 + rs))
    return rsi

def get_balance():
    balance_info = client.futures_account_balance()
    usdt_balance = [b for b in balance_info if b['asset'] == 'USDT'][0]
    return float(usdt_balance['balance']) / 2

def place_order(side, quantity):
    try:
        quantity = round(quantity, 3)
        order = client.futures_create_order(
            symbol=symbol,
            side=side,
            type=FUTURE_ORDER_TYPE_MARKET,
            quantity=quantity
        )
        print(f"Order placed: {side}, Quantity: {quantity}")
    except Exception as e:
        print("Order error:", e)

def main():
    print(f"Bot started for symbol: {symbol}")
    while True:
        try:
            rsi = get_rsi(symbol)
            print(f"RSI: {rsi}")
            usdt_balance = get_balance()
            price = float(client.futures_mark_price(symbol=symbol)["markPrice"])
            quantity = (usdt_balance * leverage) / price
            quantity = round(quantity, 3)

            if rsi > 50:
                print("LONG signal.")
                place_order(SIDE_BUY, quantity)
            elif rsi < 50:
                print("SHORT signal.")
                place_order(SIDE_SELL, quantity)

            time.sleep(60)
        except Exception as e:
            print("Error in main loop:", e)
            time.sleep(60)

if __name__ == "__main__":
    main()
