
import os
import time
from binance.client import Client
from binance.enums import *
from binance.exceptions import BinanceAPIException

api_key = os.getenv('BINANCE_API_KEY')
api_secret = os.getenv('BINANCE_API_SECRET')
symbol = os.getenv('SYMBOL', 'SOLUSDT')
client = Client(api_key, api_secret)

quantity_percentage = 0.5
leverage = 10
trailing_start = 0.003  # 0.3%
trailing_stop = 0.002   # 0.2%
breakeven_candles = 2
sl_percentage = 0.005  # 0.5%

def get_position():
    positions = client.futures_position_information(symbol=symbol)
    for pos in positions:
        if float(pos['positionAmt']) != 0:
            return pos
    return None

def close_position(position):
    side = SIDE_SELL if float(position['positionAmt']) > 0 else SIDE_BUY
    quantity = abs(float(position['positionAmt']))
    client.futures_create_order(
        symbol=symbol,
        side=side,
        type=ORDER_TYPE_MARKET,
        quantity=quantity
    )

def set_leverage(symbol, leverage):
    try:
        client.futures_change_leverage(symbol=symbol, leverage=leverage)
    except BinanceAPIException as e:
        print("Leverage error:", e)

def enter_position(side):
    balance = client.futures_account_balance()
    usdt_balance = float([x['balance'] for x in balance if x['asset'] == 'USDT'][0])
    price = float(client.futures_mark_price(symbol=symbol)['markPrice'])
    quantity = round((usdt_balance * quantity_percentage * leverage) / price, 2)
    set_leverage(symbol, leverage)
    client.futures_create_order(symbol=symbol, side=side, type=ORDER_TYPE_MARKET, quantity=quantity)
    return price, quantity

def monitor_position(entry_price, side):
    max_price = entry_price
    min_price = entry_price
    candles_waited = 0

    while True:
        price = float(client.futures_mark_price(symbol=symbol)['markPrice'])
        if side == SIDE_BUY:
            max_price = max(max_price, price)
            if price >= entry_price * (1 + trailing_start):
                if price <= max_price * (1 - trailing_stop):
                    print("Trailing stop hit. Closing LONG.")
                    close_position(get_position())
                    break
            elif candles_waited >= breakeven_candles:
                print("Closing LONG after timeout.")
                close_position(get_position())
                break
        elif side == SIDE_SELL:
            min_price = min(min_price, price)
            if price <= entry_price * (1 - trailing_start):
                if price >= min_price * (1 + trailing_stop):
                    print("Trailing stop hit. Closing SHORT.")
                    close_position(get_position())
                    break
            elif candles_waited >= breakeven_candles:
                print("Closing SHORT after timeout.")
                close_position(get_position())
                break

        if abs(price - entry_price) >= entry_price * sl_percentage:
            print("Stop loss hit. Closing position.")
            close_position(get_position())
            break

        candles_waited += 1
        time.sleep(60)

def main_loop():
    print("Bot started for symbol:", symbol)
    while True:
        try:
            klines = client.futures_klines(symbol=symbol, interval=Client.KLINE_INTERVAL_15MINUTE, limit=2)
            rsi_values = [float(k[4]) for k in klines]
            if rsi_values[-1] > rsi_values[-2] and rsi_values[-1] > 50:
                print("LONG signal.")
                entry_price, qty = enter_position(SIDE_BUY)
                monitor_position(entry_price, SIDE_BUY)
            elif rsi_values[-1] < rsi_values[-2] and rsi_values[-1] < 50:
                print("SHORT signal.")
                entry_price, qty = enter_position(SIDE_SELL)
                monitor_position(entry_price, SIDE_SELL)
        except BinanceAPIException as e:
            print("Error in main loop:", e)
        time.sleep(30)

if __name__ == "__main__":
    main_loop()
