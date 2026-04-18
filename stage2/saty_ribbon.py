import pandas as pd


def compute(df: pd.DataFrame, params: dict) -> dict:
    fast      = params['fast_ema']
    secondary = params['secondary_ema']
    pivot     = params['pivot_ema']
    slow      = params['slow_ema']
    longterm  = params['longterm_ema']

    close = df['Close']
    high  = df['High']
    low   = df['Low']
    open_ = df['Open']

    ema8   = close.ewm(span=fast,      adjust=False).mean()
    ema13  = close.ewm(span=secondary, adjust=False).mean()
    ema21  = close.ewm(span=pivot,     adjust=False).mean()
    ema48  = close.ewm(span=slow,      adjust=False).mean()
    ema200 = close.ewm(span=longterm,  adjust=False).mean()

    slope8   = ema8.diff(3)
    slope13  = ema13.diff(3)
    slope21  = ema21.diff(3)
    slope48  = ema48.diff(3)
    slope200 = ema200.diff(3)

    def _crossed_recently(series_a: pd.Series, series_b: pd.Series, above: bool, n: int = 3) -> bool:
        diff = series_a - series_b
        if len(diff) < n + 1:
            return False
        recent = diff.iloc[-(n + 1):]
        if above:
            return bool((recent.iloc[0] < 0) and (recent.iloc[-1] >= 0))
        else:
            return bool((recent.iloc[0] > 0) and (recent.iloc[-1] <= 0))

    i   = -1   # current bar
    ip  = -2   # previous bar

    c    = float(close.iloc[i])
    h    = float(high.iloc[i])
    l    = float(low.iloc[i])
    o    = float(open_.iloc[i])
    e8   = float(ema8.iloc[i])
    e13  = float(ema13.iloc[i])
    e21  = float(ema21.iloc[i])
    e48  = float(ema48.iloc[i])
    e200 = float(ema200.iloc[i])

    def _gap_pct(a: float, b: float) -> float:
        return abs(a - b) / b * 100 if b != 0 else 0.0

    return {
        'ema8':   e8,
        'ema13':  e13,
        'ema21':  e21,
        'ema48':  e48,
        'ema200': e200,
        'close':  c,
        'high':   h,
        'low':    l,
        'open':   o,

        'close_above_ema8':   c > e8,
        'close_above_ema13':  c > e13,
        'close_above_ema21':  c > e21,
        'close_above_ema48':  c > e48,
        'close_above_ema200': c > e200,

        'low_touched_ema8':   float(low.iloc[i]) <= e8,
        'low_touched_ema13':  float(low.iloc[i]) <= e13,
        'low_touched_ema21':  float(low.iloc[i]) <= e21,

        'high_touched_ema8':   float(high.iloc[i]) >= e8,
        'high_touched_ema13':  float(high.iloc[i]) >= e13,
        'high_touched_ema21':  float(high.iloc[i]) >= e21,

        'ema8_above_ema13':   e8  > e13,
        'ema13_above_ema21':  e13 > e21,
        'ema21_above_ema48':  e21 > e48,
        'ema48_above_ema200': e48 > e200,
        'ema8_above_ema21':   e8  > e21,
        'ema8_above_ema48':   e8  > e48,
        'ema21_above_ema200': e21 > e200,

        'ema8_slope':   float(slope8.iloc[i]),
        'ema13_slope':  float(slope13.iloc[i]),
        'ema21_slope':  float(slope21.iloc[i]),
        'ema48_slope':  float(slope48.iloc[i]),
        'ema200_slope': float(slope200.iloc[i]),

        'ema8_slope_positive':  float(slope8.iloc[i])  > 0,
        'ema21_slope_positive': float(slope21.iloc[i]) > 0,
        'ema48_slope_positive': float(slope48.iloc[i]) > 0,

        'ema8_ema13_gap_pct':   _gap_pct(e8, e13),
        'ema21_ema48_gap_pct':  _gap_pct(e21, e48),
        'ema48_ema200_gap_pct': _gap_pct(e48, e200),

        'ema21_crossed_above_ema48_recently':   _crossed_recently(ema21, ema48,  above=True),
        'ema21_crossed_below_ema48_recently':   _crossed_recently(ema21, ema48,  above=False),
        'ema21_crossed_above_ema200_recently':  _crossed_recently(ema21, ema200, above=True),
        'ema21_crossed_below_ema200_recently':  _crossed_recently(ema21, ema200, above=False),

        'prev_close_above_ema21': float(close.iloc[ip]) > float(ema21.iloc[ip]),
        'prev_close_above_ema48': float(close.iloc[ip]) > float(ema48.iloc[ip]),
    }
