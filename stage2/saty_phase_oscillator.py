import numpy as np
import pandas as pd


def _classify_zone(value: float) -> str:
    if value > 100:    return 'extreme_up'
    if value >= 61.8:  return 'distribution'
    if value >= 23.6:  return 'neutral_up'
    if value > -23.6:  return 'zero_band'
    if value > -61.8:  return 'neutral_down'
    if value >= -100:  return 'accumulation'
    return 'extreme_down'


def _dot_states(osc_curr: float, osc_prev: float) -> tuple[bool, bool]:
    dot_bull = (osc_prev <= -61.8 and osc_curr > -61.8) or \
               (osc_prev <= -100  and osc_curr > -100)
    dot_bear = (osc_prev >= 61.8  and osc_curr < 61.8) or \
               (osc_prev >= 100   and osc_curr < 100)
    return dot_bull, dot_bear


def _monster_eyes(osc: pd.Series, lookback: int) -> tuple[bool, bool]:
    """
    Monster Eye: 2+ crossings of the ±61.8 boundary within `lookback` bars,
    without the oscillator ever entering the zero band (-23.6 to +23.6).

    Bullish: 2+ upward crossings of -61.8, oscillator never reached > -23.6.
    Bearish: 2+ downward crossings of +61.8, oscillator never reached < +23.6.
    """
    if len(osc) < lookback + 1:
        return False, False

    window = osc.iloc[-lookback:]

    bull_crosses = sum(
        1 for i in range(1, len(window))
        if window.iloc[i - 1] <= -61.8 and window.iloc[i] > -61.8
    )
    monster_bull = bull_crosses >= 2 and float(window.max()) < -23.6

    bear_crosses = sum(
        1 for i in range(1, len(window))
        if window.iloc[i - 1] >= 61.8 and window.iloc[i] < 61.8
    )
    monster_bear = bear_crosses >= 2 and float(window.min()) > 23.6

    return monster_bull, monster_bear


def _detect_divergences(
    price_low:   pd.Series,
    price_high:  pd.Series,
    osc:         pd.Series,
    lb_left:     int,
    lb_right:    int,
    range_lower: int,
    range_upper: int,
) -> dict:
    """
    Pivot-based divergence detection matching the reference PineScript implementation.

    Pivots are detected on the oscillator (lbLeft bars lower on left, lbRight on right).
    The confirmed pivot is lb_right bars before the current bar.
    The previous pivot must have occurred between range_lower and range_upper bars before
    the current pivot. Price comparison uses low (bull) and high (bear), not close.

    Signals:
      bullish_divergence:        price lower low  + osc higher low  (reversal)
      hidden_bullish_divergence: price higher low + osc lower low   (continuation)
      bearish_divergence:        price higher high + osc lower high (reversal)
      hidden_bearish_divergence: price lower high + osc higher high (continuation)
    """
    NO_DIV = {
        'bullish_divergence':        False,
        'hidden_bullish_divergence': False,
        'bearish_divergence':        False,
        'hidden_bearish_divergence': False,
    }

    min_len = lb_left + lb_right + range_upper + 2
    if len(osc) < min_len:
        return NO_DIV

    n     = len(osc)
    p1    = n - 1 - lb_right   # index of the confirmed current pivot

    def is_pivot_low(idx: int) -> bool:
        if idx - lb_left < 0 or idx + lb_right >= n:
            return False
        v = float(osc.iloc[idx])
        return (all(v < float(osc.iloc[idx - j]) for j in range(1, lb_left  + 1)) and
                all(v < float(osc.iloc[idx + j]) for j in range(1, lb_right + 1)))

    def is_pivot_high(idx: int) -> bool:
        if idx - lb_left < 0 or idx + lb_right >= n:
            return False
        v = float(osc.iloc[idx])
        return (all(v > float(osc.iloc[idx - j]) for j in range(1, lb_left  + 1)) and
                all(v > float(osc.iloc[idx + j]) for j in range(1, lb_right + 1)))

    def find_prev_pivot(p1_idx: int, pivot_fn) -> int | None:
        for offset in range(range_lower, range_upper + 1):
            p0 = p1_idx - offset
            if p0 < lb_left:
                break
            if pivot_fn(p0):
                return p0
        return None

    # ── Bullish (pivot lows) ──────────────────────────────────────────────
    bull_div    = False
    hidden_bull = False
    if is_pivot_low(p1):
        p0 = find_prev_pivot(p1, is_pivot_low)
        if p0 is not None:
            osc_p1  = float(osc.iloc[p1]);       osc_p0  = float(osc.iloc[p0])
            low_p1  = float(price_low.iloc[p1]); low_p0  = float(price_low.iloc[p0])
            bull_div    = low_p1 < low_p0 and osc_p1 > osc_p0
            hidden_bull = low_p1 > low_p0 and osc_p1 < osc_p0

    # ── Bearish (pivot highs) ─────────────────────────────────────────────
    bear_div    = False
    hidden_bear = False
    if is_pivot_high(p1):
        p0 = find_prev_pivot(p1, is_pivot_high)
        if p0 is not None:
            osc_p1   = float(osc.iloc[p1]);        osc_p0   = float(osc.iloc[p0])
            high_p1  = float(price_high.iloc[p1]); high_p0  = float(price_high.iloc[p0])
            bear_div    = high_p1 > high_p0 and osc_p1 < osc_p0
            hidden_bear = high_p1 < high_p0 and osc_p1 > osc_p0

    return {
        'bullish_divergence':        bull_div,
        'hidden_bullish_divergence': hidden_bull,
        'bearish_divergence':        bear_div,
        'hidden_bearish_divergence': hidden_bear,
    }


def _compression_tracker(df: pd.DataFrame, pivot: pd.Series, atr: pd.Series) -> np.ndarray:
    """Compute the compression_tracker boolean array matching Pinescript logic."""
    close    = df['Close']
    stdev    = close.rolling(21).std()
    above    = (close >= pivot).values

    bp_up    = (pivot + 2.0 * stdev).values
    bp_down  = (pivot - 2.0 * stdev).values
    ct_up    = (pivot + 2.0   * atr).values
    ct_down  = (pivot - 2.0   * atr).values
    et_up    = (pivot + 1.854 * atr).values
    et_down  = (pivot - 1.854 * atr).values

    compression     = np.where(above, bp_up - ct_up,   ct_down - bp_down)
    in_exp_zone     = np.where(above, bp_up - et_up,   et_down - bp_down)
    prior_comp      = np.roll(compression, 1)
    prior_comp[0]   = compression[0]
    expansion       = prior_comp <= compression

    tracker = np.where(
        expansion & (in_exp_zone > 0), False,
        np.where(compression <= 0, True, False),
    )
    return tracker


def compute(df: pd.DataFrame, params: dict) -> dict:
    ema_p       = params['ema_period']
    atr_p       = params['atr_period']
    smooth      = params['smooth_period']
    me_lb       = int(params.get('monster_eye_lookback', 20))
    div_lb_l    = int(params.get('div_pivot_left',  3))
    div_lb_r    = int(params.get('div_pivot_right', 1))
    div_range_l = int(params.get('div_range_lower', 5))
    div_range_u = int(params.get('div_range_upper', 60))

    close = df['Close']
    high  = df['High']
    low   = df['Low']

    pivot = close.ewm(span=ema_p, adjust=False).mean()

    prev_close = close.shift(1)
    tr = pd.concat([
        high - low,
        (high - prev_close).abs(),
        (low  - prev_close).abs(),
    ], axis=1).max(axis=1)
    atr = tr.rolling(atr_p).mean()

    raw_signal = ((close - pivot) / (3.0 * atr)) * 100
    oscillator = raw_signal.ewm(span=smooth, adjust=False).mean()

    tracker = _compression_tracker(df, pivot, atr)

    osc_curr  = float(oscillator.iloc[-1])
    osc_prev  = float(oscillator.iloc[-2])
    osc_prev2 = float(oscillator.iloc[-3]) if len(oscillator) > 2 else osc_prev

    zone_curr = _classify_zone(osc_curr)
    zone_prev = _classify_zone(osc_prev)

    dot_bull_curr,  dot_bear_curr  = _dot_states(osc_curr,  osc_prev)
    dot_bull_prev,  dot_bear_prev  = _dot_states(osc_prev,  osc_prev2)

    monster_bull, monster_bear = _monster_eyes(oscillator, me_lb)

    in_comp_curr = bool(tracker[-1])
    in_comp_prev = bool(tracker[-2]) if len(tracker) > 1 else False

    div_results = _detect_divergences(
        df['Low'], df['High'], oscillator,
        div_lb_l, div_lb_r, div_range_l, div_range_u,
    )

    return {
        'oscillator':      osc_curr,
        'prev_oscillator': osc_prev,
        'raw_signal':      float(raw_signal.iloc[-1]),
        'pivot':           float(pivot.iloc[-1]),
        'atr':             float(atr.iloc[-1]),

        'zone':      zone_curr,
        'prev_zone': zone_prev,

        'in_extreme_up':    osc_curr > 100,
        'in_distribution':  61.8 <= osc_curr <= 100,
        'in_neutral_up':    23.6 <= osc_curr < 61.8,
        'in_zero_band':     -23.6 < osc_curr < 23.6,
        'in_neutral_down':  -61.8 < osc_curr <= -23.6,
        'in_accumulation':  -100 <= osc_curr <= -61.8,
        'in_extreme_down':  osc_curr < -100,
        'above_zero':       osc_curr > 0,
        'below_zero':       osc_curr < 0,

        'leaving_distribution':     osc_prev >= 61.8  and osc_curr < 61.8,
        'leaving_extreme_up':       osc_prev >= 100   and osc_curr < 100,
        'leaving_accumulation':     osc_prev <= -61.8 and osc_curr > -61.8,
        'leaving_extreme_down':     osc_prev <= -100  and osc_curr > -100,
        'crossed_above_zero':       osc_prev <= 0 and osc_curr > 0,
        'crossed_below_zero':       osc_prev >= 0 and osc_curr < 0,
        'crossed_above_neutral_up': osc_prev < 23.6  and osc_curr >= 23.6,
        'crossed_below_neutral_down': osc_prev > -23.6 and osc_curr <= -23.6,

        'reversion_dot_bull':      dot_bull_curr,
        'reversion_dot_bear':      dot_bear_curr,
        'prev_reversion_dot_bull': dot_bull_prev,
        'prev_reversion_dot_bear': dot_bear_prev,
        'monster_eye_bull':        monster_bull,
        'monster_eye_bear':        monster_bear,

        'oscillator_rising':  osc_curr > osc_prev,
        'oscillator_falling': osc_curr < osc_prev,

        'in_compression':       in_comp_curr,
        'compression_just_ended': in_comp_prev and not in_comp_curr,

        **div_results,
    }
