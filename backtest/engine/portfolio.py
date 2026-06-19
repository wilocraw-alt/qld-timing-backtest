from dataclasses import dataclass, field
from typing import Optional
import pandas as pd


@dataclass
class PortfolioState:
    cash: float
    shares: int = 0
    avg_cost: float = 0.0
    active_tranches: set = field(default_factory=set)
    pending_buys: list = field(default_factory=list)
    ma200_armed: bool = True
    tp1_armed: bool = True
    tp2_armed: bool = True

    def buy(self, price: float, amount: float, tranche_id: int, date: pd.Timestamp):
        shares_bought = int(amount / price)
        if shares_bought <= 0 or amount <= 0:
            return None
        cost = round(shares_bought * price, 2)
        old_total = self.shares * self.avg_cost
        self.cash = round(self.cash - cost, 2)
        self.shares += shares_bought
        self.avg_cost = round((old_total + cost) / self.shares, 4) if self.shares > 0 else 0.0
        self.active_tranches.add(tranche_id)
        self.tp1_armed = True
        self.tp2_armed = True
        return {"date": date, "side": "buy", "reason": f"t{tranche_id}", "shares": shares_bought, "price": round(price, 4), "cash_after": self.cash}

    def sell(self, price: float, ratio: float, reason: str, date: pd.Timestamp):
        if self.shares <= 0 or ratio <= 0:
            return None
        shares_to_sell = int(self.shares * ratio)
        if shares_to_sell <= 0:
            return None
        proceeds = round(shares_to_sell * price, 2)
        self.cash = round(self.cash + proceeds, 2)
        self.shares -= shares_to_sell
        if self.shares <= 0:
            self.shares = 0
            self.avg_cost = 0.0
        return {"date": date, "side": "sell", "reason": reason, "shares": shares_to_sell, "price": round(price, 4), "cash_after": self.cash}

    def rearm_all(self):
        self.active_tranches.clear()
        self.ma200_armed = True
        self.tp1_armed = True
        self.tp2_armed = True

    def rearm_ath(self):
        self.active_tranches.difference_update({1, 2})

    def rearm_prevlow(self):
        self.active_tranches.difference_update({3, 4})

    def is_inactive(self, tid: int) -> bool:
        return tid not in self.active_tranches
