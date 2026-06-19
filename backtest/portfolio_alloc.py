"""
Portfolio allocation decision functions for the contribution engine.
"""
from __future__ import annotations
import numpy as np


def _inv_vol_weights(ctx, tickers, win=60):
    """Return {ticker: weight} inverse-vol normalized (1/sigma_i / sum 1/sigma_j)."""
    vols = {}
    for t in tickers:
        if t not in ctx.prices.columns:
            continue
        hist = ctx.prices[t].iloc[:ctx.i + 1]
        if len(hist) < win + 5:
            continue
        ret = hist.pct_change().dropna()
        if len(ret) < win:
            continue
        vol = float(ret.iloc[-win:].std() * np.sqrt(252))
        if np.isnan(vol) or vol <= 0:
            continue
        vols[t] = 1.0 / vol
    if not vols:
        return {}
    total = sum(vols.values())
    return {t: round(v / total, 6) for t, v in vols.items()}


def _rebalance_orders(ctx, target_w):
    """
    For every ticker in ctx.prices.columns, compute order = target - current.
    target_w[t] * equity gives dollar target. Non-target tickers get w=0 (liquidation).
    Returns dict[ticker, signed_dollars].
    """
    orders = {}
    equity = ctx.equity
    for t in ctx.prices.columns:
        current_val = ctx.shares.get(t, 0) * ctx.price.get(t, 0.0)
        target_val = target_w.get(t, 0.0) * equity
        diff = round(target_val - current_val, 2)
        if abs(diff) >= 0.5:
            orders[t] = diff
    return orders


def _ma200_above(ctx, ticker):
    """True if close[ticker] > its 200-day MA (using data up to ctx.i)."""
    if ticker not in ctx.prices.columns:
        return False
    hist = ctx.prices[ticker].iloc[:ctx.i + 1]
    if len(hist) < 200:
        return False
    ma = float(hist.rolling(200).mean().iloc[-1])
    if np.isnan(ma) or ma <= 0:
        return False
    return float(hist.iloc[-1]) > ma


def _first_of_month(ctx, last_month):
    """Check if current date is a new month vs last_month."""
    if last_month is None:
        return True
    return ctx.date.month != last_month[1] or ctx.date.year != last_month[0]


# ─── Strategy factories ────────────────────────────────────────────────

def make_regime_basket(params=None):
    """
    Regime-based basket with inverse-vol weighting.
    Risk-ON (QQQ>200MA AND SPY>200MA): {TQQQ, UPRO, QLD, SSO} inv-vol.
    Risk-OFF: {TLT, GLD} inv-vol.
    Monthly rebalance.
    """
    p = dict(params or {})
    on_tickers = p.get("on_tickers", ["TQQQ", "UPRO", "QLD", "SSO"])
    off_tickers = p.get("off_tickers", ["TLT", "GLD"])
    qqq_ticker = p.get("qqq_ticker", "QQQ")
    spy_ticker = p.get("spy_ticker", "SPY")
    win = p.get("win", 60)

    last_month = None

    def decide(ctx):
        nonlocal last_month

        if not _first_of_month(ctx, last_month):
            return {}

        last_month = (ctx.date.year, ctx.date.month)

        qqq_on = _ma200_above(ctx, qqq_ticker)
        spy_on = _ma200_above(ctx, spy_ticker)
        risk_on = qqq_on and spy_on

        basket = on_tickers if risk_on else off_tickers
        valid = [t for t in basket if t in ctx.prices.columns
                 and len(ctx.prices[t].iloc[:ctx.i + 1]) >= win + 5]
        if not valid:
            return _rebalance_orders(ctx, {})

        w = _inv_vol_weights(ctx, valid, win=win)
        if not w:
            return _rebalance_orders(ctx, {})

        return _rebalance_orders(ctx, w)

    return decide


def make_xsec_momentum(params=None):
    """
    Cross-sectional momentum: each month, select top_n tickers (positive
    mean momentum across 3/6/12mo), inverse-vol weight.
    """
    p = dict(params or {})
    top_n = int(p.get("top_n", 3))
    lookbacks = p.get("lookbacks", [63, 126, 252])
    win = p.get("win", 60)

    last_month = None

    def decide(ctx):
        nonlocal last_month

        if not _first_of_month(ctx, last_month):
            return {}

        last_month = (ctx.date.year, ctx.date.month)

        max_lb = max(lookbacks)
        hist = ctx.prices.iloc[:ctx.i + 1]
        if len(hist) < max_lb + 1:
            return _rebalance_orders(ctx, {})

        # Compute blended momentum for each ticker
        scores = {}
        for t in ctx.prices.columns:
            series = hist[t]
            p_now = float(series.iloc[-1])
            rets = []
            for lb in lookbacks:
                p_lag = float(series.iloc[-(lb + 1)])
                rets.append((p_now - p_lag) / p_lag if p_lag > 0 else 0.0)
            mom = float(np.mean(rets))
            if mom > 0:
                scores[t] = mom

        if not scores:
            return _rebalance_orders(ctx, {})

        # Pick top N
        sorted_tickers = sorted(scores, key=scores.__getitem__, reverse=True)
        selected = sorted_tickers[:top_n]

        w = _inv_vol_weights(ctx, selected, win=win)
        return _rebalance_orders(ctx, w)

    return decide


def make_static_lev(params=None):
    """
    Static target-weight portfolio, monthly rebalance.
    Default: TQQQ 40%, UPRO 30%, TLT 15%, GLD 15%.
    """
    p = dict(params or {})
    targets = p.get("targets", {
        "TQQQ": 0.40, "UPRO": 0.30, "TLT": 0.15, "GLD": 0.15,
    })

    last_month = None

    def decide(ctx):
        nonlocal last_month

        if not _first_of_month(ctx, last_month):
            return {}

        last_month = (ctx.date.year, ctx.date.month)

        return _rebalance_orders(ctx, targets)

    return decide
