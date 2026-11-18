#!/usr/bin/env python3
"""Backtest CLI:
  run.py fetch BTC/USDT --tf 1h --days 365
  run.py backtest BTC/USDT --tf 1h --days 365 --strategy sma_cross --fast 20 --slow 60
  run.py sweep BTC/USDT --strategy sma_cross --grid fast=10,20,40 slow=40,80,120
"""
import argparse, json, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import data, engine
from strategies import REGISTRY

def _df(a):
    return data.fetch(a.symbol, a.tf, a.days, a.exchange)

def _params(items):
    return {k: int(v) if v.isdigit() else float(v) for k, _, v in (p.partition("=") for p in items)}

def show(r, label=""):
    m = r["metrics"] if "metrics" in r else r
    print(f"{label}return={m['total_return']:+.1%} bench={m['bench_return']:+.1%} "
          f"sharpe={m['sharpe']:.2f} maxDD={m['max_drawdown']:.1%} "
          f"win={m['winrate']:.0%} pf={m['profit_factor']:.2f} trades={m['trades']}")

def cmd_backtest(a):
    df = _df(a)
    p = _params(a.param)
    r = engine.walk_forward(df, REGISTRY[a.strategy], p,
                            fee_rate=a.fee, slippage_bps=a.slip)
    show(r["train"], "train ")
    show(r["test"], "test  ")
    print(f"verdict: {'PASS' if r['pass'] else 'FAIL'} {p}")
    if a.json:
        print(json.dumps(r["metrics"] if "metrics" in r else {k: v for k, v in r.items() if k != "pass"}))

def cmd_sweep(a):
    df = _df(a)
    import itertools
    keys = [g.split("=")[0] for g in a.grid]
    vals = [[int(x) if x.isdigit() else float(x) for x in g.split("=")[1].split(",")] for g in a.grid]
    grids = [dict(zip(keys, combo)) for combo in itertools.product(*vals)]
    rows = []
    for p in grids:
        r = engine.walk_forward(df, REGISTRY[a.strategy], p, fee_rate=a.fee, slippage_bps=a.slip)
        rows.append((r["test"]["sharpe"], p, r["pass"], r["test"]["total_return"]))
    rows.sort(reverse=True)
    for s, p, ok, ret in rows[:15]:
        print(f"sharpe={s:+.2f} ret={ret:+.1%} {'PASS' if ok else '    '} {p}")

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    sp = ap.add_subparsers(dest="cmd", required=True)
    for name in ("fetch", "backtest", "sweep"):
        p = sp.add_parser(name)
        p.add_argument("symbol"); p.add_argument("--tf", default="1h")
        p.add_argument("--days", type=int, default=365); p.add_argument("--exchange", default="binance")
        if name != "fetch":
            p.add_argument("--strategy", required=True, choices=list(REGISTRY))
            p.add_argument("--param", action="append", default=[])
            p.add_argument("--grid", action="append", default=[])
            p.add_argument("--fee", type=float, default=0.0006)
            p.add_argument("--slip", type=float, default=2.0)
            p.add_argument("--json", action="store_true")
    a = ap.parse_args()
    {"fetch": lambda: print(_df(a).tail(3)),
     "backtest": lambda: cmd_backtest(a),
     "sweep": lambda: cmd_sweep(a)}[a.cmd]()
