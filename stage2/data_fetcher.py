import warnings
import pandas as pd
import yfinance as yf


def _unpack_yfinance(raw, unique_symbols: list[str], min_bars: int) -> dict[str, pd.DataFrame]:
    result = {}
    if len(unique_symbols) == 1:
        sym = unique_symbols[0]
        df = raw.copy()
        df.columns = [c[0] if isinstance(c, tuple) else c for c in df.columns]
        df = df.dropna(how='all')
        if len(df) >= min_bars:
            result[sym] = df
        else:
            print(f'  Warning: insufficient history for {sym} ({len(df)} bars)')
        return result

    for sym in unique_symbols:
        try:
            df = raw[sym].copy()
            df = df.dropna(how='all')
            if len(df) < min_bars:
                print(f'  Warning: insufficient history for {sym} ({len(df)} bars)')
                continue
            result[sym] = df
        except (KeyError, TypeError):
            print(f'  Warning: no data for {sym}')

    return result


def fetch_history(tickers: list[str], days: int) -> dict[str, pd.DataFrame]:
    symbols = [t.split(':')[-1] for t in tickers]
    unique_symbols = list(dict.fromkeys(symbols))

    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        raw = yf.download(
            unique_symbols,
            period=f'{days}d',
            interval='1d',
            group_by='ticker',
            auto_adjust=True,
            progress=False,
        )

    return _unpack_yfinance(raw, unique_symbols, min_bars=20)


def fetch_history_weekly(tickers: list[str], weeks: int) -> dict[str, pd.DataFrame]:
    """
    Fetch weekly OHLC bars for each ticker.
    weeks: number of weekly bars to request (e.g. 100 = ~2 years).
    Returns {symbol: DataFrame} with the same column structure as fetch_history.
    """
    symbols = [t.split(':')[-1] for t in tickers]
    unique_symbols = list(dict.fromkeys(symbols))
    # yfinance period is in calendar days; 1 week ≈ 7 calendar days
    period_days = weeks * 7

    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        raw = yf.download(
            unique_symbols,
            period=f'{period_days}d',
            interval='1wk',
            group_by='ticker',
            auto_adjust=True,
            progress=False,
        )

    return _unpack_yfinance(raw, unique_symbols, min_bars=10)
