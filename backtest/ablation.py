"""
Ablation matrix and run_all orchestrator for QLD backtest.
"""
import os
import logging

import pandas as pd

from backtest.engine.strategy import run_strategy
from backtest.engine.baselines import run_lumpsum, run_dca
from backtest.analyze.metrics import compute_metrics

logger = logging.getLogger(__name__)

ABLATIONS = {
    "full": {},
    "no-200ma": {"disable_ma200_sell": True},
    "no-ath-buy": {"disable_ath_buy": True},
    "no-prevlow-buy": {"disable_prevlow_buy": True},
    "no-takeprofit": {"disable_takeprofit": True},
    "only-ath": {"disable_prevlow_buy": True, "disable_ma200_sell": True, "disable_takeprofit": True},
    "only-prevlow": {"disable_ath_buy": True, "disable_ma200_sell": True, "disable_takeprofit": True},
    "buy-only-no-sell": {"disable_ma200_sell": True, "disable_takeprofit": True},
}


def run_all(df_annotated, params, baselines_df=None):
    """
    Run all strategy variants + baselines, compute metrics, save results.csv.

    Parameters
    ----------
    df_annotated : pd.DataFrame
        DataFrame with B3 signal columns (output of indicators.annotate_signals).
    params : dict
        Full parameter dict (B4 schema).
    baselines_df : pd.DataFrame or None
        Raw price DataFrame (B2 contract) for computing baselines. If None, baselines skipped.

    Returns
    -------
    dict[str, pd.Series]
        Mapping of variant name -> equity Series (for plotting).
    """
    results_rows = []
    equities = {}

    for name, overrides in ABLATIONS.items():
        overrides = dict(overrides)
        overrides["_name"] = name
        r = run_strategy(df_annotated, params, ablation_overrides=overrides)
        equities[name] = r.equity
        row = {"variant": name}
        row.update(compute_metrics(r))
        results_rows.append(row)
        logger.info("  %s: %d trades, final_eq=%.2f", name, len(r.trades), r.equity.iloc[-1])

    if baselines_df is not None:
        cap = float(params["initial_capital"])
        r_ls = run_lumpsum(baselines_df, cap)
        equities["lumpsum"] = r_ls.equity
        row = {"variant": "lumpsum"}
        row.update(compute_metrics(r_ls))
        results_rows.append(row)

        r_dca = run_dca(baselines_df, cap, n_slices=100)
        equities["dca100"] = r_dca.equity
        row = {"variant": "dca100"}
        row.update(compute_metrics(r_dca))
        results_rows.append(row)

    out_dir = "backtest/output"
    os.makedirs(out_dir, exist_ok=True)
    df_out = pd.DataFrame(results_rows).set_index("variant")
    path = os.path.join(out_dir, "results.csv")
    df_out.to_csv(path)
    logger.info("Results saved to %s", path)

    return equities
