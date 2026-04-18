import numpy as np
import pandas as pd


def compute(df: pd.DataFrame, params: dict) -> dict:
    period    = params['period']
    mult      = params['std_dev_mult']
    bw_lb     = int(params.get('bandwidth_lookback', 125))

    close = df['Close']

    middle_s = close.rolling(period).mean()
    std_s    = close.rolling(period).std()          # ddof=1 matches TradingView
    upper_s  = middle_s + mult * std_s
    lower_s  = middle_s - mult * std_s

    band_width = upper_s - lower_s
    percent_b_s = (close - lower_s) / band_width.replace(0, np.nan)
    bandwidth_s = band_width / middle_s.replace(0, np.nan)

    # Bandwidth percentile: fraction of last bw_lb bars that are below current bandwidth
    bandwidth_pct_s = bandwidth_s.rolling(bw_lb).apply(
        lambda x: float((x[:-1] < x[-1]).sum()) / (len(x) - 1) * 100 if len(x) > 1 else 50.0,
        raw=True,
    )

    # Band walk: consecutive bars where percent_b >= 0.8 (upper) or <= 0.2 (lower)
    walk_upper = 0
    walk_lower = 0
    for k in range(len(df) - 1, max(len(df) - 20, 0) - 1, -1):
        pb = percent_b_s.iloc[k]
        if np.isnan(pb):
            break
        if pb >= 0.8:
            walk_upper += 1
        else:
            break
    for k in range(len(df) - 1, max(len(df) - 20, 0) - 1, -1):
        pb = percent_b_s.iloc[k]
        if np.isnan(pb):
            break
        if pb <= 0.2:
            walk_lower += 1
        else:
            break

    # Current and previous bar values
    ub  = float(upper_s.iloc[-1])
    mb  = float(middle_s.iloc[-1])
    lb  = float(lower_s.iloc[-1])
    pub = float(upper_s.iloc[-2])
    pmb = float(middle_s.iloc[-2])
    plb = float(lower_s.iloc[-2])
    c   = float(close.iloc[-1])
    pc  = float(close.iloc[-2])
    pb  = float(percent_b_s.iloc[-1]) if not np.isnan(percent_b_s.iloc[-1]) else 0.5
    ppb = float(percent_b_s.iloc[-2]) if not np.isnan(percent_b_s.iloc[-2]) else 0.5
    bw  = float(bandwidth_s.iloc[-1]) if not np.isnan(bandwidth_s.iloc[-1]) else 0.0
    pbw = float(bandwidth_s.iloc[-2]) if not np.isnan(bandwidth_s.iloc[-2]) else 0.0
    bwp = float(bandwidth_pct_s.iloc[-1]) if not np.isnan(bandwidth_pct_s.iloc[-1]) else 50.0
    pbwp = float(bandwidth_pct_s.iloc[-2]) if not np.isnan(bandwidth_pct_s.iloc[-2]) else 50.0

    is_squeeze      = bwp <= 20.0
    prev_is_squeeze = pbwp <= 20.0
    squeeze_fired   = prev_is_squeeze and not is_squeeze

    breakout_upper      = c > ub
    breakout_lower      = c < lb
    prev_breakout_upper = pc > pub
    prev_breakout_lower = pc < plb

    return {
        'upper_band':       ub,
        'middle_band':      mb,
        'lower_band':       lb,
        'prev_upper_band':  pub,
        'prev_middle_band': pmb,
        'prev_lower_band':  plb,

        'close':            c,
        'percent_b':        pb,
        'prev_percent_b':   ppb,

        'close_above_middle': c > mb,
        'close_below_middle': c < mb,
        'close_above_upper':  c > ub,
        'close_below_lower':  c < lb,
        'close_near_upper':   pb >= 0.8,
        'close_near_lower':   pb <= 0.2,

        'crossed_above_middle': pc < pmb and c > mb,
        'crossed_below_middle': pc > pmb and c < mb,

        'bandwidth':            bw,
        'prev_bandwidth':       pbw,
        'bandwidth_expanding':  bw > pbw,
        'bandwidth_contracting': bw < pbw,
        'bandwidth_percentile': bwp,
        'is_squeeze':           is_squeeze,
        'squeeze_just_fired':   squeeze_fired,

        'walking_upper_band':   walk_upper >= 3,
        'walking_lower_band':   walk_lower >= 3,
        'walk_upper_bar_count': walk_upper,
        'walk_lower_bar_count': walk_lower,

        'breakout_upper':      breakout_upper,
        'breakout_lower':      breakout_lower,
        'prev_breakout_upper': prev_breakout_upper,
        'prev_breakout_lower': prev_breakout_lower,
        'breakout_upper_new':  breakout_upper and not prev_breakout_upper,
        'breakout_lower_new':  breakout_lower and not prev_breakout_lower,
        'returned_inside_from_upper': prev_breakout_upper and not breakout_upper,
        'returned_inside_from_lower': prev_breakout_lower and not breakout_lower,

        'upper_band_rejection': prev_breakout_upper and not breakout_upper,
        'lower_band_rejection': prev_breakout_lower and not breakout_lower,

        'bullish_trend': c > mb and bw > pbw,
        'bearish_trend': c < mb and bw > pbw,
    }
