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
    p.add_argument('--scan',       default=None, help='Scan expression, preset name, or comma-separated list of scans')
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

    # ── Parse and validate all scan expressions ──────────────────────────
    from scanner.expression_parser import (
        parse_expression, evaluate_expression, get_required_indicators,
        get_required_tv_prefilters,
    )

    scans = [s.strip() for s in args.scan.split(',')]
    for scan in scans:
        try:
            parse_expression(scan, PRESETS, INDICATORS)
        except (SyntaxError, ValueError) as e:
            print(f'Error in scan expression "{scan}": {e}')
            sys.exit(1)

    # ── Stage 1 — run independently per scan (each has its own prefilter) ─
    from stage1.tv_screener import run_tv_screener
    cookies = None
    session = os.getenv('TV_SESSION_ID')
    if session:
        cookies = {'sessionid': session}

    scan_tickers: dict[str, list[str]] = {}  # scan -> Stage 1 ticker list
    tv_by_symbol: dict[str, dict]      = {}  # sym  -> Stage 1 row dict

    for scan in scans:
        required_for_scan = get_required_indicators(scan, PRESETS, INDICATORS)
        tv_prefilter      = get_required_tv_prefilters(scan, PRESETS, INDICATORS)
        print(f'\nScan: {scan}')
        print(f'Indicators needed: {", ".join(sorted(required_for_scan))}')
        if tv_prefilter:
            print(f'TV prefilter: {", ".join(tv_prefilter)}')

        print('Running Stage 1 (TradingView screener)...')
        try:
            tickers, tv_df = run_tv_screener(STAGE1, prefilter=tv_prefilter, cookies=cookies)
        except Exception as e:
            print(f'Stage 1 failed for "{scan}": {e}')
            sys.exit(1)

        scan_tickers[scan] = tickers
        for _, row in tv_df.iterrows():
            sym = row['ticker'].split(':')[-1]
            tv_by_symbol[sym] = {k: v for k, v in row.items() if k != 'ticker'}

    all_tickers = list(dict.fromkeys(
        t for tickers in scan_tickers.values() for t in tickers
    ))

    if not all_tickers:
        print('\nAll scans returned no candidates. Exiting.')
        sys.exit(0)

    # ── Stage 2 — fetch history once for union of all tickers ────────────
    from stage2.data_fetcher import fetch_history, fetch_history_weekly

    all_required: set[str] = set()
    for scan in scans:
        all_required |= get_required_indicators(scan, PRESETS, INDICATORS)

    weekly_indicators = [n for n in all_required
                         if INDICATORS[n].get('interval') == '1wk']

    print(f'\nFetching daily history for {len(all_tickers)} tickers...')
    history = fetch_history(all_tickers, days=STAGE1['history_days'])
    print(f'Daily history available for {len(history)} tickers.')

    weekly_history: dict[str, object] = {}
    if weekly_indicators:
        max_weeks = max(INDICATORS[n].get('history_weeks', 100) for n in weekly_indicators)
        print(f'Fetching weekly history ({max_weeks} weeks) for {len(all_tickers)} tickers...')
        weekly_history = fetch_history_weekly(all_tickers, weeks=max_weeks)
        print(f'Weekly history available for {len(weekly_history)} tickers.')

    if not history:
        print('No daily history fetched. Exiting.')
        sys.exit(0)

    # ── Stage 2 — compute all required indicators once per ticker ─────────
    from stage2 import INDICATOR_MODULES
    print('\nComputing indicators...')

    raw_outputs_all: dict[str, dict] = {}
    for ticker in history:
        raw_outputs_all[ticker] = {}
        for ind_name in all_required:
            interval = INDICATORS[ind_name].get('interval', '1d')
            source   = weekly_history if interval == '1wk' else history
            df       = source.get(ticker)
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

    # ── Evaluate each scan against its own Stage 1 candidates ────────────
    from scanner.ranker import build_result, rank_results

    # ticker -> (result, [scan, ...]) — first result wins for data, scans accumulate
    matched_by_ticker: dict[str, tuple] = {}
    for scan in scans:
        scan_syms = {t.split(':')[-1] for t in scan_tickers[scan]}
        for ticker, outputs in raw_outputs_all.items():
            if ticker not in scan_syms:
                continue
            try:
                matched = evaluate_expression(scan, outputs, PRESETS, INDICATORS)
            except Exception as e:
                print(f'  Warning: evaluation failed for {ticker} ({scan}): {e}')
                continue
            if matched:
                if ticker not in matched_by_ticker:
                    result = build_result(ticker, outputs, scan, matched, INDICATORS, PRESETS,
                                          tv_data=tv_by_symbol.get(ticker, {}))
                    matched_by_ticker[ticker] = (result, [scan])
                else:
                    matched_by_ticker[ticker][1].append(scan)

    # Merge scan names onto each result
    matched_results = []
    for result, scan_names in matched_by_ticker.values():
        result.scan = ', '.join(scan_names)
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
    save_xlsx(ranked, out_path,
              indicators=INDICATORS, columns=OUT_COLUMNS, aliases=OUT_ALIASES)


if __name__ == '__main__':
    main()
