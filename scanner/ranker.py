from models.results import ScreenerResult


_SYNC_BULL = {
    'saty_ribbon': {'close_above_ema21', 'ema21_above_ema48'},
    'ttm_squeeze': {'momentum_above_zero'},
}
_SYNC_BEAR = {
    'saty_ribbon': {'close_above_ema21': False, 'ema21_above_ema48': False},
    'ttm_squeeze': {'momentum_above_zero': False},
}


def _determine_sync(raw_outputs: dict) -> tuple[bool, str]:
    ribbon = raw_outputs.get('saty_ribbon', {})
    squeeze = raw_outputs.get('ttm_squeeze', {})

    if not ribbon or not squeeze:
        return True, ''

    ribbon_bull  = ribbon.get('close_above_ema21') and ribbon.get('ema21_above_ema48')
    squeeze_bull = squeeze.get('momentum_above_zero')

    if ribbon_bull and squeeze_bull:
        return True, 'Both bullish'
    if (not ribbon_bull) and (not squeeze_bull):
        return True, 'Both bearish'
    if ribbon_bull and not squeeze_bull:
        return False, 'Ribbon bullish / Squeeze bearish'
    return False, 'Ribbon bearish / Squeeze bullish'


def build_result(
    ticker: str,
    raw_outputs: dict,
    expression: str,
    matched: bool,
    indicators: dict,
    presets: dict,
    tv_data: dict | None = None,
) -> ScreenerResult:
    matched_subs = []
    for ind_name, ind_cfg in indicators.items():
        raw = raw_outputs.get(ind_name, {})
        for sub_name, sub_def in ind_cfg.get('subconditions', {}).items():
            from scanner.evaluator import evaluate_subcondition
            if evaluate_subcondition(raw, sub_def):
                matched_subs.append(f'{ind_name}.{sub_name}')

    in_sync, sync_note = _determine_sync(raw_outputs)

    return ScreenerResult(
        ticker=ticker,
        scan=expression,
        raw_outputs=raw_outputs,
        expression_matched=matched,
        matched_subconditions=matched_subs,
        in_sync=in_sync,
        sync_note=sync_note,
        tv_data=tv_data or {},
    )


def rank_results(results: list[ScreenerResult]) -> list[ScreenerResult]:
    def _score(r: ScreenerResult) -> tuple:
        ribbon  = r.raw_outputs.get('saty_ribbon', {})
        squeeze = r.raw_outputs.get('ttm_squeeze', {})

        sync_score        = 1 if r.in_sync else 0
        compression_bars  = squeeze.get('compression_bars', 0)
        dot_priority      = {'Orange': 3, 'Red': 2, 'Black': 1, 'Green': 0}
        dot_score         = dot_priority.get(squeeze.get('dot_color', ''), 0)
        ema_stack_score   = sum([
            ribbon.get('ema8_above_ema13',   False),
            ribbon.get('ema13_above_ema21',  False),
            ribbon.get('ema21_above_ema48',  False),
            ribbon.get('ema48_above_ema200', False),
        ])
        return (sync_score, dot_score, compression_bars, ema_stack_score)

    return sorted(results, key=_score, reverse=True)
