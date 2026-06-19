from dataclasses import dataclass, field
from typing import Optional
import pandas as pd

from .portfolio import PortfolioState

TRIGGER_COLS = {1: "trig_t1", 2: "trig_t2", 3: "trig_t3", 4: "trig_t4"}


@dataclass
class BacktestResult:
    equity: pd.Series
    cash: pd.Series
    shares: pd.Series
    trades: pd.DataFrame
    name: str = ""


def run_strategy(df: pd.DataFrame, params: dict, ablation_overrides: dict = None) -> BacktestResult:
    if ablation_overrides is None:
        ablation_overrides = {}

    disable_ma200 = ablation_overrides.get("disable_ma200_sell", False)
    disable_ath = ablation_overrides.get("disable_ath_buy", False)
    disable_prevlow = ablation_overrides.get("disable_prevlow_buy", False)
    disable_tp = ablation_overrides.get("disable_takeprofit", False)

    n = params["strategy"]["n"]
    m_ratio = params["strategy"]["m"] / 100.0
    c_pct = params["strategy"]["c"] / 100.0
    d_pct = params["strategy"]["d"] / 100.0

    daily_limit = params["daily_buy_limit"]
    tranche_size = params["tranche_size"]
    pending_expiry = params["pending_expiry_days"]
    rearm_pivot = params.get("rearm_on_new_pivot", True)

    port = PortfolioState(cash=float(params["initial_capital"]))

    trades = []
    eq_vals, cash_vals, sh_vals = [], [], []

    for date, row in df.iterrows():
        close = row["close"]

        if port.shares > 0:
            if not disable_ma200:
                streak = row.get("below_ma200_streak", 0)
                if port.ma200_armed and streak >= n:
                    t = port.sell(close, m_ratio, "ma200", date)
                    if t:
                        trades.append(t)
                        port.ma200_armed = False
            if not port.ma200_armed and row.get("below_ma200_streak", 0) == 0:
                port.ma200_armed = True
            if not disable_tp and port.avg_cost > 0:
                gain = (close - port.avg_cost) / port.avg_cost
                if gain >= d_pct and port.tp2_armed:
                    t = port.sell(close, 1.0, "tp2", date)
                    if t:
                        trades.append(t)
                        port.tp2_armed = False
                        port.tp1_armed = False
                elif gain >= c_pct and port.tp1_armed:
                    t = port.sell(close, 0.5, "tp1", date)
                    if t:
                        trades.append(t)
                        port.tp1_armed = False

        if port.shares <= 0:
            port.rearm_all()
        if rearm_pivot:
            if row.get("new_ath", False):
                port.rearm_ath()
            if row.get("new_low", False):
                port.rearm_prevlow()

        if not disable_ath:
            if row.get("trig_t1", False) and port.is_inactive(1):
                port.pending_buys.append({"tranche_id": 1, "queued_date": date, "ctype": "t1"})
            if row.get("trig_t2", False) and port.is_inactive(2):
                port.pending_buys.append({"tranche_id": 2, "queued_date": date, "ctype": "t2"})
        if not disable_prevlow:
            if row.get("trig_t3", False) and port.is_inactive(3):
                port.pending_buys.append({"tranche_id": 3, "queued_date": date, "ctype": "t3"})
            if row.get("trig_t4", False) and port.is_inactive(4):
                port.pending_buys.append({"tranche_id": 4, "queued_date": date, "ctype": "t4"})

        limit_used = 0.0
        kept = []
        for order in port.pending_buys:
            if limit_used >= daily_limit - 0.01:
                kept.append(order)
                continue
            tid = order["tranche_id"]
            days = (date - order["queued_date"]).days
            if days > pending_expiry:
                continue
            if not port.is_inactive(tid):
                continue
            if not row.get(TRIGGER_COLS[tid], False):
                continue
            avail = min(tranche_size, daily_limit - limit_used, port.cash)
            if avail < 1.0:
                kept.append(order)
                continue
            tr = port.buy(close, avail, tid, date)
            if tr:
                trades.append(tr)
                limit_used += avail
        port.pending_buys = kept

        eq = round(port.cash + port.shares * close, 2)
        eq_vals.append(eq)
        cash_vals.append(port.cash)
        sh_vals.append(port.shares)

    return BacktestResult(
        equity=pd.Series(eq_vals, index=df.index, name="equity"),
        cash=pd.Series(cash_vals, index=df.index, name="cash"),
        shares=pd.Series(sh_vals, index=df.index, name="shares"),
        trades=pd.DataFrame(trades) if trades else pd.DataFrame(columns=["date", "side", "reason", "shares", "price", "cash_after"]),
        name=ablation_overrides.get("_name", "full"),
    )
