from ply import lex

import re


def colorize(color: str, s: str):
    if color == 'crimson':
        return f"\033[1;31m{s}\033[0m"
    elif color == 'red':
        return f"\33[31m{s}\33[0m"
    elif color == 'yellow':
        return f"\33[33m{s}\33[0m"
    elif color == 'blue':
        return f"\33[34m{s}\33[0m"
    elif color == 'violet':
        return f"\33[35m{s}\33[0m"
    else:  # invalid color
        return f"{s}"


_token_types = {
    'identifier': ['IDENTIFIER_TOKEN'],
    'numeric constant': ['DECIMAL_CONSTANT', 'INTEGRAL_CONSTANT'],
    'data type': ['DOUBLE_TYPE', 'FLOAT_TYPE', 'INT_TYPE', 'SHORT_TYPE'],
    'function': ['SIN_FUNCTION', 'COS_FUNCTION'],
    '(': ['('], ')': [')'], '[': ['['], ']': [']'],
    'arithmetic operator': ['+', '-', '*', '/'],
    'coma': [','], 'semicolon': [';'], 'equal sign': ['=']
}


def get_token_type(t):
    for key, value in _token_types.items():
        if t in value:
            return key


NEWLINE = '\n'

tokens = [
    'IDENTIFIER_TOKEN'
]

constants = [
    'DECIMAL_CONSTANT', 'INTEGRAL_CONSTANT'
]

qw_types = {
    'double': 'DOUBLE_TYPE'
}

dw_types = {
    'float':  'FLOAT_TYPE',
    'int':    'INT_TYPE'
}

w_types = {
    'short': 'SHORT_TYPE'
}

integral_types = [
    'short', 'int'
]

fractional_types = [
    'float', 'double'
]

types = {
    **dw_types,
    **qw_types,
    **w_types
}

trigonometric_functions = {
    'sin': 'SIN_FUNCTION', 'cos': 'COS_FUNCTION'
}

functions = {**trigonometric_functions}

reserved = {**types}

tokens = tokens + constants + list(types.values())  # without functions.

literals = [
    '(', ')', '[', ']',
    ',', ';',
    '+', '-', '*', '/',
    '='
]


def t_IDENTIFIER_TOKEN(t):
    r"""[a-zA-Z][a-zA-Z_0-9]*"""  # '_' in front of id is reserved for code generation
    t.type = reserved.get(t.value, 'IDENTIFIER_TOKEN')
    return t


@lex.TOKEN(r'[0-9]+\.[0-9]*')
def t_DECIMAL_CONSTANT(t):
    t.value = float(t.value)
    return t


@lex.TOKEN(r'0|[1-9][0-9]*')
def t_INTEGRAL_CONSTANT(t):
    t.value = int(t.value)
    return t


t_ignore = " "

newlines_pattern = r'\n+'


@lex.TOKEN(newlines_pattern)
def t_newline(t):
    t.lexer.lineno += len(t.value)


def t_error(t):
    print(
        colorize('red', f"error: illegal character: '{t.value[0]}', at "
                        f"{t.lineno}:{t.lexpos - t.lexer.lexdata.rfind(NEWLINE, 0, t.lexpos)}\n"
                        f"{lexer.lexdata.split(NEWLINE)[t.lineno - 1]}\n"
                        f"{' ' * (t.lexpos - lexer.lexdata.rfind(NEWLINE, 0, t.lexpos) - 1) + '^'}"
                 )
    )
    lexer.errors = True
    t.lexer.skip(1)


lexer = lex.lex(
    # debug=False,
    # optimize=True,
    reflags=re.UNICODE | re.VERBOSE,
    lextab="lextab"
)

lexer.errors = False
