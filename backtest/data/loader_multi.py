"""
Multi-asset price loader: thin wrapper over loader.load_prices that fetches
several tickers and aligns them onto a common (inner-joined) trading calendar.
"""
import pandas as pd

from backtest.data.loader import load_prices


def load_many(tickers, start=None, end=None, cache_dir="backtest/data/cache"):
    """
    Load `close` Series for each ticker.

    Returns
    -------
    dict[str, pd.Series]
        ticker -> close price Series.
    """
    out = {}
    for t in tickers:
        df = load_prices(t, start, end, cache_dir, False)
        out[t] = df["close"].rename(t)
    return out


def align(prices):
    """
    Inner-join the close Series in `prices` (dict ticker->Series) onto their
    common trading days.

    Returns
    -------
    pd.DataFrame
        index=trading days (ascending), columns=tickers, no NaN rows.
    """
    df = pd.concat(prices, axis=1)
    df = df.dropna(how="any").sort_index()
    return df
