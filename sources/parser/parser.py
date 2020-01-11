from ply import yacc

from lexer import *
from .classes import *

precedence = (
    ('left', 'ADD', 'SUB'),
    ('left', 'MUL', 'DIV'),
    ('right', 'PLUS'),
    ('right', 'MINUS')
)

# start = "statements"


def p_program(p):
    """ program : statements """

    if not parser.errors:
        p[0] = ProgramStatements(p[1], parser.symbols_table)  # parsed program!


def p_statements_rec(p):
    """ statements : statements empty_statement
                   | statements declaration_statement
                   | statements assignment_statement """

    p[1].append(p[2]) if p[2] else p[1]; p[0] = p[1]


def p_statements_end(p):
    """ statements : empty_statement
                   | declaration_statement
                   | assignment_statement """

    p[0] = ([p[1]] if p[1] else [])


def p_statements_rec_error(p):
    """ statements : statements error ';' """

    print(
        colorize('blue', f"info: invalid statement, at "
                         f"{p.lineno(2)}:{p.lexpos(2) - p.lexer.lexdata.rfind(NEWLINE, 0, p.lexpos(2))}"
                 )
    ); parser.errok()


def p_statements_end_error(p):
    """ statements : error ';' """

    print(
        colorize('blue', f"info: invalid statement, at "
                         f"{p.lineno(1)}:{p.lexpos(1) - p.lexer.lexdata.rfind(NEWLINE, 0, p.lexpos(1))}"
                 )
    ); parser.errok()


def p_assignment_statement(p):
    """ assignment_statement : variable_usage '=' arithmetic_expression ';'
                             | array_usage '=' arithmetic_expression ';' """

    p[0] = AssignmentStatement(p[1], p[3], (p.lineno(2), p.lexpos(2)), p)


def p_assignment_statement_error(p):
    """ assignment_statement : error '=' arithmetic_expression ';'
                             | variable_usage '=' error ';'
                             | array_usage '=' error ';'
                             | error '=' error ';' """

    print(
        colorize('blue', "info: invalid assignment statement."
                 )
    )
    parser.errok()


def p_arithmetic_expression_rec_par(p):
    """ arithmetic_expression : '(' arithmetic_expression ')' """

    p[0] = p[2]


def p_arithmetic_expression_rec_una(p):
    """ arithmetic_expression : '-' arithmetic_expression %prec MINUS
                              | '+' arithmetic_expression %prec PLUS """

    p[0] = Unary.operation[p[1]](p[2], (p.lineno(1), p.lexpos(1))).\
        create_temp_var(parser.symbols_table)


def p_arithmetic_expression_rec_bin(p):
    """ arithmetic_expression : arithmetic_expression '+' arithmetic_expression %prec ADD
                              | arithmetic_expression '-' arithmetic_expression %prec SUB
                              | arithmetic_expression '*' arithmetic_expression %prec MUL
                              | arithmetic_expression '/' arithmetic_expression %prec DIV """

    p[0] = Binary.operation[p[2]](p[1], p[3], (p.lineno(2), p.lexpos(2))).\
        create_temp_var(parser.symbols_table)


def p_arithmetic_expression_end(p):
    """ arithmetic_expression : numeric_constant
                              | function_call
                              | variable_usage
                              | array_usage """

    p[0] = p[1]


def p_function_call(p):
    """ function_call : function_name '(' arithmetic_expression ')' """

    try:
        p[0] = FunctionCall(p[1], p[3], (p.lineno(1), p.lexpos(1)), p).\
            create_temp_var(parser.symbols_table)
    except NameError:
        parser.errors = True
        raise SyntaxError


def p_function_name(p):
    """ function_name : IDENTIFIER_TOKEN """

    if p[1] not in trigonometric_functions.keys():
        print(
            colorize('red', f"\n"
                            f"error: using unknown function '{p[1]}', at "
                            f"{p.lineno(1)}:{p.lexpos(1) - p.lexer.lexdata.rfind(NEWLINE, 0, p.lexpos(1))}\n" +
                     colorize('crimson', f"{p.lexer.lexdata.split(NEWLINE)[p.lineno(1) - 1]}\n"
                              f"{' ' * (p.lexpos(1) - p.lexer.lexdata.rfind(NEWLINE, 0, p.lexpos(1)) - 1) + '^'}")
                     )
        )
        parser.errors = True
    else:
        p[0] = p[1]


def p_variable_usage(p):
    """ variable_usage : IDENTIFIER_TOKEN """

    p[1] = f"_{p[1]}"
    variable = parser.symbols_table.has_declaration(p[1], VariableDeclaration)

    if variable:
        p[0] = VariableUsage(p[1], variable.data_type, (p.lineno(1), p.lexpos(1)))
    else:
        print(
            colorize('red', f"\n"
                            f"error: usage of undeclared variable '{p[1]}', at "
                            f"{p.lineno(1)}:{p.lexpos(1) - p.lexer.lexdata.rfind(NEWLINE, 0, p.lexpos(1))}\n"
                            f"{p.lexer.lexdata.split(NEWLINE)[p.lineno(1) - 1]}\n"
                            f"{' ' * (p.lexpos(1) - p.lexer.lexdata.rfind(NEWLINE, 0, p.lexpos(1)) - 1) + '^'}"
                     )
        )
        parser.errors = True
        raise SyntaxError


def p_array_usage(p):
    """ array_usage : IDENTIFIER_TOKEN '[' arithmetic_expression ']' """

    p[1] = f"_{p[1]}"
    array = parser.symbols_table.has_declaration(p[1], ArrayDeclaration)

    if array:
        try:
            p[0] = ArrayUsage(p[1], array.data_type, array.size, p[3], (p.lineno(1), p.lexpos(1)))
        except IndexError as e:
            print(
                colorize('red', f"\n"
                                f"error: {e.args[0]}, at "
                                f"{p.lineno(1)}:{p.lexpos(1) - p.lexer.lexdata.rfind(NEWLINE, 0, p.lexpos(1))}")
                + NEWLINE +
                colorize('blue', f"info: array '{p[1]}' must be indexed by valid positive integral value!")
            )
            parser.errors = True
            raise SyntaxError
        except TypeError as e:
            print(
                colorize('red', f"\n"
                                f"error: {e.args[0]}, at "
                                f"{p.lineno(1)}:{p.lexpos(1) - p.lexer.lexdata.rfind(NEWLINE, 0, p.lexpos(1))}")
                + NEWLINE +
                colorize('blue', f"info: array '{p[1]}' must be indexed by valid integral value or variable!")
            )
            parser.errors = True
            raise SyntaxError
    else:
        print(
            colorize('red', f"\n"
                            f"error: usage of undeclared array '{p[1]}', at "
                            f"{p.lineno(1)}:{p.lexpos(1) - p.lexer.lexdata.rfind(NEWLINE, 0, p.lexpos(1))}\n"
                            f"{p.lexer.lexdata.split(NEWLINE)[p.lineno(1) - 1]}\n"
                            f"{' ' * (p.lexpos(1) - p.lexer.lexdata.rfind(NEWLINE, 0, p.lexpos(1)) - 1) + '^'}"
                     )
        )
        parser.errors = True
        raise SyntaxError


def p_numeric_integral_constant(p):
    """ numeric_constant : INTEGRAL_CONSTANT """

    p[0] = parser.symbols_table.add_numeric_constant(IntegralConstant(p[1], (p.lineno(1), p.lexpos(1))))


def p_numeric_decimal_constant(p):
    """ numeric_constant : DECIMAL_CONSTANT """

    p[0] = parser.symbols_table.add_numeric_constant(DecimalConstant(p[1], (p.lineno(1), p.lexpos(1))))


def p_declaration_statement(p):
    """ declaration_statement : declaration_type declaration_list ';' """

    for symbol in DeclarationStatement(p[2], p[1]):
        try:
            parser.symbols_table.add_declaration(symbol) if symbol else None
        except LookupError as e:
            print(
                colorize('red', f"\n"
                                f"error: symbol '{e.args[0].identifier}' {e.args[1]}") +
                colorize('red', NEWLINE +
                         f"{p.lexer.lexdata.split(NEWLINE)[e.args[3].position[0] - 1]}\n"
                         f"{' '*(e.args[3].position[1]-p.lexer.lexdata.rfind(NEWLINE,0,e.args[3].position[1])-1)+'^'}")
                + NEWLINE +
                colorize('blue',
                         f"info: '{e.args[2].identifier}' was defined at "
                         f"{e.args[2].position[0]}:"
                         f"{e.args[2].position[1] - p.lexer.lexdata.rfind(NEWLINE, 0, e.args[2].position[1])}\n"

                         )
            )
            parser.errors = True


def p_declaration_statement_error(p):
    """ declaration_statement : declaration_type error ';' """

    print(
        colorize('blue', "info: invalid declaration statement."
                 )
    )
    parser.errok()


def p_declaration_type(p):
    """ declaration_type : FLOAT_TYPE
                         | DOUBLE_TYPE
                         | SHORT_TYPE
                         | INT_TYPE """

    p[0] = p[1]  # type`s string


def p_declaration_list_variable_declaration_rec(p):
    """ declaration_list : declaration_list ',' IDENTIFIER_TOKEN """

    p[1].append(
        VariableDeclaration(identifier=p[3], position=(p.lineno(3), p.lexpos(3)))
    ); p[0] = p[1]


def p_declaration_list_array_declaration_rec(p):
    """ declaration_list : declaration_list ',' IDENTIFIER_TOKEN '[' INTEGRAL_CONSTANT ']' """

    try:
        p[1].append(
            ArrayDeclaration(identifier=p[3], size=p[5], position=(p.lineno(3), p.lexpos(3)))
        ); p[0] = p[1]
    except AssertionError as e:
        print(
            colorize('red', f"\n"
                            f"error: {e.args[1]}")
            + NEWLINE +
            colorize('blue', f"info: array '{e.args[0]}' declared with size of {e.args[2]}, at "
                             f"{e.args[3][0]}:{e.args[3][1] - p.lexer.lexdata.rfind(NEWLINE, 0, e.args[3][1])}")
        )
        parser.errors = True
        p[0] = p[1]


def p_declaration_list_variable_declaration_end(p):
    """ declaration_list : IDENTIFIER_TOKEN """

    p[0] = [
        VariableDeclaration(identifier=p[1], position=(p.lineno(1), p.lexpos(1)))
    ]


def p_declaration_list_array_declaration_end(p):
    """ declaration_list : IDENTIFIER_TOKEN '[' INTEGRAL_CONSTANT ']' """

    try:
        p[0] = [
            ArrayDeclaration(identifier=p[1], size=p[3], position=(p.lineno(1), p.lexpos(1)))
        ]
    except AssertionError as e:
        print(
            colorize('red', f"\n"
                            f"error: {e.args[1]}")
            + NEWLINE +
            colorize('blue', f"info: array '{e.args[0]}' declared with size of {e.args[2]}, at "
                             f"{e.args[3][0]}:{e.args[3][1] - p.lexer.lexdata.rfind(NEWLINE, 0, e.args[3][1])}")
        )
        parser.errors = True
        p[0] = []


def p_empty_statement(p):
    """ empty_statement : epsilon ';' """
    # do nothing

    print(
        colorize('yellow', f"\n"
                           f"warning: empty statement, at "
                           f"{p.lineno(1)}:{p.lexpos(1) - p.lexer.lexdata.rfind(NEWLINE, 0, p.lexpos(1))}")
    )


def p_epsilon(p):
    """ epsilon : """
    pass


def p_error(p):
    if p:
        print(
            colorize('red', NEWLINE +
                     f"error: unexpected token: '{p.value}', at "
                     f"{p.lineno}:{p.lexpos - p.lexer.lexdata.rfind(NEWLINE, 0, p.lexpos)}, here:"),
            colorize('crimson', NEWLINE +
                     f"{p.lexer.lexdata.split(NEWLINE)[p.lineno-1]}\n"
                     f"{' '*(p.lexpos-p.lexer.lexdata.rfind(NEWLINE, 0, p.lexpos)-1) + '^'}")
            + NEWLINE +
            colorize('violet',
                     f"hint: expected tokens: "
                     f"{', '.join(t for t in set(map(get_token_type, parser.action[parser.state].keys())) if t)}")
        )
        parser.errors = True
    else:
        print(
            colorize('red', "\n"
                            "error: unexpected EOF!")
            + NEWLINE +
            colorize('blue', "info: missed semicolon?")
        )
        parser.errors = True
        exit(1)


parser = yacc.yacc(
    # debug=False,
    # optimize=True,
    write_tables=True,
    start="program",
    # outputdir="outdir",
    tabmodule="parsetab"
)

parser.symbols_table = SymbolsTable()

parser.errors = False
