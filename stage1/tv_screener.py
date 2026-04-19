import pandas as pd
from tradingview_screener import Query, And, col

STAGE1_SELECT_ALWAYS = [
    'name', 'close', 'open', 'high', 'low', 'volume',
    'EMA8', 'EMA13', 'EMA21', 'EMA50', 'EMA200',  # EMA48 not supported by TV API → proxied to EMA50
    'RSI', 'MACD.macd', 'MACD.signal',
    'market_cap_basic', 'sector', 'average_volume_10d_calc',
    'relative_volume_10d_calc', 'type', 'typespecs',
    'exchange', 'currency',
]


def _apply_prefilter(expressions: list, pf: dict) -> None:
    """Translate a tv_prefilter dict into tradingview_screener col() expressions."""
    # EMA48 is not supported by the TV API — proxied to EMA50 (Stage 2 uses exact values)
    if pf.get('ema21_above_ema48'):
        expressions.append(col('EMA21') >= col('EMA50'))
    if pf.get('ema48_above_ema200'):
        expressions.append(col('EMA50') >= col('EMA200'))
    if pf.get('ema8_above_ema21'):
        expressions.append(col('EMA8') >= col('EMA21'))
    if pf.get('close_above_ema8'):
        expressions.append(col('close') >= col('EMA8'))
    if pf.get('close_below_ema8'):
        expressions.append(col('close') < col('EMA8'))
    if pf.get('close_above_ema21'):
        expressions.append(col('close') >= col('EMA21'))
    if pf.get('close_below_ema21'):
        expressions.append(col('close') < col('EMA21'))
    if pf.get('close_above_ema48'):
        expressions.append(col('close') >= col('EMA50'))
    if pf.get('close_below_ema48'):
        expressions.append(col('close') < col('EMA50'))
    if pf.get('low_below_ema21'):
        expressions.append(col('low') <= col('EMA21'))
    if pf.get('low_below_ema8'):
        expressions.append(col('low') <= col('EMA8'))
    if pf.get('high_above_ema21'):
        expressions.append(col('high') >= col('EMA21'))
    if pf.get('ema8_crossed_above_ema21'):
        expressions.append(col('EMA8').crosses_above('EMA21'))
    if pf.get('ema21_crossed_above_ema48'):
        expressions.append(col('EMA21').crosses_above('EMA50'))
    if pf.get('ema21_crossed_above_ema200'):
        expressions.append(col('EMA21').crosses_above('EMA200'))
    if pf.get('ema21_crossed_below_ema200'):
        expressions.append(col('EMA21').crosses_below('EMA200'))
    if pf.get('macd_above_signal'):
        expressions.append(col('MACD.macd') >= col('MACD.signal'))
    if pf.get('macd_below_signal'):
        expressions.append(col('MACD.macd') < col('MACD.signal'))
    if pf.get('macd_above_zero'):
        expressions.append(col('MACD.macd') >= 0)
    if pf.get('macd_below_zero'):
        expressions.append(col('MACD.macd') < 0)
    if pf.get('rsi_min') is not None:
        expressions.append(col('RSI') >= pf['rsi_min'])
    if pf.get('rsi_max') is not None:
        expressions.append(col('RSI') <= pf['rsi_max'])
    if pf.get('min_rel_volume') is not None:
        expressions.append(col('relative_volume_10d_calc') >= pf['min_rel_volume'])


def build_stage1_query(cfg: dict, prefilter: dict | None = None) -> Query:
    expressions = []

    if cfg.get('type'):
        expressions.append(col('type') == cfg['type'])
    if cfg.get('typespecs'):
        expressions.append(col('typespecs').has(cfg['typespecs']))

    if cfg.get('min_market_cap'):
        expressions.append(col('market_cap_basic') >= cfg['min_market_cap'])
    if cfg.get('max_market_cap'):
        expressions.append(col('market_cap_basic') <= cfg['max_market_cap'])
    if cfg.get('min_price'):
        expressions.append(col('close') >= cfg['min_price'])
    if cfg.get('max_price'):
        expressions.append(col('close') <= cfg['max_price'])
    if cfg.get('min_avg_volume'):
        expressions.append(col('average_volume_10d_calc') >= cfg['min_avg_volume'])
    if cfg.get('sectors'):
        expressions.append(col('sector').isin(cfg['sectors']))
    if cfg.get('exchanges'):
        expressions.append(col('exchange').isin(cfg['exchanges']))

    if prefilter:
        _apply_prefilter(expressions, prefilter)

    q = (Query()
         .select(*STAGE1_SELECT_ALWAYS)
         .order_by(cfg.get('sort_by', 'market_cap_basic'),
                   ascending=cfg.get('sort_asc', False))
         .limit(cfg.get('max_results', 200)))

    if cfg.get('index'):
        indexes = cfg['index'] if isinstance(cfg['index'], list) else [cfg['index']]
        q = q.set_index(*indexes)
    else:
        market = cfg.get('market', 'america')
        if isinstance(market, list):
            q = q.set_markets(*market)
        else:
            q = q.set_markets(market)

    if expressions:
        q = q.where2(And(*expressions))

    return q


def run_tv_screener(cfg: dict, prefilter: dict | None = None, cookies: dict | None = None) -> tuple[list[str], pd.DataFrame]:
    q = build_stage1_query(cfg, prefilter=prefilter)
    kwargs = {'cookies': cookies} if cookies else {}
    total, df = q.get_scanner_data(**kwargs)
    print(f'  Stage 1: {total} total matches, returning top {len(df)}')
    tickers = df['ticker'].tolist()
    return tickers, df
