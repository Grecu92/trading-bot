
import os
import time
from binance.client import Client
from binance.exceptions import BinanceAPIException

api_key = os.getenv("BINANCE_API_KEY")
api_secret = os.getenv("BINANCE_API_SECRET")
symbol = os.getenv("SYMBOL", "SOLUSDT")
leverage = 10

client = Client(api_key, api_secret)

def get_quantity(symbol, usdt_amount):
    try:
        price = float(client.futures_symbol_ticker(symbol=symbol)['price'])
        qty = round((usdt_amount * leverage) / price, 3)
        return qty
    except Exception as e:
        print(f"Error calculating quantity: {e}")
        return 0

def set_leverage(symbol, leverage):
    try:
        client.futures_change_leverage(symbol=symbol, leverage=leverage)
    except BinanceAPIException as e:
        print(f"Leverage error: {e}")

def place_order(symbol, side, quantity):
    try:
        order = client.futures_create_order(
            symbol=symbol,
            side=side,
            type='MARKET',
            quantity=quantity
        )
        print(f"Order executed: {order}")
    except BinanceAPIException as e:
        print(f"Order error: {e}")

def run_bot():
    print(f"Bot started for symbol: {symbol}")
    set_leverage(symbol, leverage)

    while True:
        try:
            # Simulare semnal LONG - inlocuiește cu logica reală
            signal = "LONG"
            balance = client.futures_account_balance()
            usdt_balance = next(float(x['balance']) for x in balance if x['asset'] == 'USDT')
            trade_amount = usdt_balance * 0.5
            quantity = get_quantity(symbol, trade_amount)

            if quantity <= 0:
                print("Insufficient quantity to trade.")
                time.sleep(60)
                continue

            if signal == "LONG":
                print("LONG signal.")
                place_order(symbol, Client.SIDE_BUY, quantity)
            elif signal == "SHORT":
                print("SHORT signal.")
                place_order(symbol, Client.SIDE_SELL, quantity)

            time.sleep(60)

        except Exception as e:
            print(f"Error in main loop: {e}")
            time.sleep(60)

if __name__ == "__main__":
    run_bot()
