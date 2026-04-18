import numpy as np
import pandas as pd


def _linreg_value(series: pd.Series, length: int) -> float:
    vals = series.iloc[-length:].values
    if len(vals) < length or np.isnan(vals).any():
        return float('nan')
    x = np.arange(length)
    coeffs = np.polyfit(x, vals, 1)
    return float(np.polyval(coeffs, length - 1))


def _atr(df: pd.DataFrame, period: int = 14) -> float:
    high  = df['High']
    low   = df['Low']
    close = df['Close']
    prev_close = close.shift(1)
    tr = pd.concat([
        high - low,
        (high - prev_close).abs(),
        (low  - prev_close).abs(),
    ], axis=1).max(axis=1)
    return float(tr.iloc[-period:].mean())


def _dot_color(bb_lower, bb_upper, kc_lower_low, kc_upper_low,
               kc_lower_mid, kc_upper_mid, kc_lower_high, kc_upper_high) -> str:
    high_sqz = (bb_lower >= kc_lower_high) or (bb_upper <= kc_upper_high)
    if high_sqz:
        return 'Orange'
    mid_sqz  = (bb_lower >= kc_lower_mid)  or (bb_upper <= kc_upper_mid)
    if mid_sqz:
        return 'Red'
    low_sqz  = (bb_lower >= kc_lower_low)  or (bb_upper <= kc_upper_low)
    if low_sqz:
        return 'Black'
    return 'Green'


def compute(df: pd.DataFrame, params: dict) -> dict:
    length       = params['length']
    bb_mult      = params['bb_mult']
    kc_mult_high = params['kc_mult_high']
    kc_mult_mid  = params['kc_mult_mid']
    kc_mult_low  = params['kc_mult_low']

    close = df['Close']
    high  = df['High']
    low   = df['Low']

    # ── Bollinger Bands ──────────────────────────────────────────────────
    sma   = close.rolling(length).mean()
    std   = close.rolling(length).std(ddof=0)
    bb_upper_s = sma + bb_mult * std
    bb_lower_s = sma - bb_mult * std

    # ── Keltner Channels ─────────────────────────────────────────────────
    prev_close = close.shift(1)
    tr = pd.concat([
        high - low,
        (high - prev_close).abs(),
        (low  - prev_close).abs(),
    ], axis=1).max(axis=1)
    atr_s = tr.rolling(length).mean()

    kc_upper_high_s = sma + kc_mult_high * atr_s
    kc_lower_high_s = sma - kc_mult_high * atr_s
    kc_upper_mid_s  = sma + kc_mult_mid  * atr_s
    kc_lower_mid_s  = sma - kc_mult_mid  * atr_s
    kc_upper_low_s  = sma + kc_mult_low  * atr_s
    kc_lower_low_s  = sma - kc_mult_low  * atr_s

    # ── Dot colors per bar ───────────────────────────────────────────────
    dot_colors = []
    for idx in range(len(df)):
        if pd.isna(bb_lower_s.iloc[idx]):
            dot_colors.append('Green')
            continue
        color = _dot_color(
            bb_lower_s.iloc[idx],   bb_upper_s.iloc[idx],
            kc_lower_low_s.iloc[idx],  kc_upper_low_s.iloc[idx],
            kc_lower_mid_s.iloc[idx],  kc_upper_mid_s.iloc[idx],
            kc_lower_high_s.iloc[idx], kc_upper_high_s.iloc[idx],
        )
        dot_colors.append(color)

    # ── Compression count and squeeze start price ────────────────────────
    compression_bars = 0
    squeeze_start_price = float(close.iloc[-1])
    for k in range(len(dot_colors) - 1, -1, -1):
        if dot_colors[k] == 'Green':
            break
        compression_bars += 1
        squeeze_start_price = float(close.iloc[k])

    current_dot  = dot_colors[-1]
    prev_dot     = dot_colors[-2] if len(dot_colors) >= 2 else 'Green'
    first_green  = (current_dot == 'Green') and (prev_dot != 'Green')

    # ── Momentum oscillator (linear regression of delta) ─────────────────
    donchian_mid = (high.rolling(length).max() + low.rolling(length).min()) / 2
    delta = close - (donchian_mid + sma) / 2

    mom_current = _linreg_value(delta, length)
    mom_prev    = _linreg_value(delta.iloc[:-1], length)

    mom_above_zero = mom_current > 0
    mom_rising     = mom_current > mom_prev

    def _mom_color(mom: float, prev: float) -> str:
        if mom > 0 and mom > prev:   return 'Aqua'
        elif mom > 0:                return 'Blue'
        elif mom < 0 and mom < prev: return 'Red'
        else:                        return 'Yellow'

    mom_color      = _mom_color(mom_current, mom_prev)
    prev_mom_color = _mom_color(mom_prev, _linreg_value(delta.iloc[:-2], length))

    # ── ATR and distance ─────────────────────────────────────────────────
    atr_val = _atr(df)
    if atr_val and atr_val > 0:
        atr_distance = abs(float(close.iloc[-1]) - squeeze_start_price) / atr_val
    else:
        atr_distance = 0.0

    i = -1
    return {
        'dot_color':           current_dot,
        'prev_dot_color':      prev_dot,
        'compression_bars':    compression_bars,
        'momentum_value':      mom_current,
        'prev_momentum_value': mom_prev,
        'momentum_above_zero': mom_above_zero,
        'momentum_rising':     mom_rising,
        'momentum_color':      mom_color,
        'prev_momentum_color': prev_mom_color,
        'squeeze_start_price': squeeze_start_price,
        'atr':                 atr_val,
        'atr_distance':        atr_distance,
        'first_green_dot':     first_green,
        'bb_upper':            float(bb_upper_s.iloc[i]),
        'bb_lower':            float(bb_lower_s.iloc[i]),
        'kc_upper_low':        float(kc_upper_low_s.iloc[i]),
        'kc_lower_low':        float(kc_lower_low_s.iloc[i]),
        'kc_upper_mid':        float(kc_upper_mid_s.iloc[i]),
        'kc_lower_mid':        float(kc_lower_mid_s.iloc[i]),
        'kc_upper_high':       float(kc_upper_high_s.iloc[i]),
        'kc_lower_high':       float(kc_lower_high_s.iloc[i]),
    }
