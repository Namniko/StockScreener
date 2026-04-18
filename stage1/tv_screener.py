import pandas as pd
from tradingview_screener import Query, And, col

STAGE1_SELECT_ALWAYS = [
    'name', 'close', 'open', 'high', 'low', 'volume',
    'EMA20', 'EMA50', 'EMA200',   # TV only supports standard periods; Stage 2 computes exact EMAs
    'RSI', 'MACD.macd', 'MACD.signal',
    'market_cap_basic', 'sector', 'average_volume_10d_calc',
    'relative_volume_10d_calc', 'type', 'typespecs',
    'exchange', 'currency',
]


def build_stage1_query(cfg: dict) -> Query:
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

    # TV field mapping: our logical EMAs → nearest TV-supported period
    # EMA8→EMA10, EMA21→EMA20, EMA48→EMA50 (Stage 2 uses exact yfinance-computed values)
    nf = cfg.get('native_filters', {})
    if nf.get('ema21_above_ema48'):
        expressions.append(col('EMA20') >= col('EMA50'))
    if nf.get('ema48_above_ema200'):
        expressions.append(col('EMA50') >= col('EMA200'))
    if nf.get('ema8_above_ema21'):
        expressions.append(col('EMA10') >= col('EMA20'))
    if nf.get('close_above_ema21'):
        expressions.append(col('close') >= col('EMA20'))
    if nf.get('close_below_ema21'):
        expressions.append(col('close') < col('EMA20'))
    if nf.get('close_above_ema48'):
        expressions.append(col('close') >= col('EMA50'))
    if nf.get('close_below_ema48'):
        expressions.append(col('close') < col('EMA50'))
    if nf.get('low_below_ema21'):
        expressions.append(col('low') <= col('EMA20'))
    if nf.get('low_below_ema8'):
        expressions.append(col('low') <= col('EMA10'))
    if nf.get('high_above_ema21'):
        expressions.append(col('high') >= col('EMA20'))
    if nf.get('ema8_crossed_above_ema21'):
        expressions.append(col('EMA10').crosses_above('EMA20'))
    if nf.get('ema21_crossed_above_ema48'):
        expressions.append(col('EMA20').crosses_above('EMA50'))
    if nf.get('ema21_crossed_above_ema200'):
        expressions.append(col('EMA20').crosses_above('EMA200'))
    if nf.get('ema21_crossed_below_ema200'):
        expressions.append(col('EMA20').crosses_below('EMA200'))
    if nf.get('macd_above_signal'):
        expressions.append(col('MACD.macd') >= col('MACD.signal'))
    if nf.get('macd_below_signal'):
        expressions.append(col('MACD.macd') < col('MACD.signal'))
    if nf.get('rsi_min') is not None:
        expressions.append(col('RSI') >= nf['rsi_min'])
    if nf.get('rsi_max') is not None:
        expressions.append(col('RSI') <= nf['rsi_max'])
    if nf.get('min_rel_volume') is not None:
        expressions.append(col('relative_volume_10d_calc') >= nf['min_rel_volume'])

    q = (Query()
         .select(*STAGE1_SELECT_ALWAYS)
         .order_by(cfg.get('sort_by', 'market_cap_basic'),
                   ascending=cfg.get('sort_asc', False))
         .limit(cfg.get('max_results', 200)))

    if cfg.get('index'):
        indexes = cfg['index'] if isinstance(cfg['index'], list) else [cfg['index']]
        q = q.set_index(*indexes)
    else:
        q = q.set_markets(cfg.get('market', 'america'))

    if expressions:
        q = q.where2(And(*expressions))

    return q


def run_tv_screener(cfg: dict, cookies: dict | None = None) -> tuple[list[str], pd.DataFrame]:
    q = build_stage1_query(cfg)
    kwargs = {'cookies': cookies} if cookies else {}
    total, df = q.get_scanner_data(**kwargs)
    print(f'  Stage 1: {total} total matches, returning top {len(df)}')
    tickers = df['ticker'].tolist()
    return tickers, df
