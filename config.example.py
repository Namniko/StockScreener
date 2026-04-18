STAGE1 = {
    # ── Universe ────────────────────────────────────────────
    'market': 'america',
    'index': None,

    # ── Instrument type ──────────────────────────────────────
    'type': 'stock',
    'typespecs': ['common'],

    # ── Fundamental filters ──────────────────────────────────
    'min_market_cap':    1_000_000_000,
    'max_market_cap':    None,
    'min_price':         5.0,
    'max_price':         None,
    'min_avg_volume':    500_000,
    'min_rel_volume':    None,
    'sectors':           None,
    'exchanges':         None,

    # ── Native TV indicator filters ──────────────────────────
    'native_filters': {
        'ema21_above_ema48':    True,
        'ema48_above_ema200':   True,
        'ema8_above_ema21':     None,
        'close_above_ema21':    True,
        'close_below_ema21':    None,
        'close_above_ema48':    None,
        'close_below_ema48':    None,
        'low_below_ema21':      True,
        'low_below_ema8':       None,
        'high_above_ema21':     None,
        'ema8_crossed_above_ema21':    None,
        'ema21_crossed_above_ema48':   None,
        'ema21_crossed_above_ema200':  None,
        'ema21_crossed_below_ema200':  None,
        'rsi_min':              None,
        'rsi_max':              None,
        'macd_above_signal':    None,
        'macd_below_signal':    None,
        'min_rel_volume':       None,
    },

    # ── Query settings ───────────────────────────────────────
    'sort_by':       'market_cap_basic',
    'sort_asc':      False,
    'max_results':   200,
    'history_days':  300,   # needs 300+ bars for EMA200 to converge
}

INDICATORS = {

    'saty_ribbon': {
        'module': 'stage2.saty_ribbon',
        'params': {
            'fast_ema':      8,
            'secondary_ema': 13,
            'pivot_ema':     21,
            'slow_ema':      48,
            'longterm_ema':  200,
        },
        'output_fields': [
            'ema8', 'ema13', 'ema21', 'ema48', 'ema200',
            'close', 'high', 'low', 'open',
            'close_above_ema8',   'close_above_ema13',
            'close_above_ema21',  'close_above_ema48',
            'close_above_ema200',
            'low_touched_ema8',   'low_touched_ema13',
            'low_touched_ema21',
            'high_touched_ema8',  'high_touched_ema13',
            'high_touched_ema21',
            'ema8_above_ema13',   'ema13_above_ema21',
            'ema21_above_ema48',  'ema48_above_ema200',
            'ema8_above_ema21',   'ema8_above_ema48',
            'ema21_above_ema200',
            'ema8_slope',
            'ema13_slope',
            'ema21_slope',
            'ema48_slope',
            'ema200_slope',
            'ema8_slope_positive',
            'ema21_slope_positive',
            'ema48_slope_positive',
            'ema8_ema13_gap_pct',
            'ema21_ema48_gap_pct',
            'ema48_ema200_gap_pct',
            'ema21_crossed_above_ema48_recently',
            'ema21_crossed_below_ema48_recently',
            'ema21_crossed_above_ema200_recently',
            'ema21_crossed_below_ema200_recently',
            'prev_close_above_ema21',
            'prev_close_above_ema48',
        ],
        'subconditions': {
            'max_bull': {
                'ema8_above_ema13':   True,
                'ema13_above_ema21':  True,
                'ema21_above_ema48':  True,
                'ema48_above_ema200': True,
                'close_above_ema8':   True,
            },
            'strong_bull': {
                'ema8_above_ema21':   True,
                'ema21_above_ema48':  True,
                'ema48_above_ema200': True,
                'close_above_ema21':  True,
            },
            'pullback_buy': {
                'close_above_ema21':  True,
                'low_touched_ema21':  True,
                'ema21_above_ema48':  True,
            },
            'pullback_buy_strong': {
                'close_above_ema21':  True,
                'low_touched_ema21':  True,
                'ema8_above_ema13':   True,
                'ema13_above_ema21':  True,
                'ema21_above_ema48':  True,
                'ema48_above_ema200': True,
            },
            'pullback_buy_ema8': {
                'close_above_ema8':   True,
                'low_touched_ema8':   True,
                'ema8_above_ema21':   True,
                'ema21_above_ema48':  True,
            },
            'bullish_bias': {
                'close_above_ema21':  True,
            },
            'max_bear': {
                'ema8_above_ema13':   False,
                'ema13_above_ema21':  False,
                'ema21_above_ema48':  False,
                'ema48_above_ema200': False,
                'close_above_ema8':   False,
            },
            'pullback_short': {
                'close_above_ema21':  False,
                'high_touched_ema21': True,
                'ema21_above_ema48':  False,
            },
            'bearish_bias': {
                'close_above_ema21':  False,
            },
            'vomy_warning': {
                'ema8_above_ema13':      True,
                'ema8_slope_positive':   False,
                'ema8_ema13_gap_pct':    0.5,
            },
            'golden_cross': {
                'ema21_crossed_above_ema200_recently': True,
            },
            'death_cross': {
                'ema21_crossed_below_ema200_recently': True,
            },
        }
    },

    'ttm_squeeze': {
        'module': 'stage2.ttm_squeeze',
        'params': {
            'length':       20,
            'bb_mult':      2.0,
            'kc_mult_high': 1.0,
            'kc_mult_mid':  1.5,
            'kc_mult_low':  2.0,
        },
        'output_fields': [
            'dot_color',
            'prev_dot_color',
            'compression_bars',
            'momentum_value',
            'prev_momentum_value',
            'momentum_above_zero',
            'momentum_rising',
            'momentum_color',
            'prev_momentum_color',
            'squeeze_start_price',
            'atr',
            'atr_distance',
            'first_green_dot',
            'bb_upper', 'bb_lower',
            'kc_upper_low', 'kc_lower_low',
            'kc_upper_mid', 'kc_lower_mid',
            'kc_upper_high', 'kc_lower_high',
        ],
        'subconditions': {
            'anticipatory_bull': {
                'dot_color':           ['Orange', 'Red'],
                'compression_bars__gte': 5,
                'momentum_above_zero': True,
                'momentum_rising':     True,
            },
            'anticipatory_bull_orange': {
                'dot_color':           ['Orange'],
                'momentum_above_zero': True,
                'momentum_rising':     True,
            },
            'anticipatory_bear': {
                'dot_color':           ['Orange', 'Red'],
                'compression_bars__gte': 5,
                'momentum_above_zero': False,
                'momentum_rising':     False,
            },
            'anticipatory_bear_orange': {
                'dot_color':           ['Orange'],
                'momentum_above_zero': False,
                'momentum_rising':     False,
            },
            'confirmed_bull': {
                'first_green_dot':     True,
                'momentum_above_zero': True,
                'atr_distance__lte':   1.0,
            },
            'confirmed_bear': {
                'first_green_dot':     True,
                'momentum_above_zero': False,
                'atr_distance__lte':   1.0,
            },
            'late_bull': {
                'first_green_dot':     True,
                'momentum_above_zero': True,
                'atr_distance__gt':    1.0,
            },
            'late_bear': {
                'first_green_dot':     True,
                'momentum_above_zero': False,
                'atr_distance__gt':    1.0,
            },
            'exit_long': {
                'momentum_color':      ['Blue'],
                'prev_momentum_color': ['Blue'],
            },
            'exit_short': {
                'momentum_color':      ['Yellow'],
                'prev_momentum_color': ['Yellow'],
            },
            'med_bullish': {
                'dot_color':           ['Orange', 'Red', 'Black'],
                'compression_bars__gte': 3,
                'momentum_above_zero': True,
            },
            'high_compression': {
                'dot_color':           ['Orange'],
                'compression_bars__gte': 3,
            },
            'building': {
                'dot_color':           ['Black', 'Red', 'Orange'],
                'compression_bars__gte': 1,
            },
        }
    },

}
