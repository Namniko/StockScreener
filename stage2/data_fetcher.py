import warnings
import pandas as pd
import yfinance as yf


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

    result = {}

    if len(unique_symbols) == 1:
        sym = unique_symbols[0]
        df = raw.copy()
        df.columns = [c[0] if isinstance(c, tuple) else c for c in df.columns]
        if len(df) >= 20:
            result[sym] = df
        else:
            print(f'  Warning: insufficient history for {sym} ({len(df)} bars)')
        return result

    for sym in unique_symbols:
        try:
            df = raw[sym].copy()
            df = df.dropna(how='all')
            if len(df) < 20:
                print(f'  Warning: insufficient history for {sym} ({len(df)} bars)')
                continue
            result[sym] = df
        except (KeyError, TypeError):
            print(f'  Warning: no data for {sym}')

    return result
