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
    p.add_argument('--scan',       required=True, help='Scan expression or preset name')
    p.add_argument('--limit',      type=int,   default=None, help='Max results to display')
    p.add_argument('--output',     default=None, help='Save results to this .xlsx path')
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

    # ── CLI overrides ────────────────────────────────────────────────────
    if args.min_cap is not None:
        STAGE1 = {**STAGE1, 'min_market_cap': args.min_cap}
    if args.sectors:
        STAGE1 = {**STAGE1, 'sectors': args.sectors}

    # ── Validate expression ──────────────────────────────────────────────
    from scanner.expression_parser import (
        parse_expression, evaluate_expression, get_required_indicators
    )
    try:
        parse_expression(args.scan, PRESETS, INDICATORS)
    except (SyntaxError, ValueError) as e:
        print(f'Error in scan expression: {e}')
        sys.exit(1)

    required_indicators = get_required_indicators(args.scan, PRESETS, INDICATORS)
    print(f'Scan: {args.scan}')
    print(f'Indicators needed: {", ".join(sorted(required_indicators))}')

    # ── Stage 1 ──────────────────────────────────────────────────────────
    from stage1.tv_screener import run_tv_screener
    cookies = None
    session = os.getenv('TV_SESSION_ID')
    if session:
        cookies = {'sessionid': session}

    print('\nRunning Stage 1 (TradingView screener)...')
    try:
        tickers, tv_data = run_tv_screener(STAGE1, cookies=cookies)
    except Exception as e:
        print(f'Stage 1 failed: {e}')
        sys.exit(1)

    if not tickers:
        print('Stage 1 returned no candidates. Exiting.')
        sys.exit(0)

    # ── Stage 2 — fetch history ──────────────────────────────────────────
    from stage2.data_fetcher import fetch_history
    print(f'\nFetching history for {len(tickers)} tickers...')
    history = fetch_history(tickers, days=STAGE1['history_days'])
    print(f'History available for {len(history)} tickers.')

    if not history:
        print('No history fetched. Exiting.')
        sys.exit(0)

    # ── Stage 2 — compute indicators ────────────────────────────────────
    from stage2 import INDICATOR_MODULES
    print('\nComputing indicators...')

    raw_outputs_all: dict[str, dict] = {}
    for ticker, df in history.items():
        raw_outputs_all[ticker] = {}
        for ind_name in required_indicators:
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
            result = build_result(ticker, outputs, args.scan, matched, INDICATORS, PRESETS)
            matched_results.append(result)

    ranked = rank_results(matched_results)
    if args.limit:
        ranked = ranked[:args.limit]

    # ── Output ───────────────────────────────────────────────────────────
    from output.formatter import print_results, save_xlsx
    print_results(ranked, scan=args.scan)

    if args.output:
        save_xlsx(ranked, args.output, scan=args.scan)


if __name__ == '__main__':
    main()
