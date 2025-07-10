
import os, asyncio, time, requests, pandas as pd
from binance import AsyncClient

API_KEY    = os.getenv("BINANCE_KEY")
API_SECRET = os.getenv("BINANCE_SECRET")
TG_TOKEN   = os.getenv("TG_TOKEN")
TG_CHAT    = os.getenv("TG_CHAT")
INTERVAL   = "15m"
LIMIT      = 100
DELAY      = 60  # seconds between cycles

async def send(msg):
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": TG_CHAT, "text": msg})

async def get_symbols(client):
    info = await client.futures_exchange_info()
    return [s["symbol"] for s in info["symbols"] if s["quoteAsset"] == "USDT"]

async def fetch_df(client, symbol):
    kl = await client.futures_klines(symbol=symbol, interval=INTERVAL, limit=LIMIT)
    df = pd.DataFrame(kl, columns=["t","o","h","l","c","v","ct","qv","n","tb","tq","ignore"])
    df["c"] = df["c"].astype(float)
    return df[["t","c"]]

async def monitor():
    client = await AsyncClient.create(API_KEY, API_SECRET)
    symbols = await get_symbols(client)
    state = {}
    while True:
        tasks = [fetch_df(client, s) for s in symbols]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        for sym, df in zip(symbols, results):
            if isinstance(df, Exception): continue
            sma20 = df["c"].rolling(20).mean().iloc[-1]
            sma50 = df["c"].rolling(50).mean().iloc[-1]
            price = df["c"].iloc[-1]
            pos = "above" if sma20 > sma50 else "below"
            last = state.get(sym)
            if last and last != pos:
                side = "LONG_CROSS" if pos == "above" else "SHORT_CROSS"
                await send(f"{side}  {sym}  @ {price}")
            state[sym] = pos
        await asyncio.sleep(DELAY)

if __name__ == "__main__":
    asyncio.run(monitor())

