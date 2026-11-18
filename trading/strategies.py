"""Strategies = pure functions: (df, **params) -> signal Series in {-1,0,1}.
No lookahead — signal at bar t uses only data up to t."""
import pandas as pd
import numpy as np

def sma_cross(df, fast=20, slow=60):
    f = df["close"].rolling(fast).mean()
    s = df["close"].rolling(slow).mean()
    sig = pd.Series(0.0, index=df.index)
    sig[f > s] = 1.0
    sig[f < s] = -1.0
    return sig

def rsi_revert(df, period=14, lo=30, hi=70):
    d = df["close"].diff()
    up = d.clip(lower=0).rolling(period).mean()
    dn = -d.clip(upper=0).rolling(period).mean()
    rsi = 100 - 100 / (1 + up / dn.replace(0, np.nan))
    sig = pd.Series(0.0, index=df.index)
    sig[rsi < lo] = 1.0
    sig[rsi > hi] = -1.0
    return sig.ffill().fillna(0.0)

def breakout(df, lookback=20, exit_lookback=10):
    hh = df["high"].rolling(lookback).max().shift(1)
    ll = df["low"].rolling(exit_lookback).min().shift(1)
    sig = pd.Series(0.0, index=df.index)
    long = df["close"] > hh
    flat = df["close"] < ll
    pos = np.where(long, 1.0, np.where(flat, 0.0, np.nan))
    return pd.Series(pos, index=df.index).ffill().fillna(0.0)

REGISTRY = {"sma_cross": sma_cross, "rsi_revert": rsi_revert, "breakout": breakout}
