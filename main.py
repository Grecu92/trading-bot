
import time
from binance.client import Client
from binance.enums import *
import os

api_key = os.getenv("BINANCE_API_KEY")
api_secret = os.getenv("BINANCE_API_SECRET")

client = Client(api_key, api_secret)
symbol = "SOLUSDT"
quantity = 0.5
leverage = 10

client.futures_change_leverage(symbol=symbol, leverage=leverage)

def get_price():
    return float(client.futures_mark_price(symbol=symbol)['markPrice'])

def place_order(order_side):
    order = client.futures_create_order(
        symbol=symbol,
        side=SIDE_BUY if order_side == "BUY" else SIDE_SELL,
        type=ORDER_TYPE_MARKET,
        quantity=quantity
    )
    return order

def close_position(order_side):
    client.futures_create_order(
        symbol=symbol,
        side=SIDE_SELL if order_side == "BUY" else SIDE_BUY,
        type=ORDER_TYPE_MARKET,
        quantity=quantity,
        reduceOnly=True
    )

def run_bot():
    in_position = False
    entry_price = 0
    order_side = None

    while True:
        try:
            price = get_price()
            print(f"Current Price: {price}")

            if not in_position:
                if price > 140:
                    place_order("BUY")
                    entry_price = price
                    order_side = "BUY"
                    in_position = True
                    print(f"Entered LONG at {price}")
                elif price < 130:
                    place_order("SELL")
                    entry_price = price
                    order_side = "SELL"
                    in_position = True
                    print(f"Entered SHORT at {price}")
            else:
                if order_side == "BUY" and price >= entry_price * 1.007:
                    close_position(order_side)
                    print(f"Trailing TP Hit. Exited at {price}")
                    in_position = False
                elif order_side == "SELL" and price <= entry_price * 0.993:
                    close_position(order_side)
                    print(f"Trailing TP Hit. Exited at {price}")
                    in_position = False
                elif abs(price - entry_price) / entry_price >= 0.005:
                    close_position(order_side)
                    print(f"SL Hit. Exited at {price}")
                    in_position = False

            time.sleep(10)
        except Exception as e:
            print(f"Error in main loop: {e}")
            time.sleep(5)

if __name__ == "__main__":
    run_bot()
