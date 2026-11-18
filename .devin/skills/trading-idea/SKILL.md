---
name: trading-idea
description: Generate, backtest, and evaluate trading strategy hypotheses. Deterministic engine runs the math; the agent proposes ideas and interprets verified metrics.
triggers:
  - user
  - model
---

# Trading Idea Skill

Backtest engine: `trading/` (run with `pipeline/.venv/bin/python3`).
Market data cached in `storage/market/` — free ccxt public endpoints, no keys.

## Workflow

### 1. Propose a hypothesis
State it explicitly: indicator, entry/exit logic, timeframe, symbol, why it
might have edge. Write it in `trading/experiments/<name>.md` BEFORE testing.

### 2. Backtest
```bash
pipeline/.venv/bin/python3 trading/run.py backtest <SYMBOL> --tf <TF> \
  --days N --strategy <sma_cross|rsi_revert|breakout> \
  --param k=v [--param k=v]
```
Or sweep a parameter grid:
```bash
pipeline/.venv/bin/python3 trading/run.py sweep <SYMBOL> --tf <TF> \
  --days N --strategy <name> --grid k=v1,v2,v3 [--grid k2=...]
```

### 3. Verdict rules (enforced by engine)
- Walk-forward split 70/30 — metrics reported for train AND test.
- PASS requires: test sharpe > 0.5 AND test maxDD > -35%.
- A strategy that only works on train is overfit — say so, don't dress it up.

### 4. Interpret & iterate
- Report the real numbers, not a story. If FAIL, diagnose: too many trades
  (fee bleed)? Wrong regime (chop vs trend)? Parameter fragility?
- To try a new strategy type, add a pure function to `trading/strategies.py`
  registry — signal in {-1,0,1}, no lookahead (bar t uses data up to t only).

## Hard rules
- GLM/agent NEVER executes trades and never touches exchange keys. This
  pipeline is research-only; execution is out of scope.
- Never claim a strategy "works" — cite the test-set metrics.
- One hypothesis per experiment file; don't silently change params mid-report.
