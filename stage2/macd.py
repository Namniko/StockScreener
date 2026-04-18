import numpy as np
import pandas as pd


def _detect_divergence(price: pd.Series, macd: pd.Series, lookback: int) -> tuple[bool, bool]:
    if len(price) < lookback + 1:
        return False, False

    window_price = price.iloc[-lookback:-1]
    window_macd  = macd.iloc[-lookback:-1]
    curr_price   = float(price.iloc[-1])
    curr_macd    = float(macd.iloc[-1])

    low_idx  = window_price.idxmin()
    high_idx = window_price.idxmax()

    prior_price_low  = float(price[low_idx])
    prior_macd_low   = float(macd[low_idx])
    prior_price_high = float(price[high_idx])
    prior_macd_high  = float(macd[high_idx])

    bullish = (curr_price < prior_price_low) and (curr_macd > prior_macd_low)
    bearish = (curr_price > prior_price_high) and (curr_macd < prior_macd_high)
    return bullish, bearish


def compute(df: pd.DataFrame, params: dict) -> dict:
    fast     = params['fast_period']
    slow     = params['slow_period']
    signal   = params['signal_period']
    div_lb   = min(int(params.get('divergence_lookback', 14)), 50)

    close = df['Close']

    ema_fast    = close.ewm(span=fast,   adjust=False).mean()
    ema_slow    = close.ewm(span=slow,   adjust=False).mean()
    macd_line   = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    histogram   = macd_line - signal_line

    ml  = float(macd_line.iloc[-1])
    sl  = float(signal_line.iloc[-1])
    h   = float(histogram.iloc[-1])
    pml = float(macd_line.iloc[-2])
    psl = float(signal_line.iloc[-2])
    ph  = float(histogram.iloc[-2])
    c   = float(close.iloc[-1])

    macd_signal_gap     = abs(ml - sl)
    macd_signal_gap_pct = macd_signal_gap / c * 100 if c != 0 else 0.0

    bull_div, bear_div = _detect_divergence(close, macd_line, div_lb)

    return {
        'macd_line':            ml,
        'signal_line':          sl,
        'histogram':            h,
        'prev_macd_line':       pml,
        'prev_signal_line':     psl,
        'prev_histogram':       ph,

        'macd_above_zero':           ml > 0,
        'macd_below_zero':           ml < 0,
        'macd_crossed_above_zero':   pml < 0 and ml > 0,
        'macd_crossed_below_zero':   pml > 0 and ml < 0,

        'macd_above_signal':         ml > sl,
        'macd_below_signal':         ml < sl,
        'macd_crossed_above_signal': (ml - sl) > 0 and (pml - psl) <= 0,
        'macd_crossed_below_signal': (ml - sl) < 0 and (pml - psl) >= 0,

        'histogram_positive':           h > 0,
        'histogram_negative':           h < 0,
        'histogram_rising':             h > ph,
        'histogram_falling':            h < ph,
        'histogram_above_zero_rising':  h > 0 and h > ph,
        'histogram_below_zero_falling': h < 0 and h < ph,
        'histogram_above_zero_falling': h > 0 and h < ph,
        'histogram_below_zero_rising':  h < 0 and h > ph,

        'bullish_divergence': bull_div,
        'bearish_divergence': bear_div,

        'macd_signal_gap':     macd_signal_gap,
        'macd_signal_gap_pct': macd_signal_gap_pct,
        'histogram_magnitude': abs(h),
    }
