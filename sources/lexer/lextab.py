# lextab.py. This file automatically created by PLY (version 3.11). Don't edit!
_tabversion   = '3.10'
_lextokens    = set(('COS_FUNCTION', 'DECIMAL_CONSTANT', 'DOUBLE_TYPE', 'FLOAT_TYPE', 'IDENTIFIER_TOKEN', 'INTEGRAL_CONSTANT', 'INT_TYPE', 'SHORT_TYPE', 'SIN_FUNCTION'))
_lexreflags   = 96
_lexliterals  = '()[],;+-*/='
_lexstateinfo = {'INITIAL': 'inclusive'}
_lexstatere   = {'INITIAL': [('(?P<t_IDENTIFIER_TOKEN>[a-zA-Z_][a-zA-Z_0-9]*)|(?P<t_DECIMAL_CONSTANT>-?[0-9]+\\.[0-9]+)|(?P<t_INTEGRAL_CONSTANT>0|-?[1-9][0-9]*)|(?P<t_newline>\\n+)', [None, ('t_IDENTIFIER_TOKEN', 'IDENTIFIER_TOKEN'), ('t_DECIMAL_CONSTANT', 'DECIMAL_CONSTANT'), ('t_INTEGRAL_CONSTANT', 'INTEGRAL_CONSTANT'), ('t_newline', 'newline')])]}
_lexstateignore = {'INITIAL': ' '}
_lexstateerrorf = {'INITIAL': 't_error'}
_lexstateeoff = {}
