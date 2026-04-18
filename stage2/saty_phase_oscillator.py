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


def _detect_divergences(price: pd.Series, osc: pd.Series, lookback: int) -> dict:
    if len(price) < lookback + 1:
        falses = {k: False for k in [
            'bullish_divergence_class_a', 'bullish_divergence_class_b',
            'bullish_divergence_class_c', 'hidden_bullish_divergence',
            'bearish_divergence_class_a', 'bearish_divergence_class_b',
            'bearish_divergence_class_c', 'hidden_bearish_divergence',
            'any_bullish_divergence', 'any_bearish_divergence',
            'strong_bullish_divergence', 'strong_bearish_divergence',
        ]}
        return falses

    tolerance = 0.02
    window_p  = price.iloc[-lookback:-1]
    curr_p    = float(price.iloc[-1])
    curr_o    = float(osc.iloc[-1])

    low_idx       = window_p.idxmin()
    high_idx      = window_p.idxmax()
    prior_p_low   = float(price[low_idx])
    prior_o_low   = float(osc[low_idx])
    prior_p_high  = float(price[high_idx])
    prior_o_high  = float(osc[high_idx])

    # Bullish reversal
    bull_a = (curr_p < prior_p_low) and (curr_o > prior_o_low)

    p_dbl_bot = abs(curr_p - prior_p_low) / max(abs(prior_p_low), 1e-9) < tolerance
    bull_b    = p_dbl_bot and (curr_o > prior_o_low) and not bull_a

    o_eq_low = abs(curr_o - prior_o_low) < (abs(prior_o_low) * tolerance + 1.0)
    bull_c   = (curr_p < prior_p_low) and o_eq_low and not bull_a

    hidden_bull = (curr_p > prior_p_low) and (curr_o < prior_o_low)

    # Bearish reversal
    bear_a = (curr_p > prior_p_high) and (curr_o < prior_o_high)

    p_dbl_top = abs(curr_p - prior_p_high) / max(abs(prior_p_high), 1e-9) < tolerance
    bear_b    = p_dbl_top and (curr_o < prior_o_high) and not bear_a

    o_eq_high = abs(curr_o - prior_o_high) < (abs(prior_o_high) * tolerance + 1.0)
    bear_c    = (curr_p > prior_p_high) and o_eq_high and not bear_a

    hidden_bear = (curr_p < prior_p_high) and (curr_o > prior_o_high)

    return {
        'bullish_divergence_class_a': bull_a,
        'bullish_divergence_class_b': bull_b,
        'bullish_divergence_class_c': bull_c,
        'hidden_bullish_divergence':  hidden_bull,
        'bearish_divergence_class_a': bear_a,
        'bearish_divergence_class_b': bear_b,
        'bearish_divergence_class_c': bear_c,
        'hidden_bearish_divergence':  hidden_bear,
        'any_bullish_divergence':     bull_a or bull_b or bull_c,
        'any_bearish_divergence':     bear_a or bear_b or bear_c,
        'strong_bullish_divergence':  bull_a,
        'strong_bearish_divergence':  bear_a,
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
    ema_p   = params['ema_period']
    atr_p   = params['atr_period']
    smooth  = params['smooth_period']
    div_lb  = min(int(params.get('divergence_lookback', 20)), 50)

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

    monster_bull = dot_bull_curr and dot_bull_prev
    monster_bear = dot_bear_curr and dot_bear_prev

    in_comp_curr = bool(tracker[-1])
    in_comp_prev = bool(tracker[-2]) if len(tracker) > 1 else False

    div_results = _detect_divergences(close, oscillator, div_lb)

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
