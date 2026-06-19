#!/usr/bin/env python3
"""
Experiment A: tranche_size sweep.
Varies tranche_size across {1000, 2500, 5000}, runs full strategy + lumpsum baseline.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import yaml
import pandas as pd
import logging

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
logger = logging.getLogger("sweep")

from backtest.data.loader import load_prices
from backtest.engine.indicators import annotate_signals
from backtest.engine.strategy import run_strategy
from backtest.engine.baselines import run_lumpsum
from backtest.analyze.metrics import compute_metrics

with open("backtest/config.yaml") as f:
    config_base = yaml.safe_load(f)

df_raw = load_prices("QLD")
df_ann = annotate_signals(df_raw, config_base)

rows = []

for ts in [1000, 2500, 5000]:
    cfg = dict(config_base)
    cfg["tranche_size"] = ts
    r = run_strategy(df_ann, cfg, ablation_overrides={"_name": f"full-ts{ts}"})
    row = {"variant": f"full-ts{ts}", "tranche_size": ts}
    row.update(compute_metrics(r))
    rows.append(row)
    logger.info("full-ts%d: final_eq=%.2f, trades=%d, avg_cash=%.2f%%",
                ts, r.equity.iloc[-1], len(r.trades), row["avg_cash"] * 100)

# Lumpsum baseline
r_ls = run_lumpsum(df_raw, float(config_base["initial_capital"]))
row = {"variant": "lumpsum", "tranche_size": 0}
row.update(compute_metrics(r_ls))
rows.append(row)
logger.info("lumpsum: final_eq=%.2f", r_ls.equity.iloc[-1])

out = "backtest/output/exp_tranche_sweep.csv"
df_out = pd.DataFrame(rows).set_index("variant")
df_out.to_csv(out)
print(f"\nSaved: {out}")
print(df_out.to_string(float_format="%.4f"))
