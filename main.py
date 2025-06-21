
import time
import os
from binance.client import Client
from binance.exceptions import BinanceAPIException
from binance.enums import *

# Config
API_KEY = os.getenv("BINANCE_API_KEY")
API_SECRET = os.getenv("BINANCE_API_SECRET")
symbol = os.getenv("SYMBOL", "SOLUSDT")
leverage = 10

client = Client(API_KEY, API_SECRET)

# Set leverage
try:
    client.futures_change_leverage(symbol=symbol, leverage=leverage)
except BinanceAPIException as e:
    print(f"Leverage error: {e}")

def get_quantity(usdt_balance, price):
    qty = round((usdt_balance * 0.8 * leverage) / price, 3)  # 80% din capital, leverage x10
    return qty

def get_balance():
    balance = client.futures_account_balance()
    usdt_balance = float([x for x in balance if x["asset"] == "USDT"][0]["balance"])
    return usdt_balance

def get_price():
    price_data = client.futures_symbol_ticker(symbol=symbol)
    return float(price_data["price"])

def place_order(side, quantity):
    try:
        order = client.futures_create_order(
            symbol=symbol,
            side=side,
            type=ORDER_TYPE_MARKET,
            quantity=quantity
        )
        print(f"Order executed: {side} {quantity}")
        return order
    except BinanceAPIException as e:
        print(f"Order error: {e}")
        return None

# Trailing stop logic
def manage_trade(order, entry_price):
    activated = False
    while True:
        price = get_price()
        pnl = (price - entry_price) / entry_price * 100 if order["side"] == "BUY" else (entry_price - price) / entry_price * 100
        if pnl >= 0.3 and not activated:
            print("Trailing Stop Activated")
            activated = True
        if activated and pnl <= 0.1:
            print("Exiting with Trailing Stop")
            side = SIDE_SELL if order["side"] == "BUY" else SIDE_BUY
            place_order(side, float(order["origQty"]))
            break
        time.sleep(10)

while True:
    try:
        price = get_price()
        usdt_balance = get_balance()
        quantity = get_quantity(usdt_balance, price)
        if quantity <= 0:
            print("Insufficient quantity to trade.")
            time.sleep(60)
            continue
        print(f"Bot started for symbol: {symbol}")
        # Simplă strategie RSI dummy pentru test (poți înlocui)
        order = place_order(SIDE_BUY, quantity)
        if order:
            manage_trade(order, price)
        time.sleep(60)
    except Exception as e:
        print(f"Error in main loop: {e}")
        time.sleep(60)
