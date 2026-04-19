"""
Expression parser for scan expressions.

Grammar (+ binds tighter than |):
  expr   := term (| term)*
  term   := factor (+ factor)*
  factor := ( expr ) | atom
  atom   := indicator.subcondition  |  preset_name
"""
from __future__ import annotations
from scanner.evaluator import evaluate_subcondition


def _tokenize(expr: str) -> list[str]:
    tokens = []
    i = 0
    while i < len(expr):
        c = expr[i]
        if c in '()|+':
            tokens.append(c)
            i += 1
        elif c == ' ':
            i += 1
        else:
            j = i
            while j < len(expr) and expr[j] not in '()|+ ':
                j += 1
            tokens.append(expr[i:j])
            i = j
    return tokens


class _Parser:
    def __init__(self, tokens: list[str]):
        self.tokens = tokens
        self.pos = 0

    def peek(self) -> str | None:
        return self.tokens[self.pos] if self.pos < len(self.tokens) else None

    def consume(self, expected: str | None = None) -> str:
        tok = self.tokens[self.pos]
        if expected and tok != expected:
            raise SyntaxError(f'Expected {expected!r}, got {tok!r}')
        self.pos += 1
        return tok

    def parse_expr(self):
        left = self.parse_term()
        while self.peek() == '|':
            self.consume('|')
            right = self.parse_term()
            left  = ('or', left, right)
        return left

    def parse_term(self):
        left = self.parse_factor()
        while self.peek() == '+':
            self.consume('+')
            right = self.parse_factor()
            left  = ('and', left, right)
        return left

    def parse_factor(self):
        if self.peek() == '(':
            self.consume('(')
            node = self.parse_expr()
            self.consume(')')
            return node
        return ('atom', self.consume())


def _resolve_presets(expr: str, presets: dict) -> str:
    for name, expansion in presets.items():
        expr = expr.replace(name, f'({expansion})')
    return expr


def _eval_ast(node, raw_outputs: dict, indicators: dict) -> bool:
    kind = node[0]
    if kind == 'and':
        return _eval_ast(node[1], raw_outputs, indicators) and \
               _eval_ast(node[2], raw_outputs, indicators)
    if kind == 'or':
        return _eval_ast(node[1], raw_outputs, indicators) or \
               _eval_ast(node[2], raw_outputs, indicators)
    if kind == 'atom':
        atom = node[1]
        if '.' not in atom:
            raise ValueError(f'Unresolved name in expression: {atom!r}')
        indicator_name, sub_name = atom.split('.', 1)
        if indicator_name not in indicators:
            raise ValueError(f'Unknown indicator: {indicator_name!r}')
        subconditions = indicators[indicator_name].get('subconditions', {})
        if sub_name not in subconditions:
            raise ValueError(f'Unknown subcondition: {indicator_name}.{sub_name}')
        raw = raw_outputs.get(indicator_name, {})
        return evaluate_subcondition(raw, subconditions[sub_name])
    raise ValueError(f'Unknown AST node type: {kind!r}')


def parse_expression(expr: str, presets: dict, indicators: dict):
    resolved = _resolve_presets(expr, presets)
    tokens   = _tokenize(resolved)
    parser   = _Parser(tokens)
    ast      = parser.parse_expr()
    if parser.pos != len(parser.tokens):
        raise SyntaxError(f'Unexpected token: {parser.peek()!r}')
    return ast


def evaluate_expression(expr: str, raw_outputs: dict, presets: dict, indicators: dict) -> bool:
    ast = parse_expression(expr, presets, indicators)
    return _eval_ast(ast, raw_outputs, indicators)


def get_required_indicators(expr: str, presets: dict, indicators: dict) -> set[str]:
    ast = parse_expression(expr, presets, indicators)
    required = set()

    def _walk(node):
        if node[0] in ('and', 'or'):
            _walk(node[1])
            _walk(node[2])
        elif node[0] == 'atom':
            name = node[1]
            if '.' in name:
                required.add(name.split('.', 1)[0])

    _walk(ast)
    return required


def get_required_tv_prefilters(expr: str, presets: dict, indicators: dict) -> dict:
    """
    Collect tv_prefilter hints from all leaf subconditions in the expression.
    Only returns filter keys where every subcondition that declares an opinion
    agrees on the same value — safe for OR expressions (never over-filters).
    """
    ast = parse_expression(expr, presets, indicators)
    opinions: dict[str, list] = {}  # key -> list of values from subconditions that have it

    def _walk(node):
        if node[0] in ('and', 'or'):
            _walk(node[1])
            _walk(node[2])
        elif node[0] == 'atom':
            name = node[1]
            if '.' not in name:
                return
            ind_name, sub_name = name.split('.', 1)
            sub_cfg = indicators.get(ind_name, {}).get('subconditions', {}).get(sub_name, {})
            for key, val in sub_cfg.get('tv_prefilter', {}).items():
                opinions.setdefault(key, []).append(val)

    _walk(ast)
    # Only apply a filter if all opinions agree
    return {k: vals[0] for k, vals in opinions.items() if len(set(vals)) == 1}
