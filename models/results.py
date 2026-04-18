from dataclasses import dataclass, field


@dataclass
class IndicatorRawOutput:
    indicator: str
    ticker: str
    values: dict


@dataclass
class ScreenerResult:
    ticker: str
    raw_outputs: dict        # {indicator_name: raw_values_dict}
    expression_matched: bool
    matched_subconditions: list = field(default_factory=list)
    in_sync: bool = False
    sync_note: str = ''
