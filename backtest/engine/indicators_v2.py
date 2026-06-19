import numpy as np
import pandas as pd


def annotate_v2(df: pd.DataFrame, params: dict) -> pd.DataFrame:
    """
    Annotates the price DataFrame with v2 trend-following indicators and signals.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame with a tz-naive DatetimeIndex (ascending) and a 'close' column (float).
    params : dict
        Parameters dictionary. Reads from params['v2'] sub-dict with fallback defaults.

    Returns
    -------
    pd.DataFrame
        Original DataFrame plus additional signal columns (t-point info only, no look-ahead).

    Added columns:
        ma_fast       : float  - Rolling mean of close over ma_fast window
        ma_slow       : float  - Rolling mean of close over ma_slow window
        dead_cross    : bool   - ma_fast < ma_slow
        golden_cross  : bool   - ma_fast > ma_slow
        high_252      : float  - Rolling 252-day high (min_periods=1)
        dd_from_high  : float  - Drawdown from high_252 (0..1)
        regime_bear   : bool   - close < ma_slow AND ma_fast < ma_slow
        dd_exit       : bool   - dd_from_high > dd_threshold
        recovery      : bool   - close > ma_fast for recovery_days consecutive days
        overheat      : bool   - close / ma_slow > overheat_ratio
        cooled        : bool   - close / ma_slow < cool_ratio
    """
    # Extract v2 sub-params with defaults
    v2 = params.get("v2", {})
    ma_fast_w  = int(v2.get("ma_fast",        50))
    ma_slow_w  = int(v2.get("ma_slow",       200))
    rec_days   = int(v2.get("recovery_days",    3))
    dd_thresh  = float(v2.get("dd_threshold", 0.20))
    oh_ratio   = float(v2.get("overheat_ratio", 1.40))
    cool_ratio = float(v2.get("cool_ratio",     1.20))

    if "close" not in df.columns:
        raise KeyError("Input DataFrame must contain a 'close' column.")

    res = df.copy().sort_index()
    close = res["close"]

    # ── Moving averages ─────────────────────────────────────────────────────
    res["ma_fast"] = close.rolling(ma_fast_w).mean()
    res["ma_slow"] = close.rolling(ma_slow_w).mean()

    # ── Crossover signals ────────────────────────────────────────────────────
    # NaN-safe: where ma is NaN treat as False
    ma_fast_valid = res["ma_fast"].notna()
    ma_slow_valid = res["ma_slow"].notna()
    both_valid    = ma_fast_valid & ma_slow_valid

    res["dead_cross"]   = both_valid & (res["ma_fast"] < res["ma_slow"])
    res["golden_cross"] = both_valid & (res["ma_fast"] > res["ma_slow"])

    # ── 252-day rolling high and drawdown ────────────────────────────────────
    res["high_252"]    = close.rolling(252, min_periods=1).max()
    res["dd_from_high"] = 1.0 - close / res["high_252"]

    # ── Bear regime: close < ma_slow AND dead_cross ───────────────────────────
    res["regime_bear"] = both_valid & (close < res["ma_slow"]) & (res["ma_fast"] < res["ma_slow"])

    # ── dd_exit: drawdown exceeds threshold ──────────────────────────────────
    res["dd_exit"] = res["dd_from_high"] > dd_thresh

    # ── Recovery: close > ma_fast for rec_days consecutive days ─────────────
    # Use rolling sum: if close > ma_fast is True (=1) for rec_days consecutive days,
    # their sum equals rec_days.
    above_fast = (ma_fast_valid & (close > res["ma_fast"])).astype(int)
    # A day is "recovery" if rolling sum of rec_days == rec_days (all True)
    # This uses only past data (close window ending at t), no look-ahead.
    res["recovery"] = above_fast.rolling(rec_days).sum() == rec_days

    # ── Overheat / cooled (relative to ma_slow) ──────────────────────────────
    ratio = close / res["ma_slow"]
    res["overheat"] = ma_slow_valid & (ratio > oh_ratio)
    res["cooled"]   = ma_slow_valid & (ratio < cool_ratio)

    # ── Ensure all bool columns are bool dtype (not object) ──────────────────
    bool_cols = [
        "dead_cross", "golden_cross", "regime_bear",
        "dd_exit", "recovery", "overheat", "cooled",
    ]
    for col in bool_cols:
        res[col] = res[col].fillna(False).astype(bool)

    return res
