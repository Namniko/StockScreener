STAGE1 = {
    # ── Universe ────────────────────────────────────────────
    # market: string (single) or list of strings (multi-market scan)
    # Example: 'america'  |  ['america', 'canada']
    # Valid values —
    #   Equity:     america, uk, germany, france, italy, spain, netherlands,
    #               switzerland, sweden, norway, denmark, finland, belgium, austria,
    #               portugal, poland, hungary, czech, romania, turkey, russia,
    #               india, china, japan, hongkong, taiwan, korea, singapore,
    #               australia, newzealand, canada, brazil, mexico, argentina, chile,
    #               colombia, peru, nigeria, egypt, kenya, uae, israel, qatar,
    #               kuwait, bahrain, rsa, ksa, indonesia, malaysia, thailand,
    #               vietnam, philippines, pakistan, bangladesh, srilanka
    #   Non-equity: crypto, forex, futures, bonds, cfd, coin
    #               (EMA/fundamental filters do not apply to non-equity markets)
    'market': 'america',
    # index: string or list of strings. Scopes the scan to a specific index.
    #   Overrides 'market' — when set, market is ignored.
    #   Format: 'SYML:{source};{symbol}'
    # Example: 'SYML:SP;SPX'  |  ['SYML:SP;SPX', 'SYML:SP;MID']
    # Verified working values —
    #   US:            SYML:SP;SPX       (S&P 500, ~503)
    #                  SYML:SP;MID       (S&P 400 MidCap, ~399)
    #                  SYML:NASDAQ;NDX   (Nasdaq 100)
    #                  SYML:DJ;DJI       (Dow Jones 30)
    #   International: SYML:TVC;UKX      (FTSE 100)
    #                  SYML:TVC;NI225    (Nikkei 225)
    #                  SYML:NSE;NIFTY    (Nifty 50)
    #                  SYML:TSX;TX60     (TSX 60)
    #                  SYML:XETR;DAX     (DAX 40)
    #                  SYML:ASX;XJO      (ASX 200)
    #                  SYML:KRX;KOSPI    (KOSPI)
    #   Other indices follow the same SYML:{source};{symbol} pattern.
    #   Russell 2000 and S&P 600 are not accessible via this API.
    'index': None,

    # ── Instrument type ──────────────────────────────────────
    # type: string or None. Filters by instrument category.
    # Example: 'stock'  |  'fund'  |  None (no filter)
    # Valid values (america market) —
    #   'stock'   common stocks, preferred shares, ADRs  (~11k)
    #   'fund'    ETFs, REITs, trusts, closed-end funds  (~6k)
    #   'dr'      depositary receipts                    (~1.5k)
    #   None      no filter (all instrument types)
    'type': 'stock',
    # typespecs: list of strings or None. Narrows within the type category.
    #   Used with col('typespecs').has([...]) — matches if instrument has ALL listed specs.
    # Example: ['common']  |  ['etf']  |  None (no filter)
    # Valid values —
    #   For type='stock':  'common', 'preferred'
    #   For type='fund':   'etf', 'reit', 'trust', 'unit', 'mutual'
    #   For type='dr':     typespecs is typically empty — set to None
    'typespecs': ['common'],

    # ── Fundamental filters ──────────────────────────────────
    # All numeric filters: None = disabled.
    'min_market_cap':    1_000_000_000,   # raw USD   e.g. 1_000_000_000 = $1B
    'max_market_cap':    None,            # raw USD
    'min_price':         5.0,             # USD per share
    'max_price':         None,            # USD per share
    'min_avg_volume':    500_000,         # shares  (10-day average)
    'min_rel_volume':    None,            # ratio   e.g. 1.5 = 50% above average
    # sectors: list of strings or None. Filters by TradingView sector classification.
    # Example: ['Technology Services', 'Electronic Technology']  |  None (all sectors)
    # Valid values —
    #   'Commercial Services', 'Communications', 'Consumer Durables',
    #   'Consumer Non-Durables', 'Consumer Services', 'Distribution Services',
    #   'Electronic Technology', 'Energy Minerals', 'Finance',
    #   'Health Services', 'Health Technology', 'Industrial Services',
    #   'Miscellaneous', 'Non-Energy Minerals', 'Process Industries',
    #   'Producer Manufacturing', 'Retail Trade', 'Technology Services',
    #   'Transportation', 'Utilities'
    'sectors': None,
    # exchanges: list of strings or None. Filters by listing exchange.
    # Example: ['NASDAQ', 'NYSE']  |  None (all exchanges)
    # Valid values (america market): 'NASDAQ', 'NYSE', 'AMEX', 'OTC'
    'exchanges': None,


    # ── Query settings ───────────────────────────────────────
    # sort_by: string. Field to sort Stage 1 results by before applying max_results cap.
    # Example: 'market_cap_basic'  |  'relative_volume_10d_calc'  |  'Perf.W'
    # Useful values —
    #   Size/liquidity:  'market_cap_basic', 'volume', 'average_volume_10d_calc',
    #                    'relative_volume_10d_calc', 'float_shares_outstanding'
    #   Price/momentum:  'close', 'change', 'change_abs',
    #                    'Perf.W', 'Perf.1M', 'Perf.3M', 'Perf.6M', 'Perf.Y', 'Perf.YTD'
    #   Technicals:      'RSI', 'ATR'
    #   Fundamentals:    'price_earnings_ttm', 'price_sales_ratio', 'return_on_equity',
    #                    'debt_to_equity', 'earnings_per_share_basic_ttm',
    #                    'dividends_yield_current', 'beta_1_year'
    # sort_asc: bool. True = ascending (smallest first), False = descending (largest first).
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

            # ── Bullish trend states (strongest → weakest) ───────
            'max_bull': {
                'tags': ['bullish', 'trend'],
                'tv_prefilter': {'ema21_above_ema48': True, 'ema48_above_ema200': True, 'close_above_ema21': True},
                'ema8_above_ema13':   True,
                'ema13_above_ema21':  True,
                'ema21_above_ema48':  True,
                'ema48_above_ema200': True,
                'close_above_ema8':   True,
            },
            'strong_bull': {
                'tags': ['bullish', 'trend'],
                'tv_prefilter': {'ema21_above_ema48': True, 'ema48_above_ema200': True, 'close_above_ema21': True},
                'ema8_above_ema21':   True,
                'ema21_above_ema48':  True,
                'ema48_above_ema200': True,
                'close_above_ema21':  True,
            },
            'moderate_bull': {
                'tags': ['bullish', 'trend'],
                'tv_prefilter': {'ema21_above_ema48': True, 'ema48_above_ema200': True, 'close_above_ema21': True},
                'ema21_above_ema48':  True,
                'ema48_above_ema200': True,
                'close_above_ema21':  True,
            },
            'weak_bull': {
                'tags': ['bullish', 'trend'],
                'tv_prefilter': {'ema21_above_ema48': True, 'ema48_above_ema200': True, 'close_above_ema21': True},
                'ema21_above_ema48':   True,
                'ema48_above_ema200':  True,
                'close_above_ema21':   True,
                'ema8_slope_positive': False,
            },
            'bullish_bias': {
                'tags': ['bullish', 'trend'],
                'tv_prefilter': {'close_above_ema21': True},
                'close_above_ema21':  True,
            },

            # ── Bullish pullback entries (strongest → weakest) ───
            'pullback_buy_ema8': {
                'tags': ['bullish', 'entry'],
                'tv_prefilter': {'ema8_above_ema21': True, 'ema21_above_ema48': True, 'close_above_ema21': True, 'low_below_ema8': True},
                'close_above_ema8':   True,
                'low_touched_ema8':   True,
                'ema8_above_ema21':   True,
                'ema21_above_ema48':  True,
            },
            'pullback_buy_ema13': {
                'tags': ['bullish', 'entry'],
                'tv_prefilter': {'ema21_above_ema48': True, 'close_above_ema21': True},
                'close_above_ema13':  True,
                'low_touched_ema13':  True,
                'ema13_above_ema21':  True,
                'ema21_above_ema48':  True,
            },
            'pullback_buy': {
                'tags': ['bullish', 'entry'],
                'tv_prefilter': {'ema21_above_ema48': True, 'close_above_ema21': True, 'low_below_ema21': True},
                'close_above_ema21':  True,
                'low_touched_ema21':  True,
                'ema21_above_ema48':  True,
            },
            'pullback_buy_strong': {
                'tags': ['bullish', 'entry'],
                'tv_prefilter': {'ema21_above_ema48': True, 'ema48_above_ema200': True, 'close_above_ema21': True, 'low_below_ema21': True},
                'close_above_ema21':  True,
                'low_touched_ema21':  True,
                'ema8_above_ema13':   True,
                'ema13_above_ema21':  True,
                'ema21_above_ema48':  True,
                'ema48_above_ema200': True,
            },

            # ── Bearish trend states (strongest → weakest) ───────
            'max_bear': {
                'tags': ['bearish', 'trend'],
                'tv_prefilter': {'close_below_ema21': True},
                'ema8_above_ema13':   False,
                'ema13_above_ema21':  False,
                'ema21_above_ema48':  False,
                'ema48_above_ema200': False,
                'close_above_ema8':   False,
            },
            'strong_bear': {
                'tags': ['bearish', 'trend'],
                'tv_prefilter': {'close_below_ema21': True},
                'ema8_above_ema21':   False,
                'ema21_above_ema48':  False,
                'ema48_above_ema200': False,
                'close_above_ema21':  False,
            },
            'moderate_bear': {
                'tags': ['bearish', 'trend'],
                'tv_prefilter': {'close_below_ema21': True},
                'ema21_above_ema48':  False,
                'ema48_above_ema200': False,
                'close_above_ema21':  False,
            },
            'weak_bear': {
                'tags': ['bearish', 'trend'],
                'tv_prefilter': {'close_below_ema21': True},
                'ema21_above_ema48':   False,
                'ema48_above_ema200':  False,
                'close_above_ema21':   False,
                'ema8_slope_positive': True,
            },
            'bearish_bias': {
                'tags': ['bearish', 'trend'],
                'tv_prefilter': {'close_below_ema21': True},
                'close_above_ema21':  False,
            },

            # ── Bearish pullback entries (strongest → weakest) ───
            'pullback_short_ema8': {
                'tags': ['bearish', 'entry'],
                'tv_prefilter': {'close_below_ema21': True},
                'close_above_ema8':   False,
                'high_touched_ema8':  True,
                'ema8_above_ema21':   False,
                'ema21_above_ema48':  False,
            },
            'pullback_short_ema13': {
                'tags': ['bearish', 'entry'],
                'tv_prefilter': {'close_below_ema21': True},
                'close_above_ema13':  False,
                'high_touched_ema13': True,
                'ema13_above_ema21':  False,
                'ema21_above_ema48':  False,
            },
            'pullback_short': {
                'tags': ['bearish', 'entry'],
                'tv_prefilter': {'close_below_ema21': True, 'high_above_ema21': True},
                'close_above_ema21':  False,
                'high_touched_ema21': True,
                'ema21_above_ema48':  False,
            },

            # ── Reversal signals ─────────────────────────────────
            'vomy_warning': {
                'tags': ['neutral', 'reversal'],
                'tv_prefilter': {'close_above_ema21': True},
                'ema8_above_ema13':          True,
                'ema8_slope_positive':        False,
                'ema8_ema13_gap_pct__lte':   0.5,
            },
            'violent_reversal_down': {
                'tags': ['bearish', 'reversal'],
                'tv_prefilter': {'close_below_ema48': True},
                'prev_close_above_ema48': True,
                'close_above_ema48':      False,
                'ema21_above_ema48':      True,
            },
            'violent_reversal_up': {
                'tags': ['bullish', 'reversal'],
                'tv_prefilter': {'close_above_ema48': True},
                'prev_close_above_ema48': False,
                'close_above_ema48':      True,
                'ema21_above_ema48':      False,
            },
            'golden_cross': {
                'tags': ['bullish', 'reversal'],
                'tv_prefilter': {'ema21_crossed_above_ema200': True},
                'ema21_crossed_above_ema200_recently': True,
            },
            'death_cross': {
                'tags': ['bearish', 'reversal'],
                'tv_prefilter': {'ema21_crossed_below_ema200': True},
                'ema21_crossed_below_ema200_recently': True,
            },

            # ── 200 EMA watch ────────────────────────────────────
            'ema200_watch': {
                'tags': ['neutral', 'trend'],
                'tv_prefilter': {'ema48_above_ema200': True},
                'ema48_above_ema200':         True,
                'ema48_ema200_gap_pct__lte':  2.0,
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
                'tags': ['bullish', 'entry', 'compression'],
                'dot_color':             ['Orange', 'Red'],
                'compression_bars__gte': 5,
                'momentum_above_zero':   True,
                'momentum_rising':       True,
            },
            'anticipatory_bull_orange': {
                'tags': ['bullish', 'entry', 'compression'],
                'dot_color':           ['Orange'],
                'momentum_above_zero': True,
                'momentum_rising':     True,
            },
            'anticipatory_bear': {
                'tags': ['bearish', 'entry', 'compression'],
                'dot_color':             ['Orange', 'Red'],
                'compression_bars__gte': 5,
                'momentum_above_zero':   False,
                'momentum_rising':       False,
            },
            'anticipatory_bear_orange': {
                'tags': ['bearish', 'entry', 'compression'],
                'dot_color':           ['Orange'],
                'momentum_above_zero': False,
                'momentum_rising':     False,
            },
            'confirmed_bull': {
                'tags': ['bullish', 'entry', 'breakout'],
                'first_green_dot':   True,
                'momentum_color':    ['Aqua'],
                'atr_distance__lte': 1.0,
            },
            'confirmed_bear': {
                'tags': ['bearish', 'entry', 'breakout'],
                'first_green_dot':   True,
                'momentum_color':    ['Red'],
                'atr_distance__lte': 1.0,
            },
            'late_bull': {
                'tags': ['bullish', 'breakout'],
                'first_green_dot':  True,
                'momentum_color':   ['Aqua'],
                'atr_distance__gt': 1.0,
            },
            'late_bear': {
                'tags': ['bearish', 'breakout'],
                'first_green_dot':  True,
                'momentum_color':   ['Red'],
                'atr_distance__gt': 1.0,
            },
            'exit_warning_long': {
                'tags': ['neutral', 'exit'],
                'momentum_color':      ['Blue'],
                'prev_momentum_color': ['Aqua'],
            },
            'exit_warning_short': {
                'tags': ['neutral', 'exit'],
                'momentum_color':      ['Yellow'],
                'prev_momentum_color': ['Red'],
            },
            'exit_long': {
                'tags': ['neutral', 'exit'],
                'momentum_color':      ['Blue'],
                'prev_momentum_color': ['Blue'],
            },
            'exit_short': {
                'tags': ['neutral', 'exit'],
                'momentum_color':      ['Yellow'],
                'prev_momentum_color': ['Yellow'],
            },
            'med_bullish': {
                'tags': ['bullish', 'entry', 'compression'],
                'dot_color':             ['Orange', 'Red', 'Black'],
                'compression_bars__gte': 3,
                'momentum_above_zero':   True,
            },
            'high_compression': {
                'tags': ['neutral', 'compression'],
                'dot_color':             ['Orange'],
                'compression_bars__gte': 3,
            },
            'building': {
                'tags': ['neutral', 'compression'],
                'dot_color':             ['Black', 'Red', 'Orange'],
                'compression_bars__gte': 1,
            },
        }
    },

    'macd': {
        'module': 'stage2.macd',
        'params': {
            'fast_period':        12,
            'slow_period':        26,
            'signal_period':      9,
            'divergence_lookback': 14,
        },
        'output_fields': [
            'macd_line', 'signal_line', 'histogram',
            'prev_macd_line', 'prev_signal_line', 'prev_histogram',
            'macd_above_zero', 'macd_below_zero',
            'macd_crossed_above_zero', 'macd_crossed_below_zero',
            'macd_above_signal', 'macd_below_signal',
            'macd_crossed_above_signal', 'macd_crossed_below_signal',
            'histogram_positive', 'histogram_negative',
            'histogram_rising', 'histogram_falling',
            'histogram_above_zero_rising', 'histogram_below_zero_falling',
            'histogram_above_zero_falling', 'histogram_below_zero_rising',
            'bullish_divergence', 'bearish_divergence',
            'macd_signal_gap', 'macd_signal_gap_pct', 'histogram_magnitude',
        ],
        'subconditions': {
            'signal_crossover_bull': {
                'tags': ['bullish', 'entry', 'momentum'],
                'tv_prefilter': {'macd_above_signal': True},
                'macd_crossed_above_signal': True,
            },
            'signal_crossover_bear': {
                'tags': ['bearish', 'entry', 'momentum'],
                'tv_prefilter': {'macd_below_signal': True},
                'macd_crossed_below_signal': True,
            },
            'signal_crossover_bull_above_zero': {
                'tags': ['bullish', 'entry', 'momentum'],
                'tv_prefilter': {'macd_above_signal': True, 'macd_above_zero': True},
                'macd_crossed_above_signal': True,
                'macd_above_zero':           True,
            },
            'signal_crossover_bear_below_zero': {
                'tags': ['bearish', 'entry', 'momentum'],
                'tv_prefilter': {'macd_below_signal': True, 'macd_below_zero': True},
                'macd_crossed_below_signal': True,
                'macd_below_zero':           True,
            },
            'zero_cross_bull': {
                'tags': ['bullish', 'trend', 'momentum'],
                'macd_crossed_above_zero': True,
            },
            'zero_cross_bear': {
                'tags': ['bearish', 'trend', 'momentum'],
                'macd_crossed_below_zero': True,
            },
            'bullish_trend': {
                'tags': ['bullish', 'trend'],
                'tv_prefilter': {'macd_above_signal': True, 'macd_above_zero': True},
                'macd_above_zero':   True,
                'macd_above_signal': True,
            },
            'bearish_trend': {
                'tags': ['bearish', 'trend'],
                'tv_prefilter': {'macd_below_signal': True, 'macd_below_zero': True},
                'macd_below_zero':   True,
                'macd_below_signal': True,
            },
            'bullish_bias': {
                'tags': ['bullish', 'trend'],
                'tv_prefilter': {'macd_above_zero': True},
                'macd_above_zero': True,
            },
            'bearish_bias': {
                'tags': ['bearish', 'trend'],
                'tv_prefilter': {'macd_below_zero': True},
                'macd_below_zero': True,
            },
            'histogram_bull_expanding': {
                'tags': ['bullish', 'momentum'],
                'tv_prefilter': {'macd_above_signal': True, 'macd_above_zero': True},
                'histogram_above_zero_rising': True,
            },
            'histogram_bear_expanding': {
                'tags': ['bearish', 'momentum'],
                'tv_prefilter': {'macd_below_signal': True, 'macd_below_zero': True},
                'histogram_below_zero_falling': True,
            },
            'histogram_bull_fading': {
                'tags': ['neutral', 'exit'],
                'tv_prefilter': {'macd_above_signal': True},
                'histogram_above_zero_falling': True,
            },
            'histogram_bear_fading': {
                'tags': ['neutral', 'exit'],
                'tv_prefilter': {'macd_below_signal': True},
                'histogram_below_zero_rising': True,
            },
            'bullish_divergence': {
                'tags': ['bullish', 'divergence', 'reversal'],
                'bullish_divergence': True,
            },
            'bearish_divergence': {
                'tags': ['bearish', 'divergence', 'reversal'],
                'bearish_divergence': True,
            },
            'bullish_divergence_confirmed': {
                'tags': ['bullish', 'divergence', 'reversal', 'entry'],
                'tv_prefilter': {'macd_above_signal': True},
                'bullish_divergence':        True,
                'macd_crossed_above_signal': True,
            },
            'bearish_divergence_confirmed': {
                'tags': ['bearish', 'divergence', 'reversal', 'entry'],
                'tv_prefilter': {'macd_below_signal': True},
                'bearish_divergence':        True,
                'macd_crossed_below_signal': True,
            },
            'stretched_bull': {
                'tags': ['neutral', 'exit', 'extreme'],
                'tv_prefilter': {'macd_above_signal': True, 'macd_above_zero': True},
                'histogram_positive':       True,
                'macd_signal_gap_pct__gte': 0.5,
            },
            'stretched_bear': {
                'tags': ['neutral', 'exit', 'extreme'],
                'tv_prefilter': {'macd_below_signal': True, 'macd_below_zero': True},
                'histogram_negative':       True,
                'macd_signal_gap_pct__gte': 0.5,
            },
            'strong_bull': {
                'tags': ['bullish', 'trend', 'momentum'],
                'tv_prefilter': {'macd_above_signal': True, 'macd_above_zero': True},
                'macd_above_zero':             True,
                'macd_above_signal':           True,
                'histogram_above_zero_rising': True,
            },
            'strong_bear': {
                'tags': ['bearish', 'trend', 'momentum'],
                'tv_prefilter': {'macd_below_signal': True, 'macd_below_zero': True},
                'macd_below_zero':              True,
                'macd_below_signal':            True,
                'histogram_below_zero_falling': True,
            },
            'pullback_buy_setup': {
                'tags': ['bullish', 'entry'],
                'tv_prefilter': {'macd_above_signal': True, 'macd_above_zero': True},
                'macd_above_zero':              True,
                'histogram_above_zero_falling': True,
            },
            'pullback_short_setup': {
                'tags': ['bearish', 'entry'],
                'tv_prefilter': {'macd_below_signal': True, 'macd_below_zero': True},
                'macd_below_zero':             True,
                'histogram_below_zero_rising': True,
            },
        }
    },

    'bollinger_bands': {
        'module': 'stage2.bollinger_bands',
        'params': {
            'period':             20,
            'std_dev_mult':       2.0,
            'bandwidth_lookback': 125,
        },
        'output_fields': [
            'upper_band', 'middle_band', 'lower_band',
            'prev_upper_band', 'prev_middle_band', 'prev_lower_band',
            'close', 'percent_b', 'prev_percent_b',
            'close_above_middle', 'close_below_middle',
            'close_above_upper', 'close_below_lower',
            'close_near_upper', 'close_near_lower',
            'crossed_above_middle', 'crossed_below_middle',
            'bandwidth', 'prev_bandwidth',
            'bandwidth_expanding', 'bandwidth_contracting',
            'bandwidth_percentile', 'is_squeeze', 'squeeze_just_fired',
            'walking_upper_band', 'walking_lower_band',
            'walk_upper_bar_count', 'walk_lower_bar_count',
            'breakout_upper', 'breakout_lower',
            'prev_breakout_upper', 'prev_breakout_lower',
            'breakout_upper_new', 'breakout_lower_new',
            'returned_inside_from_upper', 'returned_inside_from_lower',
            'upper_band_rejection', 'lower_band_rejection',
            'bullish_trend', 'bearish_trend',
        ],
        'subconditions': {
            'squeeze': {
                'tags': ['neutral', 'compression'],
                'is_squeeze': True,
            },
            'squeeze_fired': {
                'tags': ['neutral', 'breakout'],
                'squeeze_just_fired': True,
            },
            'high_volatility': {
                'tags': ['neutral', 'breakout'],
                'bandwidth_percentile__gte': 75,
                'bandwidth_expanding':       True,
            },
            'volatility_expanding': {
                'tags': ['neutral', 'breakout'],
                'bandwidth_expanding': True,
            },
            'volatility_contracting': {
                'tags': ['neutral', 'compression'],
                'bandwidth_contracting': True,
            },
            'bullish_trend': {
                'tags': ['bullish', 'trend'],
                'close_above_middle': True,
            },
            'bearish_trend': {
                'tags': ['bearish', 'trend'],
                'close_below_middle': True,
            },
            'bullish_trend_strong': {
                'tags': ['bullish', 'trend'],
                'close_above_middle':  True,
                'bandwidth_expanding': True,
            },
            'bearish_trend_strong': {
                'tags': ['bearish', 'trend'],
                'close_below_middle':  True,
                'bandwidth_expanding': True,
            },
            'middle_band_cross_bull': {
                'tags': ['bullish', 'entry', 'momentum'],
                'crossed_above_middle': True,
            },
            'middle_band_cross_bear': {
                'tags': ['bearish', 'entry', 'momentum'],
                'crossed_below_middle': True,
            },
            'near_upper_band': {
                'tags': ['bearish', 'extreme'],
                'close_near_upper': True,
            },
            'near_lower_band': {
                'tags': ['bullish', 'extreme'],
                'close_near_lower': True,
            },
            'outside_upper_band': {
                'tags': ['neutral', 'extreme', 'breakout'],
                'breakout_upper': True,
            },
            'outside_lower_band': {
                'tags': ['neutral', 'extreme', 'breakout'],
                'breakout_lower': True,
            },
            'breakout_bull': {
                'tags': ['bullish', 'breakout', 'entry'],
                'breakout_upper_new': True,
            },
            'breakout_bear': {
                'tags': ['bearish', 'breakout', 'entry'],
                'breakout_lower_new': True,
            },
            'breakout_bull_squeeze': {
                'tags': ['bullish', 'breakout', 'entry', 'compression'],
                'breakout_upper_new': True,
                'squeeze_just_fired': True,
            },
            'breakout_bear_squeeze': {
                'tags': ['bearish', 'breakout', 'entry', 'compression'],
                'breakout_lower_new': True,
                'squeeze_just_fired': True,
            },
            'walking_upper': {
                'tags': ['bullish', 'trend', 'continuation'],
                'walking_upper_band': True,
            },
            'walking_lower': {
                'tags': ['bearish', 'trend', 'continuation'],
                'walking_lower_band': True,
            },
            'upper_band_rejection': {
                'tags': ['bearish', 'reversal'],
                'upper_band_rejection': True,
            },
            'lower_band_rejection': {
                'tags': ['bullish', 'reversal'],
                'lower_band_rejection': True,
            },
            'lower_band_rejection_bullish_trend': {
                'tags': ['bullish', 'reversal', 'entry'],
                'lower_band_rejection': True,
                'close_above_middle':   True,
            },
            'upper_band_rejection_bearish_trend': {
                'tags': ['bearish', 'reversal', 'entry'],
                'upper_band_rejection': True,
                'close_below_middle':   True,
            },
            'squeeze_bull_setup': {
                'tags': ['bullish', 'compression', 'entry'],
                'is_squeeze':         True,
                'close_above_middle': True,
            },
            'squeeze_bear_setup': {
                'tags': ['bearish', 'compression', 'entry'],
                'is_squeeze':         True,
                'close_below_middle': True,
            },
            'oversold_reversal': {
                'tags': ['bullish', 'reversal', 'extreme'],
                'close_near_lower':      True,
                'bandwidth_contracting': True,
            },
            'overbought_reversal': {
                'tags': ['bearish', 'reversal', 'extreme'],
                'close_near_upper':      True,
                'bandwidth_contracting': True,
            },
        }
    },

    'saty_phase_oscillator': {
        'module': 'stage2.saty_phase_oscillator',
        'params': {
            'ema_period':           21,
            'atr_period':           14,
            'smooth_period':        3,
            'monster_eye_lookback': 20,
            'div_pivot_left':       3,    # bars to the left of pivot to confirm
            'div_pivot_right':      1,    # bars to the right of pivot to confirm
            'div_range_lower':      5,    # min bars between two pivots
            'div_range_upper':      60,   # max bars between two pivots
        },
        'output_fields': [
            'oscillator', 'prev_oscillator', 'raw_signal', 'pivot', 'atr',
            'zone', 'prev_zone',
            'in_extreme_up', 'in_distribution', 'in_neutral_up', 'in_zero_band',
            'in_neutral_down', 'in_accumulation', 'in_extreme_down',
            'above_zero', 'below_zero',
            'leaving_distribution', 'leaving_extreme_up',
            'leaving_accumulation', 'leaving_extreme_down',
            'crossed_above_zero', 'crossed_below_zero',
            'crossed_above_neutral_up', 'crossed_below_neutral_down',
            'reversion_dot_bull', 'reversion_dot_bear',
            'prev_reversion_dot_bull', 'prev_reversion_dot_bear',
            'monster_eye_bull', 'monster_eye_bear',
            'oscillator_rising', 'oscillator_falling',
            'in_compression', 'compression_just_ended',
            'bullish_divergence', 'hidden_bullish_divergence',
            'bearish_divergence', 'hidden_bearish_divergence',
        ],
        'subconditions': {
            'in_accumulation': {
                'tags': ['bullish', 'extreme'],
                'in_accumulation': True,
            },
            'in_extreme_down': {
                'tags': ['bullish', 'extreme'],
                'in_extreme_down': True,
            },
            'in_distribution': {
                'tags': ['bearish', 'extreme'],
                'in_distribution': True,
            },
            'in_extreme_up': {
                'tags': ['bearish', 'extreme'],
                'in_extreme_up': True,
            },
            'bullish_momentum': {
                'tags': ['bullish', 'momentum'],
                'in_neutral_up':     True,
                'oscillator_rising': True,
            },
            'above_zero': {
                'tags': ['bullish', 'trend'],
                'above_zero': True,
            },
            'below_zero': {
                'tags': ['bearish', 'trend'],
                'below_zero': True,
            },
            'leaving_accumulation': {
                'tags': ['bullish', 'reversal', 'entry'],
                'leaving_accumulation': True,
            },
            'leaving_extreme_down': {
                'tags': ['bullish', 'reversal', 'entry'],
                'leaving_extreme_down': True,
            },
            'leaving_distribution': {
                'tags': ['bearish', 'reversal', 'entry'],
                'leaving_distribution': True,
            },
            'leaving_extreme_up': {
                'tags': ['bearish', 'reversal', 'entry'],
                'leaving_extreme_up': True,
            },
            'zero_cross_bull': {
                'tags': ['bullish', 'momentum', 'entry'],
                'crossed_above_zero': True,
            },
            'zero_cross_bear': {
                'tags': ['bearish', 'momentum', 'entry'],
                'crossed_below_zero': True,
            },
            'entering_bull_zone': {
                'tags': ['bullish', 'momentum', 'trend'],
                'crossed_above_neutral_up': True,
            },
            'entering_bear_zone': {
                'tags': ['bearish', 'momentum', 'trend'],
                'crossed_below_neutral_down': True,
            },
            'reversion_dot_bull': {
                'tags': ['bullish', 'reversal'],
                'reversion_dot_bull': True,
            },
            'reversion_dot_bear': {
                'tags': ['bearish', 'reversal'],
                'reversion_dot_bear': True,
            },
            'monster_eye_bull': {
                'tags': ['bullish', 'reversal'],
                'monster_eye_bull': True,
            },
            'monster_eye_bear': {
                'tags': ['bearish', 'reversal'],
                'monster_eye_bear': True,
            },
            'monster_eye_bull_divergence': {
                'tags': ['bullish', 'reversal', 'divergence'],
                'monster_eye_bull':    True,
                'bullish_divergence':  True,
            },
            'monster_eye_bear_divergence': {
                'tags': ['bearish', 'reversal', 'divergence'],
                'monster_eye_bear':    True,
                'bearish_divergence':  True,
            },
            'compression': {
                'tags': ['neutral', 'compression'],
                'in_compression': True,
            },
            'compression_fired': {
                'tags': ['neutral', 'breakout'],
                'compression_just_ended': True,
            },
            'compression_bull_setup': {
                'tags': ['bullish', 'compression'],
                'in_compression': True,
                'above_zero':     True,
            },
            'compression_bear_setup': {
                'tags': ['bearish', 'compression'],
                'in_compression': True,
                'below_zero':     True,
            },
            'pullback_buy_accumulation': {
                'tags': ['bullish', 'entry', 'extreme'],
                'in_accumulation':   True,
                'oscillator_rising': True,
            },
            'pullback_buy_zero_cross': {
                'tags': ['bullish', 'entry', 'momentum'],
                'crossed_above_zero': True,
            },
            'pullback_short_distribution': {
                'tags': ['bearish', 'entry', 'extreme'],
                'in_distribution':    True,
                'oscillator_falling': True,
            },
            'pullback_short_zero_cross': {
                'tags': ['bearish', 'entry', 'momentum'],
                'crossed_below_zero': True,
            },
            'bullish_divergence': {
                'tags': ['bullish', 'divergence', 'reversal'],
                'bullish_divergence': True,
            },
            'bullish_divergence_confirmed': {
                'tags': ['bullish', 'divergence', 'reversal', 'entry'],
                'bullish_divergence':    True,
                'leaving_accumulation': True,
            },
            'bullish_divergence_extreme_confirmed': {
                'tags': ['bullish', 'divergence', 'reversal', 'entry'],
                'bullish_divergence':    True,
                'leaving_extreme_down': True,
            },
            'hidden_bull_continuation': {
                'tags': ['bullish', 'divergence', 'continuation'],
                'hidden_bullish_divergence': True,
                'above_zero':                True,
            },
            'bearish_divergence': {
                'tags': ['bearish', 'divergence', 'reversal'],
                'bearish_divergence': True,
            },
            'bearish_divergence_confirmed': {
                'tags': ['bearish', 'divergence', 'reversal', 'entry'],
                'bearish_divergence':    True,
                'leaving_distribution': True,
            },
            'hidden_bear_continuation': {
                'tags': ['bearish', 'divergence', 'continuation'],
                'hidden_bearish_divergence': True,
                'below_zero':                True,
            },
            'strong_bull': {
                'tags': ['bullish', 'trend', 'momentum'],
                'in_neutral_up':     True,
                'oscillator_rising': True,
                'above_zero':        True,
            },
            'strong_bear': {
                'tags': ['bearish', 'trend', 'momentum'],
                'in_neutral_down':    True,
                'oscillator_falling': True,
                'below_zero':         True,
            },
            'mean_reversion_bull': {
                'tags': ['bullish', 'reversal', 'extreme'],
                'in_accumulation':   True,
                'oscillator_rising': True,
            },
            'mean_reversion_bear': {
                'tags': ['bearish', 'reversal', 'extreme'],
                'in_distribution':    True,
                'oscillator_falling': True,
            },
        }
    },

}


# ─────────────────────────────────────────────────────────────────────────────
# WEEKLY TIMEFRAME INDICATORS (optional)
#
# To add weekly versions of any indicator:
#   1. Uncomment the entry below and add it inside the INDICATORS dict above.
#   2. Set 'interval': '1wk' — the fetcher will pull weekly bars automatically.
#   3. Set 'history_weeks' to the number of weekly bars you want (100 ≈ 2 years).
#   4. Define subconditions just like daily ones — the same module handles both.
#   5. Reference in presets as e.g. 'saty_ribbon_weekly.strong_bull'.
#
# The indicator module code does not change at all — it receives a weekly
# DataFrame instead of a daily one and returns the same output fields.
# ─────────────────────────────────────────────────────────────────────────────

# WEEKLY EXAMPLES — paste these entries into INDICATORS above to activate:
#
#   'saty_ribbon_weekly': {
#       'module':         'stage2.saty_ribbon',
#       'interval':       '1wk',     # tells the fetcher to use weekly bars
#       'history_weeks':  100,        # ~2 years of weekly data
#       'params': {
#           'fast_ema':      8,
#           'secondary_ema': 13,
#           'pivot_ema':     21,
#           'slow_ema':      48,
#           'longterm_ema':  200,
#       },
#       'output_fields': [           # same fields as saty_ribbon — weekly values
#           'ema8', 'ema13', 'ema21', 'ema48', 'ema200',
#           'close', 'high', 'low', 'open',
#           'close_above_ema8',   'close_above_ema13',
#           'close_above_ema21',  'close_above_ema48',
#           'close_above_ema200',
#           'low_touched_ema8',   'low_touched_ema13',
#           'low_touched_ema21',
#           'high_touched_ema8',  'high_touched_ema13',
#           'high_touched_ema21',
#           'ema8_above_ema13',   'ema13_above_ema21',
#           'ema21_above_ema48',  'ema48_above_ema200',
#           'ema8_above_ema21',   'ema8_above_ema48',
#           'ema21_above_ema200',
#           'ema8_slope',         'ema13_slope',
#           'ema21_slope',        'ema48_slope',        'ema200_slope',
#           'ema8_slope_positive', 'ema21_slope_positive', 'ema48_slope_positive',
#           'ema8_ema13_gap_pct', 'ema21_ema48_gap_pct', 'ema48_ema200_gap_pct',
#           'ema21_crossed_above_ema48_recently',
#           'ema21_crossed_below_ema48_recently',
#           'ema21_crossed_above_ema200_recently',
#           'ema21_crossed_below_ema200_recently',
#           'prev_close_above_ema21', 'prev_close_above_ema48',
#       ],
#       'subconditions': {
#           'weekly_strong_bull': {
#               'ema8_above_ema21':   True,
#               'ema21_above_ema48':  True,
#               'ema48_above_ema200': True,
#               'close_above_ema21':  True,
#           },
#           'weekly_pullback_buy': {
#               'close_above_ema21': True,
#               'low_touched_ema21': True,
#               'ema21_above_ema48': True,
#           },
#           'weekly_bullish_bias': {
#               'close_above_ema21': True,
#           },
#           'weekly_bearish_bias': {
#               'close_above_ema21': False,
#           },
#       }
#   },
#
#   'ttm_squeeze_weekly': {
#       'module':         'stage2.ttm_squeeze',
#       'interval':       '1wk',
#       'history_weeks':  100,
#       'params': {
#           'length':       20,
#           'bb_mult':      2.0,
#           'kc_mult_high': 1.0,
#           'kc_mult_mid':  1.5,
#           'kc_mult_low':  2.0,
#       },
#       'output_fields': [           # same fields as ttm_squeeze — weekly values
#           'dot_color', 'prev_dot_color', 'compression_bars',
#           'momentum_value', 'prev_momentum_value',
#           'momentum_above_zero', 'momentum_rising',
#           'momentum_color', 'prev_momentum_color',
#           'squeeze_start_price', 'atr', 'atr_distance', 'first_green_dot',
#           'bb_upper', 'bb_lower',
#           'kc_upper_low', 'kc_lower_low',
#           'kc_upper_mid', 'kc_lower_mid',
#           'kc_upper_high', 'kc_lower_high',
#       ],
#       'subconditions': {
#           'weekly_anticipatory_bull': {
#               'dot_color':             ['Orange', 'Red'],
#               'compression_bars__gte': 3,
#               'momentum_above_zero':   True,
#               'momentum_rising':       True,
#           },
#           'weekly_high_compression': {
#               'dot_color':             ['Orange'],
#               'compression_bars__gte': 2,
#           },
#           'weekly_confirmed_bull': {
#               'first_green_dot':       True,
#               'momentum_above_zero':   True,
#               'atr_distance__lte':     1.0,
#           },
#       }
#   },
