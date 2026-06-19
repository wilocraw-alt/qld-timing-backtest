import pandas as pd
import numpy as np

from backtest.engine.strategy import BacktestResult


def run_strategy_v2(df: pd.DataFrame, params: dict, ablation_overrides: dict = None) -> BacktestResult:
    if ablation_overrides is None:
        ablation_overrides = {}

    disable_core = ablation_overrides.get("disable_core", False)
    disable_overheat = ablation_overrides.get("disable_overheat", False)
    disable_dd_exit = ablation_overrides.get("disable_dd_exit", False)
    instant_sell = ablation_overrides.get("instant_sell", False)
    slow_reentry = ablation_overrides.get("slow_reentry", False)
    lump_cashout = ablation_overrides.get("lump_cashout", False)

    v2 = params.get("v2", {})
    core_ratio = v2.get("core_ratio", 0.30)
    if disable_core or lump_cashout:
        core_ratio = 0.0
    buy_days = v2.get("buy_days", 3)
    if slow_reentry:
        buy_days = 10
    sell_days = v2.get("sell_days", 3)
    if instant_sell:
        sell_days = 1

    initial_capital = float(params["initial_capital"])
    cash = initial_capital
    core_shares = 0
    sat_shares = 0
    avg_cost = 0.0

    regime = "risk_on"
    sat_target_cash = initial_capital * (1.0 - core_ratio)
    sell_remaining = 0
    sell_chunk = 0
    in_overheat = False

    trades = []
    eq_vals, cash_vals, sh_vals = [], [], []

    for date, row in df.iterrows():
        close = float(row["close"])

        if len(eq_vals) == 0 and core_ratio > 0:
            amount = initial_capital * core_ratio
            core_shares = int(amount / close)
            cost = round(core_shares * close, 2)
            cash = round(initial_capital - cost, 2)
            avg_cost = round(cost / core_shares, 4) if core_shares > 0 else 0.0
            trades.append({
                "date": date, "side": "buy", "reason": "core",
                "shares": core_shares, "price": round(close, 4),
                "cash_after": cash,
            })

        regime_bear = bool(row.get("regime_bear", False))
        dd_exit = bool(row.get("dd_exit", False)) if not disable_dd_exit else False
        recovery = bool(row.get("recovery", False))
        overheat_sig = bool(row.get("overheat", False))
        cooled_sig = bool(row.get("cooled", False))

        if regime == "risk_on":
            if regime_bear or dd_exit:
                regime = "bear_selling"
                if lump_cashout:
                    cash = round(cash + sat_shares * close, 2)
                    trades.append({
                        "date": date, "side": "sell", "reason": "lump_cashout",
                        "shares": sat_shares, "price": round(close, 4),
                        "cash_after": cash,
                    })
                    sat_shares = 0
                else:
                    sell_remaining = int(sat_shares)
                    sell_chunk = max(1, int(sell_remaining / sell_days))
        elif regime == "bear_selling":
            if recovery:
                regime = "risk_on"

        if regime == "bear_selling" and not lump_cashout:
            if sell_remaining > 0:
                sell_today = min(sell_chunk, sell_remaining)
                proceeds = round(sell_today * close, 2)
                cash = round(cash + proceeds, 2)
                sat_shares -= sell_today
                sell_remaining -= sell_today
                trades.append({
                    "date": date, "side": "sell", "reason": "sat_sell",
                    "shares": sell_today, "price": round(close, 4),
                    "cash_after": cash,
                })

        if regime == "risk_on":
            if not disable_overheat and overheat_sig and not in_overheat and sat_shares > 0:
                sell_oh = int(sat_shares * 0.5)
                if sell_oh > 0:
                    proceeds = round(sell_oh * close, 2)
                    cash = round(cash + proceeds, 2)
                    sat_shares -= sell_oh
                    in_overheat = True
                    trades.append({
                        "date": date, "side": "sell", "reason": "overheat_sell",
                        "shares": sell_oh, "price": round(close, 4),
                        "cash_after": cash,
                    })
            if not disable_overheat and cooled_sig and in_overheat:
                in_overheat = False

            if not in_overheat and cash > 0.1:
                buy_chunk = max(1, int(sat_target_cash / buy_days))
                buy_amt = min(buy_chunk, cash)
                bought = int(buy_amt / close)
                if bought > 0:
                    cost = round(bought * close, 2)
                    old_total = (core_shares + sat_shares) * avg_cost
                    cash = round(cash - cost, 2)
                    sat_shares += bought
                    total = core_shares + sat_shares
                    avg_cost = round((old_total + cost) / total, 4) if total > 0 else 0.0
                    trades.append({
                        "date": date, "side": "buy", "reason": "sat_buy",
                        "shares": bought, "price": round(close, 4),
                        "cash_after": cash,
                    })

        total = core_shares + sat_shares
        eq = round(cash + total * close, 2)
        eq_vals.append(eq)
        cash_vals.append(round(cash, 2))
        sh_vals.append(total)

    return BacktestResult(
        equity=pd.Series(eq_vals, index=df.index, name="equity"),
        cash=pd.Series(cash_vals, index=df.index, name="cash"),
        shares=pd.Series(sh_vals, index=df.index, name="shares"),
        trades=pd.DataFrame(trades) if trades else pd.DataFrame(columns=["date", "side", "reason", "shares", "price", "cash_after"]),
        name=ablation_overrides.get("_name", "v2-full"),
    )
