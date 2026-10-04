"""Read a bounded, explicitly declared subset of native Tau normal-form text.

Parsing grants no semantic authority. Re-render the AST with its original sorts
and require both native implications and the independent support checks. Native
Tau 7625580 spells term XOR '^'; '+' requires an explicit legacy-alias option.
"""
import re


class NormalizedParseError(ValueError):
    pass


_BINARY = {
    '||': (10, 'orF', 'formula'), '&&': (20, 'andF', 'formula'),
    '=': (40, 'eq0', 'comparison'), '!=': (40, 'ne0', 'comparison'),
    '|': (50, 'or', 'term'), '^': (60, 'xor', 'term'),
    '+': (60, 'xor', 'term'), '&': (70, 'and', 'term'),
}
_FORM_TAGS = frozenset(('T', 'F', 'eq0', 'ne0', 'notF', 'andF', 'orF'))
_RESERVED = frozenset(('all', 'ex', 'exists', 'tau', 'sbf', 'normalize', 'valid', 'sat'))


def _sort(ast):
    return 'formula' if ast[0] in _FORM_TAGS else 'term'


def _tokens(text, names, allow_legacy_plus):
    if not isinstance(text, str) or len(text) > 4000:
        raise NormalizedParseError('normal form must be a string of at most 4000 characters')
    result, pos = [], 0
    while pos < len(text):
        char = text[pos]
        if char.isspace():
            pos += 1
            continue
        pair = text[pos:pos + 2]
        if pair in ('&&', '||', '!='):
            result.append(pair)
            pos += 2
            continue
        if char.isalpha() or char == '_':
            match = re.match(r'[A-Za-z_][A-Za-z_0-9]*', text[pos:])
            if match is None:
                raise NormalizedParseError('only ASCII variable names are accepted')
            word = match.group()
            if word in ('T', 'F'):
                result.append(word)
            elif word in _RESERVED or any(letter not in names for letter in word):
                raise NormalizedParseError('undeclared name or unsupported keyword: ' + word)
            else:
                # Each letter is a separately declared variable; adjacency is meet.
                result.extend(word)
            pos += len(word)
            continue
        if char == '+' and not allow_legacy_plus:
            raise NormalizedParseError("native XOR uses '^'; '+' is not an admitted native operator")
        if char not in "01()'=!&|^+":
            raise NormalizedParseError('unsupported token at offset ' + str(pos))
        result.append(char)
        pos += 1
    if len(result) > 2000:
        raise NormalizedParseError('normal form token limit exceeded')
    return result


class _Parser:
    def __init__(self, tokens, names):
        self.tokens, self.names, self.pos = tokens, names, 0

    def peek(self):
        return self.tokens[self.pos] if self.pos < len(self.tokens) else None

    def take(self):
        token = self.peek()
        if token is None:
            raise NormalizedParseError('unexpected end of normal form')
        self.pos += 1
        return token

    def expression(self, minimum=0, depth=0):
        if depth > 128:
            raise NormalizedParseError('normal form nesting limit exceeded')
        token = self.take()
        if token in self.names:
            left = ('var', token)
        elif token in ('0', '1'):
            left = ('zero',) if token == '0' else ('one',)
        elif token in ('T', 'F'):
            left = (token,)
        elif token == '(':
            left = self.expression(0, depth + 1)
            if self.take() != ')':
                raise NormalizedParseError('unclosed grouping')
        elif token == '!':
            left = self.expression(30, depth + 1)
            if _sort(left) != 'formula':
                raise NormalizedParseError('logical negation requires a formula')
            left = ('notF', left)
        else:
            raise NormalizedParseError('expected an admitted atom or grouping')
        while True:
            token = self.peek()
            if token == "'":
                if 80 < minimum:
                    break
                self.take()
                if _sort(left) != 'term':
                    raise NormalizedParseError('postfix complement requires a term')
                left = ('not', left)
                continue
            implicit = token in self.names or token == '('
            operator = '&' if implicit else token
            if operator not in _BINARY:
                break
            precedence, tag, required = _BINARY[operator]
            if precedence < minimum:
                break
            if not implicit:
                self.take()
            right = self.expression(precedence + 1, depth + 1)
            if required == 'comparison':
                if _sort(left) != 'term' or right != ('zero',):
                    raise NormalizedParseError('only term equality/inequality to literal zero is accepted')
                left = (tag, left)
            else:
                if _sort(left) != required or _sort(right) != required:
                    raise NormalizedParseError('operator operands have incompatible sorts')
                left = (tag, left, right)
        return left


def parse_normalized_formula(text, declared_vars, *, allow_legacy_plus=False):
    """Return engine/corpus tuple tags, or reject the entire unsupported input."""
    names = tuple(declared_vars)
    if (len(names) != len(set(names)) or
            any(not isinstance(name, str) or re.fullmatch('[a-z]', name) is None for name in names)):
        raise NormalizedParseError('declare unique single-letter lowercase variable names')
    parser = _Parser(_tokens(text, frozenset(names), allow_legacy_plus), frozenset(names))
    ast = parser.expression()
    if parser.peek() is not None:
        raise NormalizedParseError('trailing or unsupported input')
    if _sort(ast) != 'formula':
        raise NormalizedParseError('the normalizer baseline requires a formula')
    stack, count = [(ast, 0)], 0
    while stack:
        node, depth = stack.pop()
        count += 1
        if count > 1000 or depth > 128:
            raise NormalizedParseError('normal form AST resource limit exceeded')
        if node[0] not in ('var', 'zero', 'one', 'T', 'F'):
            stack.extend((child, depth + 1) for child in node[1:])
    return ast


def parse_native_output(stdout, declared_vars, *, allow_legacy_plus=False):
    """Read exactly one history result; exit status/diagnostics remain caller gates."""
    if not isinstance(stdout, str):
        raise NormalizedParseError('native output must be text')
    match = re.fullmatch(r'%1:\s*(.*?)\s*', stdout, flags=re.DOTALL)
    if match is None:
        raise NormalizedParseError('expected exactly one native history result')
    return parse_normalized_formula(match.group(1), declared_vars,
                                    allow_legacy_plus=allow_legacy_plus)


parse_normalized = parse_normalized_formula
