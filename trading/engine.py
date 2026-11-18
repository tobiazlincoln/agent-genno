"""Deterministic vectorized backtest engine.

signal: pd.Series of -1/0/+1 (short/flat/long), computed on bar close.
Positions are applied to the NEXT bar (shift(1)) — no lookahead.
Fees: fee_rate * |position change|. Slippage: slippage_bps * |change| on entry/exit.
"""
import numpy as np
import pandas as pd

def run(df, signal, fee_rate=0.0006, slippage_bps=2.0):
    """df: OHLCV DataFrame. signal: Series aligned to df.index in {-1,0,1}.
    Returns dict with equity curve + metrics."""
    ret = df["close"].pct_change().fillna(0.0)
    pos = signal.shift(1).fillna(0.0).clip(-1, 1)
    cost = (fee_rate + slippage_bps / 1e4) * pos.diff().abs().fillna(0.0)
    strat_ret = pos * ret - cost
    equity = (1 + strat_ret).cumprod()
    bench = (1 + ret).cumprod()

    n = len(df)
    yrs = max((df.index[-1] - df.index[0]).total_seconds() / (365.25 * 86400), 1e-9)
    periods_per_year = n / yrs
    dd = equity / equity.cummax() - 1
    sharpe = (strat_ret.mean() / strat_ret.std() * np.sqrt(periods_per_year)
              if strat_ret.std() > 0 else 0.0)

    trades = pos.diff().abs() > 0
    # win rate per round trip: split equity by position flips
    trade_rets = strat_ret[pos != pos.shift(1).fillna(0)]
    wins = (trade_rets > 0).sum()
    profit_factor = abs(strat_ret[strat_ret > 0].sum() / strat_ret[strat_ret < 0].sum()) \
                    if (strat_ret < 0).any() and strat_ret[strat_ret < 0].sum() != 0 else float("inf")

    return {
        "equity": equity, "bench": bench, "pos": pos, "ret": strat_ret,
        "metrics": {
            "total_return": float(equity.iloc[-1] - 1),
            "bench_return": float(bench.iloc[-1] - 1),
            "sharpe": float(sharpe),
            "max_drawdown": float(dd.min()),
            "winrate": float(wins / max(len(trade_rets), 1)),
            "trades": int(trades.sum() // 2),
            "profit_factor": float(profit_factor),
        },
    }

def walk_forward(df, signal_fn, params, split=0.7, **kw):
    """Evaluate signal_fn(params) on train[:70%] and test[70%:] separately.
    Anti-overfitting: a strategy must work OOS to count."""
    i = int(len(df) * split)
    train, test = df.iloc[:i], df.iloc[i:]
    res = {}
    for name, part in (("train", train), ("test", test)):
        sig = signal_fn(part, **params)
        res[name] = run(part, sig, **kw)["metrics"]
    res["params"] = params
    res["pass"] = res["test"]["sharpe"] > 0.5 and res["test"]["max_drawdown"] > -0.35
    return res
