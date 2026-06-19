import numpy as np
import pandas as pd

def annotate_signals(df: pd.DataFrame, params: dict) -> pd.DataFrame:
    """
    Annotates the price DataFrame with indicators and trading triggers.
    
    Parameters
    ----------
    df : pd.DataFrame
        DataFrame with a tz-naive DatetimeIndex (ascending) and a single float column 'close'.
    params : dict
        Parameters dictionary adhering to the specified schema.
        
    Returns
    -------
    pd.DataFrame
        DataFrame with the original data and additional indicator/signal columns:
        - 'ma200': 200-day Simple Moving Average.
        - 'below_ma200_streak': Count of consecutive days close is below ma200.
        - 'ath': Running maximum close.
        - 'confirmed_low': The latest confirmed swing low (lookforward L days).
        - 'trig_t1': Boolean trigger for ATH -a%
        - 'trig_t2': Boolean trigger for ATH -b%
        - 'trig_t3': Boolean trigger for ConfirmedLow +e%
        - 'trig_t4': Boolean trigger for ConfirmedLow +f%
        - 'new_ath': Boolean, True on the day a new ATH is established.
        - 'new_low': Boolean, True on the day a new local low is confirmed.
    """
    # Create a copy to prevent modifying the original DataFrame
    res = df.copy()
    res = res.sort_index()
    
    # Ensure 'close' is present
    if 'close' not in res.columns:
        raise KeyError("Input DataFrame must contain a 'close' column.")
        
    # 1. 200-day Moving Average
    res['ma200'] = res['close'].rolling(window=200).mean()
    
    # 2. Running Maximum Close (ATH)
    res['ath'] = res['close'].cummax()
    res['new_ath'] = res['close'] > res['ath'].shift(1)
    res['new_ath'] = res['new_ath'].fillna(False)
    
    # Get parameters
    L = params.get('pivot_lookback', 10)
    min_move = params.get('pivot_min_move', 0.05)
    
    strategy_params = params.get('strategy', {})
    a = strategy_params.get('a', 10.0)
    b = strategy_params.get('b', 15.0)
    e = strategy_params.get('e', 10.0)
    f = strategy_params.get('f', 20.0)
    
    n_rows = len(res)
    close_vals = res['close'].values
    ma200_vals = res['ma200'].values
    
    below_ma200_streak = np.zeros(n_rows, dtype=int)
    confirmed_low = np.full(n_rows, np.nan)
    new_low = np.full(n_rows, False)
    
    streak = 0
    last_low = np.nan
    
    # Compute indicators requiring sequential iteration
    for t in range(n_rows):
        # Calculate ma200 streak
        ma_val = ma200_vals[t]
        if not np.isnan(ma_val) and close_vals[t] < ma_val:
            streak += 1
        else:
            streak = 0
        below_ma200_streak[t] = streak
        
        # Calculate confirmed swing low (with lookforward L days)
        if t >= 2 * L:
            idx_candidate = t - L
            window = close_vals[t - 2 * L : t + 1]
            candidate_price = close_vals[idx_candidate]
            
            # If the candidate is the minimum price in the lookback+lookforward window
            if candidate_price == np.min(window):
                # Apply min_move filter vs the previously confirmed low
                if np.isnan(last_low) or (abs(candidate_price - last_low) / last_low >= min_move):
                    last_low = candidate_price
                    new_low[t] = True
                    
        confirmed_low[t] = last_low
        
    res['below_ma200_streak'] = below_ma200_streak
    res['confirmed_low'] = confirmed_low
    res['new_low'] = new_low
    
    # 3. Compute Buying Triggers
    res['trig_t1'] = res['close'] <= res['ath'] * (1.0 - a / 100.0)
    res['trig_t2'] = res['close'] <= res['ath'] * (1.0 - b / 100.0)
    
    res['trig_t3'] = (res['close'] >= res['confirmed_low'] * (1.0 + e / 100.0)) & res['confirmed_low'].notna()
    res['trig_t4'] = (res['close'] >= res['confirmed_low'] * (1.0 + f / 100.0)) & res['confirmed_low'].notna()
    
    return res
