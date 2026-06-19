"""
Sanity checks: daily buy limit, equity preservation, lumpsum cross-check, cash/shares non-negative.
Runs on all variants from the full pipeline.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import pandas as pd
import yaml

from backtest.data.loader import load_prices
from backtest.engine.indicators import annotate_signals
from backtest.ablation import run_all

with open("backtest/config.yaml") as f:
    config = yaml.safe_load(f)

df_raw = load_prices("QLD")
df_ann = annotate_signals(df_raw, config)

# Run ALL variants
equities = run_all(df_ann, config, baselines_df=df_raw)

violations = []

# For each variant, check invariants
for name, eq in equities.items():
    # Load result from disk
    import importlib
    if name in ("lumpsum", "dca100"):
        from backtest.engine.baselines import run_lumpsum, run_dca
        cap = float(config["initial_capital"])
        if name == "lumpsum":
            r = run_lumpsum(df_raw, cap)
        else:
            r = run_dca(df_raw, cap, n_slices=100)
    else:
        overrides = {}
        if name == "no-200ma": overrides = {"disable_ma200_sell": True}
        elif name == "no-ath-buy": overrides = {"disable_ath_buy": True}
        elif name == "no-prevlow-buy": overrides = {"disable_prevlow_buy": True}
        elif name == "no-takeprofit": overrides = {"disable_takeprofit": True}
        elif name == "only-ath": overrides = {"disable_prevlow_buy": True, "disable_ma200_sell": True, "disable_takeprofit": True}
        elif name == "only-prevlow": overrides = {"disable_ath_buy": True, "disable_ma200_sell": True, "disable_takeprofit": True}
        elif name == "buy-only-no-sell": overrides = {"disable_ma200_sell": True, "disable_takeprofit": True}
        overrides["_name"] = name
        from backtest.engine.strategy import run_strategy
        r = run_strategy(df_ann, config, ablation_overrides=overrides)

    # 1. Non-negative cash and shares
    if (r.cash < -0.01).any():
        violations.append(f"[{name}] Negative cash found (min={r.cash.min():.2f})")
    if (r.shares < 0).any():
        violations.append(f"[{name}] Negative shares found")

    # 2. Equity preservation: eq == cash + shares*close (sampled weekly)
    sampled = df_ann.iloc[::5]  # every 5th row to keep check fast
    for dt in sampled.index:
        idx = df_ann.index.get_loc(dt)
        eq_val = r.equity.iloc[idx]
        c = r.cash.iloc[idx]
        sh = r.shares.iloc[idx]
        close = df_ann.loc[dt, "close"]
        computed = round(c + sh * close, 2)
        if abs(eq_val - computed) > 0.05:
            violations.append(f"[{name}] Equity mismatch at {dt.date()}: {eq_val} vs {computed}")

    # 3. Daily buy limit: sum of buy amounts per day <= $1,000 (strategy variants only)
    if name not in ("lumpsum", "dca100") and len(r.trades) > 0 and "side" in r.trades.columns:
        buys = r.trades[r.trades["side"] == "buy"].copy()
        if len(buys) > 0:
            buys["buy_value"] = buys["shares"] * buys["price"]
            daily = buys.groupby(buys["date"].dt.date)["buy_value"].sum()
            exceeded = daily[daily > 1000 + 1]
            for d, val in exceeded.items():
                violations.append(f"[{name}] Daily buy limit {val:.0f} on {d}")

    # 4. Lumpsum cross-check
    if name == "lumpsum":
        first_close = float(df_raw["close"].iloc[0])
        cap = float(config["initial_capital"])
        expected_shares = int(cap / first_close)
        expected_cash = cap - expected_shares * first_close
        last_close = float(df_raw["close"].iloc[-1])
        expected_final = round(expected_cash + expected_shares * last_close, 2)
        actual_final = round(r.equity.iloc[-1], 2)
        if abs(expected_final - actual_final) > 0.10:
            violations.append(f"[lumpsum] Cross-check failed: expected {expected_final}, got {actual_final}")
        else:
            print(f"  [lumpsum] Cross-check OK: {actual_final} (expected ~{expected_final})")

print(f"\n=== Sanity results ===")
if violations:
    for v in violations:
        print(f"  FAIL: {v}")
    sys.exit(1)
else:
    print("  ALL sanity checks PASSED")
