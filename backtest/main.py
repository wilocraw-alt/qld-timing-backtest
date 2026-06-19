#!/usr/bin/env python3
"""
QLD timed-entry strategy backtest — CLI entry point.

Usage:
  python3 backtest/main.py --config backtest/config.yaml --ablation all
  python3 backtest/main.py --config backtest/config.yaml --ablation full --n 10 --m 30
  python3 backtest/main.py --config backtest/config.yaml --ablation full --start 2010-01-01 --end 2020-12-31
"""
import argparse
import logging
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
logger = logging.getLogger("main")


def load_config(path):
    import yaml
    with open(path, "r") as f:
        return yaml.safe_load(f)


def override_params(config, args):
    """Apply CLI overrides to the config dict (no hardcoding)."""
    strat = config.setdefault("strategy", {})
    for key in ("n", "m", "a", "b", "c", "d", "e", "f"):
        val = getattr(args, key, None)
        if val is not None:
            strat[key] = val
    for key in ("initial_capital", "daily_buy_limit", "tranche_size",
                "pending_expiry_days", "pivot_lookback"):
        val = getattr(args, key, None)
        if val is not None:
            config[key] = val
    if args.rearm_on_new_pivot is not None:
        config["rearm_on_new_pivot"] = args.rearm_on_new_pivot
    return config


def main():
    parser = argparse.ArgumentParser(description="QLD timing strategy backtest")
    parser.add_argument("--config", default="backtest/config.yaml", help="Config YAML path")
    parser.add_argument("--ablation", default="all",
                        help="Ablation variant name or 'all' (default: all)")
    parser.add_argument("--start", default=None, help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end", default=None, help="End date (YYYY-MM-DD)")
    parser.add_argument("--force-dl", action="store_true", help="Force re-download from yfinance")

    # Strategy param overrides
    for key in ("n", "m", "a", "b", "c", "d", "e", "f"):
        parser.add_argument(f"--{key}", type=float, help=f"Override strategy.{key}")
    parser.add_argument("--initial_capital", type=float)
    parser.add_argument("--daily_buy_limit", type=float)
    parser.add_argument("--tranche_size", type=float)
    parser.add_argument("--pending_expiry_days", type=int)
    parser.add_argument("--pivot_lookback", type=int)
    parser.add_argument("--rearm_on_new_pivot", type=lambda x: x.lower() == "true")

    args = parser.parse_args()

    config = load_config(args.config)
    config = override_params(config, args)

    ticker = config["ticker"]

    from backtest.data.loader import load_prices
    from backtest.engine.indicators import annotate_signals

    logger.info("Loading %s prices ...", ticker)
    df_raw = load_prices(ticker, start=args.start, end=args.end,
                         force_dl=args.force_dl)
    logger.info("  -> %d rows (%s-%s)", len(df_raw),
                str(df_raw.index[0].date()), str(df_raw.index[-1].date()))

    logger.info("Annotating signals ...")
    df_ann = annotate_signals(df_raw, config)

    logger.info("Running ablation ...")
    from backtest.ablation import run_all
    equities = run_all(df_ann, config, baselines_df=df_raw)

    logger.info("Plotting ...")
    from backtest.analyze.plot import plot_equity, plot_drawdown
    plot_equity(equities, "backtest/output/equity.png")
    plot_drawdown(equities, "backtest/output/drawdown.png")

    logger.info("Done. Variants: %s", list(equities.keys()))
    print(f"\nResults: backtest/output/results.csv")
    print(f"Plots:   backtest/output/equity.png, backtest/output/drawdown.png")


if __name__ == "__main__":
    main()
