import os
import logging
import pandas as pd
import yfinance as yf

# Configure logger
logger = logging.getLogger(__name__)

def load_prices(ticker: str, start=None, end=None, cache_dir="backtest/data/cache", force_dl=False) -> pd.DataFrame:
    """
    Downloads historical price data using yfinance and caches it locally as a parquet file.
    
    Parameters
    ----------
    ticker : str
        The ticker symbol (e.g., 'QLD').
    start : str or datetime-like, optional
        Start date for slicing the data.
    end : str or datetime-like, optional
        End date for slicing the data.
    cache_dir : str, default 'backtest/data/cache'
        Directory path to store/read the parquet cache.
    force_dl : bool, default False
        If True, force download from yfinance even if cached data exists.
        
    Returns
    -------
    pd.DataFrame
        DataFrame with a tz-naive DatetimeIndex (ascending) and a single float column 'close'.
    """
    os.makedirs(cache_dir, exist_ok=True)
    cache_path = os.path.join(cache_dir, f"{ticker}.parquet")
    
    df = None
    download_success = False
    
    # Try downloading if forced or if cache doesn't exist
    if force_dl or not os.path.exists(cache_path):
        logger.info(f"Downloading historical data for {ticker} from yfinance...")
        try:
            # yfinance download with auto_adjust=True to adjust for stock splits and dividends
            ticker_obj = yf.Ticker(ticker)
            raw_df = ticker_obj.history(period="max", auto_adjust=True)
            
            if raw_df is not None and not raw_df.empty:
                # Process raw data
                df = raw_df.copy()
                
                # yfinance usually returns tz-aware index, convert to tz-naive
                if df.index.tz is not None:
                    df.index = df.index.tz_localize(None)
                
                # Check for 'Close' column (yfinance uses capitalization)
                if 'Close' in df.columns:
                    df = df[['Close']].rename(columns={'Close': 'close'})
                elif 'close' in df.columns:
                    df = df[['close']]
                else:
                    raise KeyError(f"No 'Close' column found in yfinance history for {ticker}")
                
                # Sort ascending, drop NaNs, and drop duplicates
                df = df.sort_index()
                df = df.dropna(subset=['close'])
                df = df[~df.index.duplicated(keep='first')]
                df['close'] = df['close'].astype(float)
                
                # Save to parquet cache
                df.to_parquet(cache_path, engine='pyarrow')
                logger.info(f"Cached data saved to {cache_path}")
                download_success = True
            else:
                logger.warning(f"Downloaded yfinance data for {ticker} was empty.")
        except Exception as e:
            logger.exception(f"Error downloading data for {ticker} from yfinance: {e}")
            
    # Fallback to cache if download failed or wasn't requested
    if df is None:
        if os.path.exists(cache_path):
            logger.info(f"Loading cached data for {ticker} from {cache_path}...")
            try:
                df = pd.read_parquet(cache_path, engine='pyarrow')
                # Ensure index is tz-naive DatetimeIndex
                if df.index.tz is not None:
                    df.index = df.index.tz_localize(None)
                df = df.sort_index()
            except Exception as e:
                logger.error(f"Failed to read parquet cache at {cache_path}: {e}")
                raise
        else:
            msg = f"Failed to load data for {ticker}: download failed and cache file {cache_path} does not exist."
            logger.error(msg)
            raise RuntimeError(msg)
            
    # Slice the data to requested start and end dates
    if start is not None:
        start_dt = pd.to_datetime(start)
        df = df[df.index >= start_dt]
        
    if end is not None:
        end_dt = pd.to_datetime(end)
        df = df[df.index <= end_dt]
        
    # Final check of data properties
    if df.empty:
        logger.warning(f"Data for {ticker} is empty after slicing with start={start}, end={end}")
        
    return df[['close']]
