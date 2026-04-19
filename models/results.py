from dataclasses import dataclass, field


@dataclass
class IndicatorRawOutput:
    indicator: str
    ticker: str
    values: dict


@dataclass
class ScreenerResult:
    ticker: str
    scan: str
    raw_outputs: dict        # {indicator_name: raw_values_dict}
    expression_matched: bool
    matched_subconditions: list = field(default_factory=list)
    in_sync: bool = False
    sync_note: str = ''
    tv_data: dict = field(default_factory=dict)  # Stage 1 fields: close, volume, market_cap_basic, sector, etc.
