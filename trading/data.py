"""OHLCV data fetch + local cache. Public endpoints only — no API keys."""
import os, time
import ccxt, pandas as pd

CACHE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "storage", "market")

EXCHANGES = {"binance": ccxt.binance, "bybit": ccxt.bybit, "kraken": ccxt.kraken}

def fetch(symbol="BTC/USDT", timeframe="1h", days=365, exchange="binance", cache=True):
    """Return DataFrame indexed by UTC time: open, high, low, close, volume."""
    os.makedirs(CACHE, exist_ok=True)
    fn = f"{exchange}_{symbol.replace('/', '-')}_{timeframe}_{days}d.csv"
    path = os.path.join(CACHE, fn)
    if cache and os.path.exists(path) and time.time() - os.path.getmtime(path) < 3600:
        return pd.read_csv(path, index_col=0, parse_dates=True)

    ex = EXCHANGES[exchange]({"enableRateLimit": True})
    since = ex.milliseconds() - days * 86400_000
    rows, limit = [], 1000
    while True:
        batch = ex.fetch_ohlcv(symbol, timeframe, since=since, limit=limit)
        if not batch:
            break
        rows += batch
        since = batch[-1][0] + 1
        if len(batch) < limit:
            break
    df = pd.DataFrame(rows, columns=["ts", "open", "high", "low", "close", "volume"])
    df["ts"] = pd.to_datetime(df["ts"], unit="ms", utc=True)
    df = df.set_index("ts").drop_duplicates()
    df.to_csv(path)
    return df
