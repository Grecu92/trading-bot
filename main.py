
import os, asyncio, json, logging, time
from datetime import datetime
from aiogram import Bot, Dispatcher
import aiohttp
import math

API_KEY = os.getenv("BINANCE_API_KEY")  # not required for public data
TELEGRAM_TOKEN = os.getenv("TG_TOKEN")  # set in Railway variables
CHAT_ID = os.getenv("TG_CHAT_ID")       # your Telegram chat/group id as string

SYMBOLS = ["BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "XRPUSDT", "ADAUSDT", "DOGEUSDT", "AVAXUSDT", "LINKUSDT", "DOTUSDT", "TRXUSDT", "MATICUSDT", "LTCUSDT", "BCHUSDT", "ETCUSDT", "ATOMUSDT", "XLMUSDT", "HBARUSDT", "ALGOUSDT", "ICPUSDT", "FILUSDT", "SUIUSDT", "SEIUSDT", "APTUSDT", "ARBUSDT", "NEARUSDT", "OPUSDT", "INJUSDT", "PEPEUSDT", "1000SATSUSDT", "WIFUSDT", "JTOUSDT", "RNDRUSDT", "FTMUSDT", "GALAUSDT", "SANDUSDT", "MANAUSDT", "AAVEUSDT", "UNIUSDT", "DYDXUSDT", "ETCUSD_PERP", "XRPUSD_PERP", "SOLUSD_PERP", "ADAUSD_PERP", "DOGEUSD_PERP", "LINKUSD_PERP", "DOTUSD_PERP", "LTCUSD_PERP", "AVAXUSD_PERP", "FILUSD_PERP"]

FAST=20
SLOW=50
INTERVAL='1m'  # closes every minute

logging.basicConfig(level=logging.INFO)
bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher(bot)

async def fetch_klines(session, symbol):
    url = f'https://api.binance.com/api/v3/klines?symbol={symbol}&interval={INTERVAL}&limit={SLOW+1}'
    async with session.get(url) as resp:
        data = await resp.json()
        closes = [float(k[4]) for k in data]
        return closes

def sma(values, n):
    return sum(values[-n:]) / n

async def check_symbol(session, symbol, last_state):
    closes = await fetch_klines(session, symbol)
    if len(closes) < SLOW:
        return last_state
    fast = sma(closes, FAST)
    slow = sma(closes, SLOW)
    prev_fast = sma(closes[:-1], FAST)
    prev_slow = sma(closes[:-1], SLOW)

    cross_up = prev_fast < prev_slow and fast > slow
    cross_down = prev_fast > prev_slow and fast < slow

    state = last_state
    if cross_up and last_state != 'long':
        text = f"🚀 SMA20 crossed ABOVE SMA50 on {symbol} at {closes[-1]:.4f}"
        asyncio.create_task(bot.send_message(CHAT_ID, text))
        state = 'long'
    elif cross_down and last_state != 'short':
        text = f"🔻 SMA20 crossed BELOW SMA50 on {symbol} at {closes[-1]:.4f}"
        asyncio.create_task(bot.send_message(CHAT_ID, text))
        state = 'short'
    return state

async def main_loop():
    states = {s: None for s in SYMBOLS}
    async with aiohttp.ClientSession() as session:
        while True:
            start = time.time()
            tasks = [check_symbol(session, s, states[s]) for s in SYMBOLS]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for s, st in zip(SYMBOLS, results):
                states[s] = st
            elapsed = time.time() - start
            await asyncio.sleep(max(0, 60 - elapsed))

if __name__ == '__main__':
    asyncio.run(main_loop())
