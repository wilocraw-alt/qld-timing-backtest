import pandas as pd
import numpy as np

from backtest.engine.strategy import BacktestResult


def run_lumpsum(df, initial_capital):
    """
    Buy-and-hold: invest all cash on the first day at close price.

    Parameters
    ----------
    df : pd.DataFrame
        Raw price DataFrame with 'close' column (B2 contract).
    initial_capital : float

    Returns
    -------
    BacktestResult
    """
    dates = df.index
    first_close = float(df["close"].iloc[0])
    shares = int(initial_capital / first_close)
    cost = shares * first_close
    cash = initial_capital - cost

    cash_vals = [cash] * len(dates)
    sh_vals = [shares] * len(dates)

    eq_vals = [round(cash + shares * float(df["close"].iloc[i]), 2) for i in range(len(dates))]
    trades = pd.DataFrame([{
        "date": dates[0], "side": "buy", "reason": "lumpsum",
        "shares": shares, "price": round(first_close, 4), "cash_after": round(cash, 2)
    }])

    return BacktestResult(
        equity=pd.Series(eq_vals, index=dates, name="equity"),
        cash=pd.Series(cash_vals, index=dates, name="cash"),
        shares=pd.Series(sh_vals, index=dates, name="shares"),
        trades=trades, name="lumpsum",
    )


def run_dca(df, initial_capital, n_slices=100):
    """
    Dollar-cost average: split capital into n_slices, buy equal amounts
    at regular intervals across the full period.

    Parameters
    ----------
    df : pd.DataFrame
    initial_capital : float
    n_slices : int

    Returns
    -------
    BacktestResult
    """
    dates = df.index
    close = df["close"]
    slice_amount = initial_capital / n_slices

    step = max(len(dates) // n_slices, 1)
    buy_indices = list(range(0, len(dates), step))[:n_slices]

    trades = []
    cash = initial_capital
    total_shares = 0
    avg_cost = 0.0

    eq_vals, cash_vals, sh_vals = [], [], []

    for i, date in enumerate(dates):
        price = float(close.iloc[i])
        if i in buy_indices:
            amount = min(slice_amount, cash)
            shares_bought = int(amount / price)
            if shares_bought > 0:
                cost = shares_bought * price
                old_val = total_shares * avg_cost
                cash -= cost
                total_shares += shares_bought
                avg_cost = (old_val + cost) / total_shares if total_shares > 0 else 0.0
                trades.append({
                    "date": date, "side": "buy", "reason": "dca",
                    "shares": shares_bought, "price": round(price, 4),
                    "cash_after": round(cash, 2),
                })

        eq_vals.append(round(cash + total_shares * price, 2))
        cash_vals.append(round(cash, 2))
        sh_vals.append(total_shares)

    return BacktestResult(
        equity=pd.Series(eq_vals, index=dates, name="equity"),
        cash=pd.Series(cash_vals, index=dates, name="cash"),
        shares=pd.Series(sh_vals, index=dates, name="shares"),
        trades=pd.DataFrame(trades) if trades else pd.DataFrame(columns=["date", "side", "reason", "shares", "price", "cash_after"]),
        name="dca100",
    )
