import pandas as pd
import numpy as np
from backtest.engine.strategy import BacktestResult


class Ctx:
    """Decision context passed to decide_fn each trading day."""

    __slots__ = ("i", "date", "cash", "shares", "price",
                 "contrib_today", "equity", "prices")

    def __init__(self, i, date, cash, shares, price,
                 contrib_today, equity, prices):
        self.i = i
        self.date = date
        self.cash = cash
        self.shares = shares
        self.price = price
        self.contrib_today = contrib_today
        self.equity = equity
        self.prices = prices


def make_contributions(index, monthly=300.0):
    """
    Return pd.Series (same index) where each month's first trading day
    gets `monthly`, all other days 0.0.
    """
    contrib = pd.Series(0.0, index=pd.Index(index))
    years = index.year
    months = index.month
    seen = set()
    for i in range(len(index)):
        key = (years[i], months[i])
        if key not in seen:
            seen.add(key)
            contrib.iloc[i] = monthly
    return contrib


def run_contrib(prices_df, decide_fn, monthly=300.0, name="", cost=0.0):
    """
    Contribution-based backtest engine.

    Parameters
    ----------
    prices_df : pd.DataFrame
        Index=trading days, columns=ticker names (e.g. 'QLD'), values=close.
    decide_fn : callable
        ctx -> dict[ticker, signed_dollars].
    monthly : float
        Monthly contribution amount.
    name : str
    cost : float
        Transaction cost ratio (deducted from cash).

    Returns
    -------
    BacktestResult
    """
    contributions = make_contributions(prices_df.index, monthly)
    tickers = list(prices_df.columns)
    if not tickers:
        raise ValueError("prices_df must have at least one column")

    cash = 0.0
    shares = {t: 0 for t in tickers}
    trades = []
    eq_vals, cash_vals, sh_vals = [], [], []

    for i, (date, row) in enumerate(prices_df.iterrows()):
        close = {t: float(row[t]) for t in tickers}
        contrib_today = float(contributions.loc[date])
        cash += contrib_today
        equity = round(cash + sum(shares[t] * close[t] for t in tickers), 2)

        ctx = Ctx(
            i=i, date=date, cash=cash, shares=dict(shares),
            price=dict(close), contrib_today=contrib_today,
            equity=equity, prices=prices_df,
        )
        decision = decide_fn(ctx)

        # Pass 1: execute all sells first (free up cash for same-day buys)
        for ticker in tickers:
            sd = decision.get(ticker, 0.0)
            if sd >= -0.01:
                continue
            sell_dollars = min(-sd, shares[ticker] * close[ticker])
            qty = int(sell_dollars / close[ticker])
            if qty > 0:
                proceeds = round(qty * close[ticker], 2)
                fee = round(proceeds * cost, 2)
                cash = round(cash + proceeds - fee, 2)
                shares[ticker] -= qty
                trades.append({
                    "date": date, "side": "sell", "reason": "signal",
                    "ticker": ticker, "shares": qty,
                    "price": round(close[ticker], 4),
                    "cash_after": cash, "fee": fee,
                })

        # Pass 2: execute all buys (cash now includes sale proceeds)
        for ticker in tickers:
            sd = decision.get(ticker, 0.0)
            if sd <= 0.01:
                continue
            buy_dollars = min(sd, cash)
            qty = int(buy_dollars / close[ticker])
            if qty > 0:
                cost_trade = round(qty * close[ticker], 2)
                fee = round(cost_trade * cost, 2)
                cash = round(cash - cost_trade - fee, 2)
                shares[ticker] += qty
                trades.append({
                    "date": date, "side": "buy", "reason": "signal",
                    "ticker": ticker, "shares": qty,
                    "price": round(close[ticker], 4),
                    "cash_after": cash, "fee": fee,
                })

        total_shares = sum(shares.values())
        eq = round(cash + sum(shares[t] * close[t] for t in tickers), 2)
        eq_vals.append(eq)
        cash_vals.append(round(cash, 2))
        sh_vals.append(total_shares)

    cols = ["date", "side", "reason", "ticker", "shares",
            "price", "cash_after", "fee"]
    trades_df = pd.DataFrame(trades, columns=cols) if trades else pd.DataFrame(columns=cols)

    return BacktestResult(
        equity=pd.Series(eq_vals, index=prices_df.index, name="equity"),
        cash=pd.Series(cash_vals, index=prices_df.index, name="cash"),
        shares=pd.Series(sh_vals, index=prices_df.index, name="shares"),
        trades=trades_df,
        name=name,
    )


def decide_immediate(ctx):
    """Buy all available cash into the first ticker on contribution days."""
    if ctx.cash < 0.5:
        return {}
    return {list(ctx.prices.columns)[0]: ctx.cash}


def decide_daily(ctx):
    """
    Spread cash evenly across remaining trading days of the current month.
    On the last trading day of the month, deploy all remaining cash.
    Each day's amount is rounded to integer shares to avoid dust accumulation.
    """
    if ctx.cash < 0.5:
        return {}
    ticker = list(ctx.prices.columns)[0]
    idx = ctx.prices.index
    mask = (idx.year == ctx.date.year) & (idx.month == ctx.date.month)
    month_days = idx[mask]
    remaining = len(month_days) - month_days.get_loc(ctx.date)
    if remaining <= 0:
        remaining = 1
    amount = ctx.cash / remaining
    qty = int(amount / ctx.price[ticker])
    if qty > 0:
        return {ticker: qty * ctx.price[ticker]}
    elif remaining == 1 and ctx.cash > 0.5:
        return {ticker: ctx.cash}
    return {}


def make_decide_rule_v1(params=None):
    """
    Factory: returns a decide_fn that applies v1 timing signals (ATH declines,
    confirmed-low rebounds, 200MA stop, take-profit) to contribution cash flow.
    """
    from backtest.engine.indicators import annotate_signals

    defaults = {
        "pivot_lookback": 10,
        "pivot_min_move": 0.05,
        "strategy": {"n": 5, "m": 50, "a": 10, "b": 15,
                     "c": 20, "d": 40, "e": 10, "f": 20},
    }
    cfg = dict(defaults)
    if params:
        cfg.update(params)
        strat = dict(defaults["strategy"])
        strat.update(params.get("strategy", {}))
        cfg["strategy"] = strat

    n = cfg["strategy"]["n"]
    m_ratio = cfg["strategy"]["m"] / 100.0
    c_pct = cfg["strategy"]["c"] / 100.0
    d_pct = cfg["strategy"]["d"] / 100.0

    _annotated = None
    _avg_cost = 0.0
    _ma200_armed = True
    _tp1_armed = True
    _tp2_armed = True

    def decide(ctx):
        nonlocal _annotated, _avg_cost
        nonlocal _ma200_armed, _tp1_armed, _tp2_armed

        ticker = list(ctx.prices.columns)[0]

        if _annotated is None:
            close_col = ctx.prices.iloc[:, 0]
            _annotated = annotate_signals(close_col.to_frame(name="close"), cfg)

        row = _annotated.iloc[ctx.i]

        decision = {}

        # ── Sell logic ────────────────────────────────────────────────
        if ctx.shares.get(ticker, 0) > 0:
            price = ctx.price[ticker]
            streak = int(row.get("below_ma200_streak", 0))

            if _ma200_armed and streak >= n:
                qty = int(ctx.shares[ticker] * m_ratio)
                if qty > 0:
                    decision[ticker] = -qty * price
                _ma200_armed = False
            if streak == 0:
                _ma200_armed = True

            if _avg_cost > 0:
                gain = (ctx.price[ticker] - _avg_cost) / _avg_cost
            else:
                gain = 0.0

            if _tp2_armed and gain >= d_pct:
                qty = ctx.shares[ticker]
                sell_val = qty * price
                decision[ticker] = decision.get(ticker, 0) - sell_val
                _tp2_armed = False
                _tp1_armed = False
            elif _tp1_armed and _tp2_armed and gain >= c_pct:
                qty = int(ctx.shares[ticker] * 0.5)
                if qty > 0:
                    sell_val = qty * price
                    decision[ticker] = decision.get(ticker, 0) - sell_val
                _tp1_armed = False

        # ── Buy logic (only if not selling today) ──────────────────────
        is_selling = any(v < 0 for v in decision.values())
        if ctx.cash > 0 and not is_selling:
            tranche = ctx.cash * 0.10
            buy_total = 0.0
            for trig in ("trig_t1", "trig_t2", "trig_t3", "trig_t4"):
                if bool(row.get(trig, False)):
                    buy_total += tranche

            if buy_total > 0:
                decision[ticker] = min(buy_total, ctx.cash)

        # ── Update tracked avg_cost ───────────────────────────────────
        buy_dollars = decision.get(ticker, 0)
        if buy_dollars > 0:
            qty = int(min(buy_dollars, ctx.cash) / ctx.price[ticker])
            if qty > 0:
                old_shares = ctx.shares.get(ticker, 0)
                new_shares_total = old_shares + qty
                old_total_val = old_shares * _avg_cost
                new_cost_val = qty * ctx.price[ticker]
                _avg_cost = round((old_total_val + new_cost_val) / new_shares_total, 4)
        if ctx.shares.get(ticker, 0) <= 0 and decision.get(ticker, 0) <= 0:
            _avg_cost = 0.0

        return decision

    return decide
