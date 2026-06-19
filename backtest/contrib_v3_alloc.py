"""
backtest/contrib_v3_alloc.py
────────────────────────────
Two decide_fn implementations for the monthly-contribution backtest engine.

Both functions consume a ctx object (provided by contrib.py's run_contrib) and
return dict{ticker: signed_dollars} (positive=buy, negative=sell).
The engine clamps orders to available cash / held shares, so we only express
"target-directed orders" in dollar terms.

Assumptions:
  - ctx.prices has columns ["QQQ", "QLD", "TQQQ"]
  - Only ctx.prices.iloc[:ctx.i+1] is used — no look-ahead
  - Data-insufficient warmup periods fall back to cash (return {})

Regime logic (decide_v3_regime):
  ratio = QQQ_close / QQQ_200MA
  ratio > 1.15  →  hold TQQQ
  ratio > 1.00  →  hold QLD
  else          →  cash (sell all)

Dual-momentum logic (decide_dual_momentum):
  - Updates only on the first trading day of each calendar month
  - 12-month (252-bar) return for QQQ, QLD, TQQQ
  - Best performer → target; if best < 0  →  cash
  - Between rebalance days: return {} (hold whatever is in the portfolio)
"""

from __future__ import annotations
import numpy as np
import pandas as pd

TICKERS = ["QQQ", "QLD", "TQQQ"]

# ──────────────────────────────────────────────────────────────────────────────
# Internal helpers
# ──────────────────────────────────────────────────────────────────────────────

def _switch_to(ctx, target: str | None) -> dict:
    """
    Build orders to move all holdings into `target` ETF (or cash if None).

    Steps:
      1. Sell everything that isn't the target (full-position sell orders).
      2. Buy target with all available cash + estimated sale proceeds.

    The engine clamps everything, so over-ordering is safe.
    """
    orders: dict[str, float] = {}

    # Collect proceeds from selling non-target positions
    estimated_proceeds = 0.0
    for ticker in TICKERS:
        held = ctx.shares.get(ticker, 0)
        if held > 0 and ticker != target:
            px = ctx.price.get(ticker, 0.0)
            sell_val = held * px
            orders[ticker] = -sell_val          # full sell
            estimated_proceeds += sell_val

    if target is not None:
        # Buy target with all cash + sale proceeds
        buy_budget = ctx.cash + estimated_proceeds
        if buy_budget > 0:
            orders[target] = buy_budget

    return orders


def _qqq_ma200_ratio(ctx) -> float | None:
    """
    Compute QQQ close / QQQ 200-day MA using only rows 0..ctx.i (inclusive).
    Returns None if insufficient data.
    """
    hist = ctx.prices["QQQ"].iloc[: ctx.i + 1]
    if len(hist) < 200:
        return None
    ma200 = hist.rolling(200).mean().iloc[-1]
    if np.isnan(ma200) or ma200 == 0:
        return None
    return float(hist.iloc[-1]) / float(ma200)


def _best_12mo_ticker(ctx) -> str | None:
    """
    Pick the 252-bar best-return ticker among QQQ/QLD/TQQQ.
    Returns None if data insufficient or best return < 0.
    """
    hist = ctx.prices[TICKERS].iloc[: ctx.i + 1]
    if len(hist) < 253:          # need at least 253 rows for a 252-bar return
        return None

    returns: dict[str, float] = {}
    for t in TICKERS:
        series = hist[t]
        p_now  = series.iloc[-1]
        p_252  = series.iloc[-253]
        if p_252 == 0 or np.isnan(p_252) or np.isnan(p_now):
            return None
        returns[t] = (p_now - p_252) / p_252

    best_ticker = max(returns, key=returns.__getitem__)
    if returns[best_ticker] <= 0:
        return None                  # all negative → cash
    return best_ticker


# ──────────────────────────────────────────────────────────────────────────────
# Public decide functions
# ──────────────────────────────────────────────────────────────────────────────

def decide_v3_regime(ctx) -> dict:
    """
    Regime-stack allocator using QQQ 200-day MA ratio.

    ratio > 1.15  →  TQQQ
    ratio > 1.00  →  QLD
    else          →  cash (sell all, hold cash)

    No look-ahead: only prices.iloc[:i+1] is read.
    Returns {} (no action) if data is insufficient or already in correct position.
    """
    ratio = _qqq_ma200_ratio(ctx)

    if ratio is None:
        # Warmup: insufficient data → stay in cash (sell any existing holdings)
        orders = {}
        for ticker in TICKERS:
            held = ctx.shares.get(ticker, 0)
            if held > 0:
                orders[ticker] = -held * ctx.price.get(ticker, 0.0)
        return orders

    # Determine target asset
    if ratio > 1.15:
        target = "TQQQ"
    elif ratio > 1.00:
        target = "QLD"
    else:
        target = None        # cash

    # Check if already in the right position
    if target is not None:
        already_held = ctx.shares.get(target, 0) > 0
        no_others    = all(
            ctx.shares.get(t, 0) == 0 for t in TICKERS if t != target
        )
        if already_held and no_others and ctx.cash < 1.0:
            return {}        # nothing to do

    return _switch_to(ctx, target)


# State for dual-momentum (module-level, resets via factory below)
class _DualMomState:
    def __init__(self):
        self.last_month: int | None = None
        self.cached_target: str | None = None   # current month's chosen asset

_dm_state = _DualMomState()


def reset_dual_momentum_state():
    """Call between backtests to avoid state bleed across runs."""
    global _dm_state
    _dm_state = _DualMomState()


def decide_dual_momentum(ctx) -> dict:
    """
    Dual-momentum allocator. Rebalances only on the first trading day of each month.

    On rebalance day:
      - Compute 252-bar return for QQQ, QLD, TQQQ (i-slice only)
      - Allocate to winner; if winner return ≤ 0 → cash
    Between rebalance days:
      - Add incoming contribution cash to current holding (buy more of same asset)
      - Return {} to hold position (engine adds cash automatically via contrib_today)

    No look-ahead: only prices.iloc[:i+1] is read.
    """
    global _dm_state

    current_month = ctx.date.month

    is_first_of_month = (_dm_state.last_month != current_month)

    if is_first_of_month:
        _dm_state.last_month   = current_month
        _dm_state.cached_target = _best_12mo_ticker(ctx)

    target = _dm_state.cached_target

    if is_first_of_month:
        # Rebalance: switch to new target
        return _switch_to(ctx, target)
    else:
        # Mid-month: invest any fresh contribution into the current target,
        # but only if there's meaningful cash to deploy.
        if target is not None and ctx.contrib_today > 0:
            return {target: ctx.cash}   # deploy all available cash to target
        return {}
