#!/usr/bin/env python3
"""
QLD v2 trend-following strategy backtest — CLI entry point.

Usage:
  python3 backtest/main_v2.py --config backtest/config_v2.yaml --ablation all
  python3 backtest/main_v2.py --config backtest/config_v2.yaml --ablation v2-full --core_ratio 0.40
"""
import argparse
import logging
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
logger = logging.getLogger("main_v2")


def load_config(path):
    import yaml
    with open(path) as f:
        return yaml.safe_load(f)


def override_v2_params(config, args):
    v2 = config.setdefault("v2", {})
    for key in ("ma_fast", "ma_slow", "recovery_days", "core_ratio",
                "sell_days", "buy_days", "dd_threshold", "overheat_ratio", "cool_ratio"):
        val = getattr(args, key, None)
        if val is not None:
            v2[key] = val
    for key in ("initial_capital",):
        val = getattr(args, key, None)
        if val is not None:
            config[key] = val
    return config


def main():
    parser = argparse.ArgumentParser(description="QLD v2 trend-following backtest")
    parser.add_argument("--config", default="backtest/config_v2.yaml")
    parser.add_argument("--ablation", default="all")
    parser.add_argument("--start", default=None)
    parser.add_argument("--end", default=None)
    parser.add_argument("--force-dl", action="store_true")
    for key in ("ma_fast", "ma_slow", "recovery_days", "core_ratio",
                "sell_days", "buy_days", "dd_threshold", "overheat_ratio", "cool_ratio"):
        parser.add_argument(f"--{key}", type=float)
    parser.add_argument("--initial_capital", type=float)

    args = parser.parse_args()
    config = load_config(args.config)
    config = override_v2_params(config, args)

    from backtest.data.loader import load_prices
    from backtest.engine.indicators_v2 import annotate_v2

    ticker = config["ticker"]
    start = args.start or config.get("start")
    end = args.end or config.get("end")

    logger.info("Loading %s %s..%s ...", ticker, start, end)
    df_raw = load_prices(ticker, start=start, end=end, force_dl=args.force_dl)
    logger.info("  -> %d rows", len(df_raw))

    logger.info("Annotating v2 signals ...")
    df_ann = annotate_v2(df_raw, config)

    # v1 signals for comparison
    from backtest.engine.indicators import annotate_signals
    df_ann_v1 = annotate_signals(df_raw, config)

    logger.info("Running v2 ablation ...")
    from backtest.ablation_v2 import run_all_v2
    equities = run_all_v2(df_ann, config, df_raw,
                          params_v1=config, df_annotated_v1=df_ann_v1)

    from backtest.analyze.plot import plot_equity, plot_drawdown
    plot_equity(equities, "backtest/output/equity_v2.png")
    plot_drawdown(equities, "backtest/output/drawdown_v2.png")

    logger.info("Done. Variants: %s", list(equities.keys()))
    print(f"\nResults: backtest/output/results_v2.csv")
    print(f"Plots:   backtest/output/equity_v2.png, backtest/output/drawdown_v2.png")


if __name__ == "__main__":
    main()
