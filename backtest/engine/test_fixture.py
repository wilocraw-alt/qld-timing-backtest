# coding: utf-8
"""
Synthetic fixture test for strategy.py + portfolio.py.
Simulates a full market cycle: peak -> decline -> buy T1/T2 -> bounce -> buy T3/T4 -> recovery -> TP sell.
Validates invariants: non-negative cash/shares, daily buy <= $1,000, tranche non-duplication.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import pandas as pd
import numpy as np
from backtest.engine.strategy import run_strategy

params = {
    "initial_capital": 10000,
    "daily_buy_limit": 1000,
    "tranche_size": 1000,
    "pending_expiry_days": 5,
    "rearm_on_new_pivot": True,
    "pivot_lookback": 10,
    "pivot_min_move": 0.05,
    "strategy": {"n": 3, "m": 50, "a": 10, "b": 15, "c": 20, "d": 40, "e": 10, "f": 20},
}

dates = pd.bdate_range("2024-01-01", periods=14, freq="D")
np.random.seed(42)

df = pd.DataFrame(index=dates)
df["close"] = [
    100.00,  # d0  peak
    98.00,   # d1
    95.00,   # d2
    89.00,   # d3  trig_t1 (<=90)
    85.00,   # d4  trig_t2 (<=85) + streak=3
    84.00,   # d5  more decline
    86.00,   # d6
    90.00,   # d7
    93.00,   # d8  confirmed_low established at 80
    96.00,   # d9  trig_t3 (>=88)
    100.00,  # d10 back to peak, new_ath
    108.00,  # d11 new_ath, trig_t4 (>=96)
    120.00,  # d12 tp1 (+20% from avg)
    130.00,  # d13 tp2 (+40%)
]

df["ma200"] = 100.0
df["below_ma200_streak"] = [0, 0, 1, 2, 3, 4, 4, 3, 2, 1, 0, 0, 0, 0]
df["ath"] = 100.0

df["confirmed_low"] = np.nan
df.loc[dates[8]:, "confirmed_low"] = 80.0

df["trig_t1"] = False
df.loc[dates[3]:dates[6], "trig_t1"] = True

df["trig_t2"] = False
df.loc[dates[4]:dates[6], "trig_t2"] = True

df["trig_t3"] = False
df.loc[dates[9]:dates[9], "trig_t3"] = True

df["trig_t4"] = False
df.loc[dates[10]:dates[11], "trig_t4"] = True

df["new_ath"] = False
df.loc[dates[0], "new_ath"] = True
df.loc[dates[10]:dates[11], "new_ath"] = True

df["new_low"] = False
df.loc[dates[8], "new_low"] = True

print("=== Synthetic fixture data ===")
print(df.to_string())
print()

result = run_strategy(df, params, ablation_overrides=None)

print("=== Trades ===")
print(result.trades.to_string())
print()

trades = result.trades
assert len(trades) > 0, "Should have at least one trade"

violations = []
for i in range(len(result.equity)):
    date = result.equity.index[i]
    eq = result.equity.iloc[i]
    c = result.cash.iloc[i]
    sh = result.shares.iloc[i]
    close = df.loc[date, "close"]
    computed = round(c + sh * close, 2)
    if abs(eq - computed) > 0.02:
        violations.append(f"Equity mismatch at {date.date()}: {eq} vs {computed}")
    if c < -0.01:
        violations.append(f"Negative cash at {date.date()}: {c}")
    if sh < 0:
        violations.append(f"Negative shares at {date.date()}: {sh}")

daily_buys = {}
for _, t in trades[trades["side"] == "buy"].iterrows():
    d = t["date"].date()
    daily_buys[d] = daily_buys.get(d, 0) + t["shares"] * t["price"]
for d, amt in daily_buys.items():
    if amt > 1000 + 1:
        violations.append(f"Daily buy limit exceeded on {d}: {amt:.2f}")

tranche_buy_dates = {}
for _, t in trades[trades["side"] == "buy"].iterrows():
    reason = t["reason"]
    d = t["date"].date()
    if reason in tranche_buy_dates:
        violations.append(f"Duplicate {reason} buy on {d} (already bought on {tranche_buy_dates[reason]})")
    else:
        tranche_buy_dates[reason] = d

# Latch regression: no repeated sell in same episode
sell_trades = trades[trades["side"] == "sell"]
ma200_dates = sorted(sell_trades[sell_trades["reason"] == "ma200"]["date"])
tp1_dates = sorted(sell_trades[sell_trades["reason"] == "tp1"]["date"])
tp2_dates = sorted(sell_trades[sell_trades["reason"] == "tp2"]["date"])

for i in range(1, len(ma200_dates)):
    gap = (ma200_dates[i] - ma200_dates[i-1]).days
    if gap <= 1:
        violations.append(f"MA200 sell repeated on consecutive days: {ma200_dates[i-1].date()} -> {ma200_dates[i].date()}")

if len(tp1_dates) > 1:
    violations.append(f"TP1 fired {len(tp1_dates)} times (max 1 per cycle): {[d.date() for d in tp1_dates]}")

if len(tp2_dates) > 1:
    violations.append(f"TP2 fired {len(tp2_dates)} times (max 1 per cycle): {[d.date() for d in tp2_dates]}")

print("=== Validation results ===")
if violations:
    for v in violations:
        print(f"  FAIL: {v}")
else:
    print("  All checks passed: equity preserved, cash>=0, shares>=0, daily<=$1k, no duplicate tranche buys, no repeated sells")

print()
print(f"Final: cash={result.cash.iloc[-1]:.2f}, shares={result.shares.iloc[-1]}, equity={result.equity.iloc[-1]:.2f}")
print(f"Total trades: {len(trades)} ({len(trades[trades['side']=='buy'])} buys, {len(trades[trades['side']=='sell'])} sells)")

assert not violations, f"Fixtures failed: {violations}"
print("=== FULL STRATEGY FIXTURE PASSED ===")
print()

# Ablation test
ablations = [
    ("no-ma200", {"disable_ma200_sell": True}),
    ("no-ath", {"disable_ath_buy": True}),
    ("no-prevlow", {"disable_prevlow_buy": True}),
    ("no-tp", {"disable_takeprofit": True}),
]
for name, overrides in ablations:
    r = run_strategy(df, params, ablation_overrides=overrides)
    eq_series = r.equity
    assert (eq_series >= 0).all(), f"{name}: negative equity"
    assert (r.cash >= -0.01).all(), f"{name}: negative cash"
    assert (r.shares >= 0).all(), f"{name}: negative shares"
    print(f"  ablation={name}: {len(r.trades)} trades, final_eq={eq_series.iloc[-1]:.2f}")

print("=== ALL ABLATION FIXTURES PASSED ===")
