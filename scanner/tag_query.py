"""
Tag-based subcondition browser.

Tags are stored as a list on each subcondition in config.py, e.g.:
    'tags': ['bullish', 'entry']

Convention:
  - First tag is always the direction: bullish | bearish | neutral
  - Remaining tags are types: trend | entry | momentum | reversal |
    breakout | compression | divergence | extreme | exit | continuation

Query format (passed to list_subconditions):
  ''              → full tag tree
  'bullish'       → all bullish subconditions
  'bullish.entry' → bullish AND entry
  'entry'         → all with entry tag (any direction)
"""

DIRECTIONS = {'bullish', 'bearish', 'neutral'}

TYPES = {
    'trend', 'entry', 'momentum', 'reversal',
    'breakout', 'compression', 'divergence',
    'extreme', 'exit', 'continuation',
}

ALL_TAGS = DIRECTIONS | TYPES


def _all_tagged(indicators: dict) -> list[tuple[str, str, list]]:
    """Return [(indicator_name, subcondition_name, tags), ...] for all subconditions."""
    rows = []
    for ind_name, ind_cfg in indicators.items():
        for sub_name, sub_def in ind_cfg.get('subconditions', {}).items():
            tags = sub_def.get('tags', [])
            rows.append((ind_name, sub_name, tags))
    return rows


def _matches(tags: list, query: str) -> bool:
    if not query:
        return True
    if '.' in query:
        parts = [p.strip() for p in query.split('.')]
        return all(p in tags for p in parts)
    return query in tags


def list_subconditions(indicators: dict, query: str = '') -> None:
    query = query.strip().lower()
    rows  = _all_tagged(indicators)
    matches = [(ind, sub, tags) for ind, sub, tags in rows if _matches(tags, query)]

    if not matches:
        print(f'No subconditions matched: {query!r}')
        return

    # Group by indicator
    by_indicator: dict[str, list] = {}
    for ind, sub, tags in matches:
        by_indicator.setdefault(ind, []).append((sub, tags))

    title = f'Subconditions matching: {query!r}' if query else 'All subconditions'
    print(f'\n{title} ({len(matches)} total)')
    print('=' * 60)

    for ind_name, subs in by_indicator.items():
        print(f'\n{ind_name}')
        max_sub_len = max(len(s) for s, _ in subs)
        for sub_name, tags in subs:
            tag_str = ', '.join(tags) if tags else '(untagged)'
            print(f'  .{sub_name:<{max_sub_len}}  [{tag_str}]')

    print()


def print_tag_tree(indicators: dict) -> None:
    """Print a two-level hierarchy: direction → type → subconditions."""
    rows = _all_tagged(indicators)

    # Build tree: direction -> type -> [(indicator, subcondition)]
    tree: dict[str, dict[str, list]] = {}
    untagged = []

    for ind, sub, tags in rows:
        if not tags:
            untagged.append((ind, sub))
            continue
        direction = tags[0] if tags[0] in DIRECTIONS else 'neutral'
        types     = [t for t in tags[1:] if t in TYPES] or ['(untyped)']
        for t in types:
            tree.setdefault(direction, {}).setdefault(t, []).append((ind, sub, tags))

    direction_order = ['bullish', 'bearish', 'neutral']
    type_order = ['trend', 'entry', 'momentum', 'reversal', 'breakout',
                  'compression', 'divergence', 'extreme', 'exit', 'continuation']

    total = sum(
        len(subs)
        for d in tree.values()
        for subs in d.values()
    )
    print(f'\nSubcondition tag tree ({total} total)\n' + '=' * 60)

    for direction in direction_order:
        if direction not in tree:
            continue
        direction_subs = sum(len(v) for v in tree[direction].values())
        print(f'\n{direction.upper()} ({direction_subs})')

        for type_tag in type_order:
            if type_tag not in tree[direction]:
                continue
            subs = tree[direction][type_tag]
            print(f'  {type_tag} ({len(subs)})')
            for ind, sub, tags in subs:
                extra = [t for t in tags[1:] if t != type_tag and t in TYPES]
                extra_str = f'  +{", ".join(extra)}' if extra else ''
                print(f'    {ind}.{sub}{extra_str}')

    if untagged:
        print(f'\nUNTAGGED ({len(untagged)})')
        for ind, sub in untagged:
            print(f'  {ind}.{sub}')

    print()
