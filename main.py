import argparse
import os
import sys

from dotenv import load_dotenv  # pip install python-dotenv (optional)


def _load_optional_dotenv():
    try:
        load_dotenv()
    except ImportError:
        pass


def parse_args():
    p = argparse.ArgumentParser(description='Stock Screener')
    p.add_argument('--scan',       default=None, help='Scan expression or preset name')
    p.add_argument('--list',       nargs='?',    const='', metavar='QUERY',
                   help='List subconditions. Optional query: "bullish", "bullish.entry", "entry"')
    p.add_argument('--tree',       action='store_true',
                   help='Print full subcondition tag tree')
    p.add_argument('--limit',      type=int,   default=None, help='Max results to display')
    p.add_argument('--output',     default=None, help='Override output .xlsx path (default: output/stockscreener_result_YYYYMMDD_HHMM.xlsx)')
    p.add_argument('--min-cap',    type=float, default=None, dest='min_cap',
                   help='Override min market cap (Stage 1)')
    p.add_argument('--sectors',    nargs='+',  default=None, help='Filter by sector(s)')
    return p.parse_args()


def main():
    _load_optional_dotenv()
    args = parse_args()

    # ── Load user config and presets ────────────────────────────────────
    try:
        import config as cfg_module
    except ImportError:
        print('Error: config.py not found. Copy config.example.py → config.py and edit it.')
        sys.exit(1)

    try:
        import presets as presets_module
        PRESETS = presets_module.PRESETS
    except ImportError:
        PRESETS = {}

    STAGE1     = cfg_module.STAGE1
    INDICATORS = cfg_module.INDICATORS

    try:
        import output_config as out_module
        OUT_COLUMNS = out_module.COLUMNS
        OUT_ALIASES = out_module.ALIASES
    except ImportError:
        print('Error: output_config.py not found. Copy output_config.example.py -> output_config.py and edit it.')
        sys.exit(1)

    # ── Tag listing (no scan needed) ─────────────────────────────────────
    if args.tree:
        from scanner.tag_query import print_tag_tree
        print_tag_tree(INDICATORS)
        sys.exit(0)

    if args.list is not None:
        from scanner.tag_query import list_subconditions
        list_subconditions(INDICATORS, query=args.list)
        sys.exit(0)

    if not args.scan:
        print('Error: --scan is required unless using --list or --tree.')
        sys.exit(1)

    # ── CLI overrides ────────────────────────────────────────────────────
    if args.min_cap is not None:
        STAGE1 = {**STAGE1, 'min_market_cap': args.min_cap}
    if args.sectors:
        STAGE1 = {**STAGE1, 'sectors': args.sectors}

    # ── Validate expression ──────────────────────────────────────────────
    from scanner.expression_parser import (
        parse_expression, evaluate_expression, get_required_indicators,
        get_required_tv_prefilters,
    )
    try:
        parse_expression(args.scan, PRESETS, INDICATORS)
    except (SyntaxError, ValueError) as e:
        print(f'Error in scan expression: {e}')
        sys.exit(1)

    required_indicators = get_required_indicators(args.scan, PRESETS, INDICATORS)
    tv_prefilter        = get_required_tv_prefilters(args.scan, PRESETS, INDICATORS)
    print(f'Scan: {args.scan}')
    print(f'Indicators needed: {", ".join(sorted(required_indicators))}')
    if tv_prefilter:
        print(f'TV prefilter: {", ".join(tv_prefilter)}')

    # ── Stage 1 ──────────────────────────────────────────────────────────
    from stage1.tv_screener import run_tv_screener
    cookies = None
    session = os.getenv('TV_SESSION_ID')
    if session:
        cookies = {'sessionid': session}

    print('\nRunning Stage 1 (TradingView screener)...')
    try:
        tickers, tv_df = run_tv_screener(STAGE1, prefilter=tv_prefilter, cookies=cookies)
    except Exception as e:
        print(f'Stage 1 failed: {e}')
        sys.exit(1)

    # Build symbol → Stage 1 row dict for output enrichment
    tv_by_symbol = {
        row['ticker'].split(':')[-1]: {k: v for k, v in row.items() if k != 'ticker'}
        for _, row in tv_df.iterrows()
    }

    if not tickers:
        print('Stage 1 returned no candidates. Exiting.')
        sys.exit(0)

    # ── Stage 2 — fetch history ──────────────────────────────────────────
    from stage2.data_fetcher import fetch_history, fetch_history_weekly

    daily_indicators   = [n for n in required_indicators
                          if INDICATORS[n].get('interval', '1d') == '1d']
    weekly_indicators  = [n for n in required_indicators
                          if INDICATORS[n].get('interval') == '1wk']

    print(f'\nFetching daily history for {len(tickers)} tickers...')

    history = fetch_history(tickers, days=STAGE1['history_days'])
    print(f'Daily history available for {len(history)} tickers.')

    weekly_history: dict[str, object] = {}
    if weekly_indicators:
        max_weeks = max(INDICATORS[n].get('history_weeks', 100) for n in weekly_indicators)
        print(f'Fetching weekly history ({max_weeks} weeks) for {len(tickers)} tickers...')
        weekly_history = fetch_history_weekly(tickers, weeks=max_weeks)
        print(f'Weekly history available for {len(weekly_history)} tickers.')

    if not history:
        print('No daily history fetched. Exiting.')
        sys.exit(0)

    # ── Stage 2 — compute indicators ────────────────────────────────────
    from stage2 import INDICATOR_MODULES
    print('\nComputing indicators...')

    raw_outputs_all: dict[str, dict] = {}
    for ticker in history:
        raw_outputs_all[ticker] = {}

        for ind_name in required_indicators:
            interval = INDICATORS[ind_name].get('interval', '1d')
            source   = weekly_history if interval == '1wk' else history
            df = source.get(ticker)
            if df is None:
                continue

            module = INDICATOR_MODULES.get(ind_name)
            if module is None:
                print(f'  Warning: no module for indicator {ind_name!r}')
                continue
            params = INDICATORS[ind_name]['params']
            try:
                raw_outputs_all[ticker][ind_name] = module.compute(df, params)
            except Exception as e:
                print(f'  Warning: {ind_name} failed for {ticker}: {e}')

    # ── Evaluate expression ──────────────────────────────────────────────
    from scanner.ranker import build_result, rank_results

    matched_results = []
    for ticker, outputs in raw_outputs_all.items():
        try:
            matched = evaluate_expression(args.scan, outputs, PRESETS, INDICATORS)
        except Exception as e:
            print(f'  Warning: evaluation failed for {ticker}: {e}')
            continue
        if matched:
            result = build_result(ticker, outputs, args.scan, matched, INDICATORS, PRESETS,
                                  tv_data=tv_by_symbol.get(ticker, {}))
            matched_results.append(result)

    ranked = rank_results(matched_results)
    if args.limit:
        ranked = ranked[:args.limit]

    # ── Output ───────────────────────────────────────────────────────────
    from output.formatter import print_results, save_xlsx
    print_results(ranked, scan=args.scan)

    from datetime import datetime
    ts = datetime.now().strftime('%Y%m%d_%H%M')
    out_path = args.output or os.path.join('output', f'stockscreener_result_{ts}.xlsx')
    save_xlsx(ranked, out_path, scan=args.scan,
              indicators=INDICATORS, columns=OUT_COLUMNS, aliases=OUT_ALIASES)


if __name__ == '__main__':
    main()
