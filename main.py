
import time
from binance.client import Client
from binance.enums import *
from binance.exceptions import BinanceAPIException
import os

api_key = os.getenv("BINANCE_API_KEY")
api_secret = os.getenv("BINANCE_API_SECRET")
symbol = os.getenv("SYMBOL", "SOLUSDT")
leverage = 10

client = Client(api_key, api_secret)
client.futures_change_leverage(symbol=symbol, leverage=leverage)

def get_balance():
    balance = client.futures_account_balance()
    usdt_balance = next((item for item in balance if item["asset"] == "USDT"), None)
    return float(usdt_balance["balance"]) if usdt_balance else 0

def get_price():
    return float(client.futures_symbol_ticker(symbol=symbol)["price"])

def calculate_quantity(usdt_balance, price):
    trade_value = usdt_balance * 0.8  # 80% din capital
    quantity = (trade_value * leverage) / price
    step_size = 0.01  # Ajustează în funcție de simbol dacă este nevoie
    return round(quantity - (quantity % step_size), 2)

while True:
    try:
        balance = get_balance()
        price = get_price()
        quantity = calculate_quantity(balance, price)

        if quantity <= 0:
            print("Insufficient quantity to trade.")
            time.sleep(10)
            continue

        # Exemplu de tranzacție LONG
        print("Bot started for symbol:", symbol)
        print("LONG signal.")
        client.futures_create_order(
            symbol=symbol,
            side=SIDE_BUY,
            type=ORDER_TYPE_MARKET,
            quantity=quantity
        )
        # Trailing Stop configurabil
        client.futures_create_order(
            symbol=symbol,
            side=SIDE_SELL,
            type=ORDER_TYPE_TRAILING_STOP_MARKET,
            quantity=quantity,
            callbackRate=1.0,  # trailing stop de 1%
            reduceOnly=True
        )

        time.sleep(60)  # Așteaptă 1 minut înainte de următorul ciclu

    except BinanceAPIException as e:
        print(f"Order error: {e}")
        time.sleep(10)
    except Exception as ex:
        print(f"Unexpected error: {ex}")
        time.sleep(10)
