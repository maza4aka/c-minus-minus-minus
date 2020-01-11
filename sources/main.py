from compiler import *


def main(code: str):
    result = parser.parse(
        code, tracking=True,
        # debug=True
    )

    if not parser.errors and not lexer.errors:
        return repr(result)
    else:
        exit(1)


if __name__ == '__main__':
    with open('example.cmmm', 'r') as c:
        with open('example.s', 'w') as a:
            a.write("// example.s\n" + main(c.read()))
