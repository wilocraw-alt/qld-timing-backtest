import numpy as np
import pandas as pd


def compute_metrics(result):
    """
    Compute performance metrics from a BacktestResult.

    Parameters
    ----------
    result : BacktestResult
        With .equity (pd.Series), .cash (pd.Series), .shares (pd.Series), .trades (pd.DataFrame).

    Returns
    -------
    dict
        Keys: total_return, cagr, mdd, ann_vol, sharpe, sortino, exposure, avg_cash, trades, final_value.
    """
    eq = result.equity
    cash = result.cash
    shares = result.shares
    trades_df = result.trades

    n = len(eq)
    if n < 2:
        return {k: 0.0 for k in ("total_return", "cagr", "mdd", "ann_vol", "sharpe", "sortino", "exposure", "avg_cash", "trades", "final_value")}

    init = float(eq.iloc[0])
    final = float(eq.iloc[-1])
    total_return = final / init - 1.0 if init > 0 else 0.0

    days = (eq.index[-1] - eq.index[0]).days
    cagr = (final / init) ** (365.25 / max(days, 1)) - 1.0 if init > 0 and days > 0 else 0.0

    daily_ret = eq.pct_change().dropna()
    ann_vol = float(daily_ret.std() * np.sqrt(252)) if len(daily_ret) > 1 else 0.0
    sharpe = float(daily_ret.mean() * 252 / ann_vol) if ann_vol > 0 else 0.0

    neg_ret = daily_ret[daily_ret < 0]
    downside_std = float(neg_ret.std() * np.sqrt(252)) if len(neg_ret) > 1 else 0.0
    sortino = float(daily_ret.mean() * 252 / downside_std) if downside_std > 0 else 0.0

    cummax = eq.cummax()
    dd = ((cummax - eq) / cummax).max()
    mdd = float(dd) if not np.isnan(dd) else 0.0

    exposure = float((shares > 0).sum() / n) if n > 0 else 0.0
    ratio = cash / eq
    avg_cash = float(ratio.mean()) if n > 0 else 0.0

    return {
        "total_return": round(total_return, 4),
        "cagr": round(cagr, 4),
        "mdd": round(mdd, 4),
        "ann_vol": round(ann_vol, 4),
        "sharpe": round(sharpe, 4),
        "sortino": round(sortino, 4),
        "exposure": round(exposure, 4),
        "avg_cash": round(avg_cash, 4),
        "trades": len(trades_df),
        "final_value": round(final, 2),
    }
