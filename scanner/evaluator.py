SUFFIX_OPS = ('__gte', '__lte', '__gt', '__lt', '__in')


def evaluate_subcondition(raw: dict, subcondition: dict) -> bool:
    for key, threshold in subcondition.items():
        if key == 'tags':
            continue
        op = None
        field = key
        for suffix in SUFFIX_OPS:
            if key.endswith(suffix):
                op    = suffix[2:]   # strip leading __
                field = key[:-len(suffix)]
                break

        if field not in raw:
            return False

        value = raw[field]

        if op is None:
            if isinstance(threshold, list):
                if value not in threshold:
                    return False
            else:
                if value != threshold:
                    return False
        elif op == 'gte':
            if not (value >= threshold):
                return False
        elif op == 'lte':
            if not (value <= threshold):
                return False
        elif op == 'gt':
            if not (value > threshold):
                return False
        elif op == 'lt':
            if not (value < threshold):
                return False
        elif op == 'in':
            if value not in threshold:
                return False

    return True
