PRESETS = {

    # ── Bullish setups ──────────────────────────────────────────────────
    'bullish_pullback': (
        'saty_ribbon.pullback_buy'
        '+'
        '(ttm_squeeze.anticipatory_bull|ttm_squeeze.anticipatory_bull_orange)'
    ),
    'bullish_pullback_strong': (
        'saty_ribbon.pullback_buy_strong'
        '+'
        '(ttm_squeeze.anticipatory_bull|ttm_squeeze.confirmed_bull)'
    ),
    'max_bull_squeeze': (
        'saty_ribbon.max_bull'
        '+'
        '(ttm_squeeze.anticipatory_bull|ttm_squeeze.anticipatory_bull_orange|ttm_squeeze.confirmed_bull)'
    ),
    'squeeze_bull_any': (
        'ttm_squeeze.anticipatory_bull'
        '|ttm_squeeze.anticipatory_bull_orange'
        '|ttm_squeeze.confirmed_bull'
    ),

    # ── Bearish setups ──────────────────────────────────────────────────
    'bearish_pullback': (
        'saty_ribbon.pullback_short'
        '+'
        '(ttm_squeeze.anticipatory_bear|ttm_squeeze.anticipatory_bear_orange)'
    ),
    'squeeze_bear_any': (
        'ttm_squeeze.anticipatory_bear'
        '|ttm_squeeze.anticipatory_bear_orange'
        '|ttm_squeeze.confirmed_bear'
    ),

    # ── Reversal setups ─────────────────────────────────────────────────
    'bull_reversal_watch': (
        'saty_ribbon.bearish_bias'
        '+'
        'ttm_squeeze.high_compression'
    ),
    'golden_cross': (
        'saty_ribbon.golden_cross'
    ),
    'death_cross': (
        'saty_ribbon.death_cross'
    ),

    # ── Exit signals ────────────────────────────────────────────────────
    'exit_longs': (
        'ttm_squeeze.exit_long'
        '+'
        'saty_ribbon.bullish_bias'
    ),

}


# ─────────────────────────────────────────────────────────────────────────────
# WEEKLY PRESET EXAMPLES
#
# These require the weekly indicator entries to be uncommented in config.py
# first (see the weekly section at the bottom of config.example.py).
# Once active, weekly and daily subconditions can be freely mixed with +/|.
# ─────────────────────────────────────────────────────────────────────────────

# Paste these into PRESETS above to activate:
#
#   # Daily pullback with weekly trend confirmation
#   'bullish_pullback_weekly_confirmed': (
#       'saty_ribbon.pullback_buy'
#       '+'
#       '(ttm_squeeze.anticipatory_bull|ttm_squeeze.anticipatory_bull_orange)'
#       '+'
#       'saty_ribbon_weekly.weekly_bullish_bias'
#   ),
#
#   # Weekly squeeze firing with daily ribbon aligned
#   'weekly_squeeze_bull': (
#       'ttm_squeeze_weekly.weekly_anticipatory_bull'
#       '+'
#       'saty_ribbon.bullish_bias'
#   ),
#
#   # High-conviction: weekly squeeze + daily pullback entry
#   'weekly_squeeze_daily_entry': (
#       'ttm_squeeze_weekly.weekly_anticipatory_bull'
#       '+'
#       'saty_ribbon.pullback_buy'
#       '+'
#       '(ttm_squeeze.anticipatory_bull|ttm_squeeze.building)'
#   ),
#
#   # Weekly trend intact, weekly squeeze compressing
#   'weekly_compression_watch': (
#       'saty_ribbon_weekly.weekly_strong_bull'
#       '+'
#       'ttm_squeeze_weekly.weekly_high_compression'
#   ),
