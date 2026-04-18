# Stock Screener

A two-stage US stock screener that combines TradingView's server-side scan API with locally-computed custom indicators to identify stocks meeting specific technical criteria.

## How It Works

### Stage 1 — TradingView Broad Filter
Uses the [TradingView Screener](https://github.com/shner-elmo/TradingView-Screener) Python package to query TradingView's scan API. Applies fundamental and native indicator filters server-side to narrow ~8,000 US equities down to a short list of candidates. All filter parameters are defined in `config.py`.

### Stage 2 — Local Indicator Computation
Fetches daily OHLC history for each candidate via `yfinance`, then computes custom indicators locally. Raw indicator values are evaluated against named subconditions defined in `config.py`. Subconditions are composed into scan expressions using `+` (AND) and `|` (OR) logic.

### Output
Results are ranked and printed to the console. Optionally saved to `.xlsx`.

---

## Architecture

```
main.py                      # Entry point — orchestrates Stage 1 → Stage 2 → output
config.py                    # Your personal indicator params, subconditions, Stage 1 filters
presets.py                   # Your personal named scan compositions
config.example.py            # Committed example — copy to config.py to get started
presets.example.py           # Committed example — copy to presets.py to get started

stage1/
  tv_screener.py             # Builds and executes TradingView screener query

stage2/
  data_fetcher.py            # yfinance batch OHLC download
  saty_ribbon.py             # Saty Pivot Ribbon indicator (pure calculation)
  ttm_squeeze.py             # TTM Squeeze Pro indicator (pure calculation)

scanner/
  evaluator.py               # Evaluates raw indicator output against config subconditions
  expression_parser.py       # Parses +, |, () scan expressions into an AST
  ranker.py                  # Scores and sorts results

models/
  results.py                 # Dataclasses for raw output and screener results

output/
  formatter.py               # Console printing and XLSX export
```

### Design Principles

- **Indicator modules are pure math** — they compute and return raw values only, no labels or opinions.
- **`config.py` owns all interpretation** — raw values are mapped to named subconditions with thresholds.
- **`presets.py` owns all scan compositions** — named scans combine subconditions with AND/OR logic.
- **Adding a new condition never requires touching indicator code** — only `config.py` and `presets.py`.

---

## Indicators

Two indicators are pre-loaded:

**Saty Pivot Ribbon** — an EMA ribbon system for trend direction and pullback detection.  
Credit: [Saty Mahajan (@satymahajan)](https://www.tradingview.com/u/satymahajan/) on TradingView.

**TTM Squeeze Pro** — a volatility compression and momentum indicator based on Bollinger Bands and Keltner Channels.  
Credit: [Beardy_Fred (@Beardy_Fred)](https://www.tradingview.com/u/Beardy_Fred/) on TradingView.

---

## Setup

```bash
# Create and activate conda environment
conda create -n stockscreener python=3.13 -y
conda activate stockscreener

# Install dependencies
pip install tradingview-screener yfinance pandas numpy openpyxl python-dotenv

# Copy example configs to personal versions (gitignored)
cp config.example.py config.py
cp presets.example.py presets.py
```

### Optional: Real-Time TradingView Data

By default the TradingView API returns data with a 15-minute delay. To use real-time data, add your TradingView session cookie to a `.env` file in the project root:

```
TV_SESSION_ID=your_session_id_here
```

Your session ID can be found in your browser's cookies after logging into TradingView (`sessionid` cookie on `tradingview.com`).

---

## Usage

```bash
# Run a named preset
python main.py --scan bullish_pullback
python main.py --scan bearish_pullback

# Run an ad-hoc subcondition
python main.py --scan "ttm_squeeze.anticipatory_bull"
python main.py --scan "saty_ribbon.pullback_buy"

# AND: both must fire
python main.py --scan "ttm_squeeze.anticipatory_bull+saty_ribbon.pullback_buy"

# OR: either fires
python main.py --scan "ttm_squeeze.anticipatory_bull|ttm_squeeze.confirmed_bull"

# Mixed with parentheses
python main.py --scan "saty_ribbon.pullback_buy+(ttm_squeeze.anticipatory_bull|ttm_squeeze.confirmed_bull)"

# Additional flags
python main.py --scan bullish_pullback --limit 20
python main.py --scan bullish_pullback --output output/results.xlsx
python main.py --scan bullish_pullback --min-cap 1000000000
python main.py --scan bullish_pullback --sectors Technology Healthcare
```

### Expression Syntax

| Operator | Meaning |
|---|---|
| `+` | AND — both sides must match |
| `\|` | OR — either side matches |
| `()` | Grouping — standard precedence, `+` binds tighter than `\|` |
| `indicator.subcondition` | A named subcondition from `config.py` |
| `preset_name` | A named preset from `presets.py` |

Presets and subconditions can be freely mixed in the same expression.

---

## Configuration

### `config.py` — Stage 1 Filters

Controls the TradingView broad filter: market universe, instrument type, fundamental minimums, and native indicator filters applied server-side before Stage 2.

Key settings:

```python
STAGE1 = {
    'min_market_cap':  1_000_000_000,  # $1B minimum
    'min_price':       5.0,
    'min_avg_volume':  500_000,        # 10-day average volume
    'max_results':     200,            # candidates passed to Stage 2
    'history_days':    300,            # OHLC bars fetched (300+ needed for EMA200)
    'native_filters': {
        'ema21_above_ema48':  True,    # maps to EMA20 >= EMA50 in TV API
        'close_above_ema21':  True,
        'low_below_ema21':    True,
        # ... etc
    }
}
```

### `config.py` — Subconditions

Each indicator entry defines named subconditions as dicts of `field: threshold` pairs. Threshold suffixes control the comparison operator:

| Suffix | Operator | Example |
|---|---|---|
| *(none, bool)* | exact match | `'momentum_above_zero': True` |
| *(none, list)* | value in list | `'dot_color': ['Orange', 'Red']` |
| `__gte` | >= | `'compression_bars__gte': 5` |
| `__lte` | <= | `'atr_distance__lte': 1.0` |
| `__gt` | > | `'atr_distance__gt': 1.0` |
| `__lt` | < | `'ema8_ema13_gap_pct__lt': 0.5` |

### `presets.py` — Named Scans

```python
PRESETS = {
    'bullish_pullback': (
        'saty_ribbon.pullback_buy'
        '+'
        '(ttm_squeeze.anticipatory_bull|ttm_squeeze.anticipatory_bull_orange)'
    ),
    # ...
}
```

---

## Adding a New Indicator

1. Create `stage2/new_indicator.py` — implement `compute(df, params) -> dict`, return raw values only.
2. Add an entry to `INDICATORS` in `config.py` with `module`, `params`, `output_fields`, and `subconditions`.
3. Register it in `stage2/__init__.py` under `INDICATOR_MODULES`.
4. Optionally reference it in `presets.py`.

No changes needed to `evaluator.py`, `expression_parser.py`, `main.py`, or `formatter.py`.

---

## Attribution

- **TradingView Screener API** — market data and server-side scanning provided by [TradingView](https://www.tradingview.com/). Python client by [shner-elmo](https://github.com/shner-elmo/TradingView-Screener).
- **Saty Pivot Ribbon** — indicator concept by [Saty Mahajan (@satymahajan)](https://www.tradingview.com/u/satymahajan/) on TradingView.
- **TTM Squeeze Pro** — indicator concept by [Beardy_Fred (@Beardy_Fred)](https://www.tradingview.com/u/Beardy_Fred/) on TradingView.
