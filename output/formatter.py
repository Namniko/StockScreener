import datetime
from models.results import ScreenerResult


def _fmt_float(v) -> str:
    if v is None or (isinstance(v, float) and v != v):
        return 'N/A'
    return f'{v:.2f}'


def _ema_stack_str(r: dict) -> str:
    parts = []
    labels = [('ema8', 8), ('ema13', 13), ('ema21', 21), ('ema48', 48), ('ema200', 200)]
    prev_v = None
    for key, span in labels:
        v = r.get(key)
        if v is None:
            parts.append(f'{span}(?)')
            continue
        label = f'{span}({_fmt_float(v)})'
        if prev_v is not None:
            sep = ' > ' if prev_v >= v else ' < '
        else:
            sep = ''
        parts.append(sep + label if sep else label)
        prev_v = v
    return ''.join(parts)


def print_results(results: list[ScreenerResult], scan: str = '') -> None:
    if not results:
        print('\nNo results matched the scan criteria.')
        return

    print(f'\n{"=" * 60}')
    print(f'SCAN: {scan}  |  {len(results)} result(s)')
    print(f'{"=" * 60}')

    for r in results:
        ribbon  = r.raw_outputs.get('saty_ribbon', {})
        squeeze = r.raw_outputs.get('ttm_squeeze', {})
        sync_mark = 'Y' if r.in_sync else 'N'

        print(f'\nTICKER: {r.ticker}  |  IN SYNC: {sync_mark}  {r.sync_note}')
        print(f'MATCHED: {", ".join(r.matched_subconditions)}')
        print('-' * 50)

        if ribbon:
            print('SATY RIBBON (raw)')
            print(f'  EMA Stack: {_ema_stack_str(ribbon)}')
            print(f'  Close: {_fmt_float(ribbon.get("close"))}  |  '
                  f'Low: {_fmt_float(ribbon.get("low"))}  |  '
                  f'High: {_fmt_float(ribbon.get("high"))}')
            lt21 = 'Y' if ribbon.get('low_touched_ema21') else 'N'
            ca21 = 'Y' if ribbon.get('close_above_ema21') else 'N'
            print(f'  Pullback: Low touched EMA21 {lt21}  |  Close above EMA21 {ca21}')
            if ribbon.get('ema21_crossed_above_ema200_recently'):
                print('  200 EMA: Golden Cross (recent)')
            elif ribbon.get('ema21_crossed_below_ema200_recently'):
                print('  200 EMA: Death Cross (recent)')
            else:
                print('  200 EMA: Inactive')

        if squeeze:
            dot   = squeeze.get('dot_color', '?')
            cbars = squeeze.get('compression_bars', 0)
            mom   = squeeze.get('momentum_value', 0)
            mcol  = squeeze.get('momentum_color', '?')
            above = '+' if squeeze.get('momentum_above_zero') else '-'
            rising = 'rising' if squeeze.get('momentum_rising') else 'falling'
            atr_d = squeeze.get('atr_distance', 0)

            compression_label = {
                'Orange': 'High Compression',
                'Red':    'Mid Compression',
                'Black':  'Low Compression',
                'Green':  'No Squeeze',
            }.get(dot, '?')

            print('TTM SQUEEZE (raw)')
            print(f'  Dot: {dot} ({cbars} bars) -> {compression_label}')
            print(f'  Momentum: {_fmt_float(mom)} {above} ({mcol}) | above zero: {squeeze.get("momentum_above_zero")}, {rising}')
            if squeeze.get('first_green_dot'):
                print(f'  ATR Dist: {_fmt_float(atr_d)}')

    print(f'\n{"=" * 60}\n')


def save_xlsx(results: list[ScreenerResult], path: str, scan: str = '') -> None:
    try:
        import openpyxl
    except ImportError:
        print('openpyxl not installed — skipping XLSX output. Run: pip install openpyxl')
        return

    import pandas as pd
    rows = []
    date_run = datetime.date.today().isoformat()

    for r in results:
        ribbon  = r.raw_outputs.get('saty_ribbon', {})
        squeeze = r.raw_outputs.get('ttm_squeeze', {})

        ema_stack = (
            f"8({_fmt_float(ribbon.get('ema8'))}) "
            f"13({_fmt_float(ribbon.get('ema13'))}) "
            f"21({_fmt_float(ribbon.get('ema21'))}) "
            f"48({_fmt_float(ribbon.get('ema48'))}) "
            f"200({_fmt_float(ribbon.get('ema200'))})"
        )

        rows.append({
            'ticker':     r.ticker,
            'scan':       scan,
            'in_sync':    r.in_sync,
            'sync_note':  r.sync_note,
            'ribbon_ema_stack':   ema_stack,
            'ribbon_close':       ribbon.get('close'),
            'ribbon_low':         ribbon.get('low'),
            'ribbon_high':        ribbon.get('high'),
            'ribbon_ema8':        ribbon.get('ema8'),
            'ribbon_ema13':       ribbon.get('ema13'),
            'ribbon_ema21':       ribbon.get('ema21'),
            'ribbon_ema48':       ribbon.get('ema48'),
            'ribbon_ema200':      ribbon.get('ema200'),
            'ribbon_matched':     ', '.join(
                s for s in r.matched_subconditions if s.startswith('saty_ribbon.')
            ),
            'squeeze_dot_color':        squeeze.get('dot_color'),
            'squeeze_compression_bars': squeeze.get('compression_bars'),
            'squeeze_momentum_value':   squeeze.get('momentum_value'),
            'squeeze_momentum_color':   squeeze.get('momentum_color'),
            'squeeze_atr_distance':     squeeze.get('atr_distance'),
            'squeeze_matched':    ', '.join(
                s for s in r.matched_subconditions if s.startswith('ttm_squeeze.')
            ),
            'date_run': date_run,
        })

    df = pd.DataFrame(rows)
    df.to_excel(path, index=False)
    print(f'Saved {len(rows)} results to {path}')
