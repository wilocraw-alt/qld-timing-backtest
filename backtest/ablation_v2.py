"""
V2 ablation matrix + run_all_v2 orchestrator for 15-year QLD backtest.
"""
import os
import logging

import pandas as pd

from backtest.engine.strategy_v2 import run_strategy_v2
from backtest.engine.strategy import run_strategy as run_strategy_v1
from backtest.engine.baselines import run_lumpsum, run_dca
from backtest.analyze.metrics import compute_metrics

logger = logging.getLogger(__name__)

ABLATIONS_V2 = {
    "v2-full": {},
    "no-core": {"disable_core": True},
    "core-50": {"_core_ratio_override": 0.50},
    "no-overheat": {"disable_overheat": True},
    "no-dd-exit": {"disable_dd_exit": True},
    "instant-sell": {"instant_sell": True},
    "slow-reentry": {"slow_reentry": True},
    "lump-cashout": {"lump_cashout": True},
}


def run_v1_full(df_annotated_v1, params_v1):
    """Run v1 full strategy on the same 15-year period for reference."""
    config = {
        "initial_capital": float(params_v1.get("initial_capital", 10000)),
        "daily_buy_limit": 1000000000000,
        "tranche_size": 1000,
        "pending_expiry_days": 5,
        "rearm_on_new_pivot": True,
        "pivot_lookback": 10,
        "pivot_min_move": 0.05,
        "strategy": {"n": 5, "m": 50, "a": 10, "b": 15, "c": 20, "d": 40, "e": 10, "f": 20},
    }
    r = run_strategy_v1(df_annotated_v1, config, ablation_overrides={"_name": "v1-full"})
    return r


def run_all_v2(df_annotated_v2, params_v2, df_raw, params_v1=None, df_annotated_v1=None):
    """
    Run all v2 ablation variants + baselines + v1 reference.

    Parameters
    ----------
    df_annotated_v2 : pd.DataFrame (with B2 signal columns)
    params_v2 : dict (with 'v2' sub-dict)
    df_raw : pd.DataFrame (raw prices for baselines)
    params_v1 : dict or None (for v1 reference)
    df_annotated_v1 : pd.DataFrame or None (v1 signals)

    Returns
    -------
    dict[str, pd.Series]
    """
    results_rows = []
    equities = {}

    for name, overrides in ABLATIONS_V2.items():
        overrides = dict(overrides)
        overrides["_name"] = name
        cfg = dict(params_v2)
        cfg["v2"] = dict(params_v2.get("v2", {}))
        cr_override = overrides.pop("_core_ratio_override", None)
        if cr_override is not None:
            cfg["v2"]["core_ratio"] = cr_override

        r = run_strategy_v2(df_annotated_v2, cfg, ablation_overrides=overrides)
        equities[name] = r.equity
        row = {"variant": name}
        row.update(compute_metrics(r))
        results_rows.append(row)
        logger.info("  %s: %d trades, final_eq=%.2f", name, len(r.trades), r.equity.iloc[-1])

    cap = float(params_v2["initial_capital"])

    r_ls = run_lumpsum(df_raw, cap)
    equities["lumpsum"] = r_ls.equity
    row = {"variant": "lumpsum"}
    row.update(compute_metrics(r_ls))
    results_rows.append(row)

    r_dca = run_dca(df_raw, cap, n_slices=100)
    equities["dca100"] = r_dca.equity
    row = {"variant": "dca100"}
    row.update(compute_metrics(r_dca))
    results_rows.append(row)

    lumpsum_final = r_ls.equity.iloc[-1]

    if params_v1 is not None and df_annotated_v1 is not None:
        r_v1 = run_v1_full(df_annotated_v1, params_v1)
        equities["v1-full"] = r_v1.equity
        row = {"variant": "v1-full"}
        row.update(compute_metrics(r_v1))
        results_rows.append(row)

    out_dir = "backtest/output"
    os.makedirs(out_dir, exist_ok=True)

    df_out = pd.DataFrame(results_rows).set_index("variant")
    df_out["excess_vs_lumpsum"] = df_out["final_value"] / lumpsum_final - 1.0
    path = os.path.join(out_dir, "results_v2.csv")
    df_out.to_csv(path)
    logger.info("Results saved to %s", path)

    return equities
