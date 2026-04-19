import datetime
from models.results import ScreenerResult

BUILTIN_SOURCES = {'ticker', 'scan', 'matched_subconditions', 'in_sync', 'sync_note', 'date_run'}
_SUFFIX_OPS = ('__gte', '__lte', '__gt', '__lt', '__in')


def _fmt_float(v) -> str:
    if v is None or (isinstance(v, float) and v != v):
        return 'N/A'
    return f'{v:.4f}'


def _resolve_value(source: str, r: ScreenerResult, scan: str, date_run: str):
    if source == 'ticker':                  return r.ticker
    if source == 'scan':                    return scan
    if source == 'matched_subconditions':   return ', '.join(r.matched_subconditions)
    if source == 'in_sync':                 return r.in_sync
    if source == 'sync_note':               return r.sync_note
    if source == 'date_run':                return date_run
    if '.' in source:
        ns, field = source.split('.', 1)
        if ns == 'tv':
            return r.tv_data.get(field)
        return r.raw_outputs.get(ns, {}).get(field)
    return None


def _required_filter_fields(r: ScreenerResult, indicators: dict) -> dict:
    """
    Returns {source_string: auto_alias} for every field used in the matched
    subconditions that must appear in output regardless of user config.
    """
    required = {}
    for sub_ref in r.matched_subconditions:
        if '.' not in sub_ref:
            continue
        ind_name, sub_name = sub_ref.split('.', 1)
        sub_def = (indicators.get(ind_name, {})
                             .get('subconditions', {})
                             .get(sub_name, {}))
        for key in sub_def:
            if key in ('tags', 'tv_prefilter'):
                continue
            field = key
            for suffix in _SUFFIX_OPS:
                if key.endswith(suffix):
                    field = key[:-len(suffix)]
                    break
            source = f'{ind_name}.{field}'
            if source not in required:
                required[source] = f'{ind_name}.{field}'
    return required


def print_results(results: list[ScreenerResult], scan: str = '') -> None:
    if not results:
        print('\nNo results matched the scan criteria.')
        return

    print(f'\n{"=" * 60}')
    print(f'SCAN: {scan}  |  {len(results)} result(s)')
    print(f'{"=" * 60}')

    for r in results:
        sync_mark = 'Y' if r.in_sync else 'N'
        print(f'\nTICKER: {r.ticker}  |  IN SYNC: {sync_mark}  {r.sync_note}')
        print(f'MATCHED: {", ".join(r.matched_subconditions)}')
        print('-' * 50)

        for ind_name, raw in r.raw_outputs.items():
            if not raw:
                continue
            print(f'{ind_name.upper().replace("_", " ")}')
            for field, value in raw.items():
                if isinstance(value, bool):
                    print(f'  {field}: {"Y" if value else "N"}')
                elif isinstance(value, float):
                    print(f'  {field}: {_fmt_float(value)}')
                elif value is not None:
                    print(f'  {field}: {value}')

    print(f'\n{"=" * 60}\n')


def save_xlsx(results: list[ScreenerResult], path: str, scan: str,
              indicators: dict, columns: list, aliases: dict) -> None:
    try:
        import openpyxl
    except ImportError:
        print('openpyxl not installed — skipping XLSX output. Run: pip install openpyxl')
        return

    import pandas as pd
    date_run = datetime.date.today().isoformat()

    # Build ordered working column map (alias -> source) from user-specified COLUMNS
    col_map: dict[str, str] = {}
    for alias in columns:
        if alias in aliases:
            col_map[alias] = aliases[alias]

    covered_sources: set[str] = set(col_map.values())

    # Enforce: any field that drove a matched subcondition must appear in output
    auto_added: list[str] = []
    for r in results:
        for source, auto_alias in _required_filter_fields(r, indicators).items():
            if source not in covered_sources:
                # use a pretty alias from aliases if one maps to this source, else raw key
                pretty = next((a for a, s in aliases.items() if s == source), auto_alias)
                col_map[pretty] = source
                covered_sources.add(source)
                auto_added.append(pretty)

    if auto_added:
        print(f'  Note: auto-added filter fields to output: {", ".join(sorted(set(auto_added)))}')

    rows = []
    for r in results:
        row = {alias: _resolve_value(source, r, scan, date_run)
               for alias, source in col_map.items()}
        rows.append(row)

    df = pd.DataFrame(rows)
    df.to_excel(path, index=False)
    print(f'Saved {len(rows)} results to {path}')
