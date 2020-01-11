# intermediate representation classes

from dataclasses import *

from lexer import (
    NEWLINE,
    colorize,
    w_types, dw_types, qw_types,
    integral_types, fractional_types,
    types,
    trigonometric_functions
)


class Statement:

    def __init__(self, position):

        self.position = position

    @staticmethod  # idk, why not
    def data_type_size(data_type: str) -> int:
        if data_type in qw_types.keys():
            return 8
        elif data_type in dw_types.keys():
            return 4
        elif data_type in w_types.keys():
            return 2
        else:
            raise TypeError("unknown data type?")

    @staticmethod
    def data_type_conversion(data_type_one: str, data_type_two: str):
        data_types_priority = integral_types + fractional_types
        if data_types_priority.index(data_type_one) >= data_types_priority.index(data_type_two):
            return data_type_one
        else:  # elif data_type_two?
            return data_type_two

    @staticmethod
    def numeric_constant_type(data_type: str) -> str:
        if data_type in types.keys():
            return '.'+data_type
        else:
            raise TypeError("unknown constant type?")

    @staticmethod
    def instruction_data_suffix(data_type: str, fpu: bool = False) -> str:
        if data_type == 'short':
            return 'w'
        elif data_type == 'int':
            return 'l'
        elif data_type == 'float':
            return 's' if fpu else 'l'
        elif data_type == 'double':
            return 'l' if fpu else 'q'
        else:
            raise TypeError("unknown suffix?")

    @staticmethod
    def register_name_prefix(data_type: str):
        data_type_size = Statement.data_type_size(data_type)
        if data_type_size == 2:
            return ''  # if 16-bit
        elif data_type_size == 4:
            return 'e'  # 32-bit
        elif data_type_size == 8:
            return 'r'  # if 64-bit
        else:
            raise TypeError("unknown register?")


class Declaration:

    def __init__(self, identifier: str, position=None, data_type: str = None):
        self.identifier = f"_{identifier}"
        self.data_type = data_type

        self.position = position

    def __eq__(self, other):
        return (self.identifier == other) if type(other) is str else (self.identifier == other.identifier)


class VariableDeclaration(Declaration):

    def __init__(self, identifier: str, position=None, data_type: str = None):
        super().__init__(identifier, position, data_type)

    def __repr__(self):
        return f".comm {self.identifier}, {Statement.data_type_size(self.data_type)}"

    def __str__(self):
        return f"{self.__class__.__name__} -> " \
               f"{{data_type={self.data_type}, identifier='{self.identifier}'}}"


class ArrayDeclaration(Declaration):

    def __init__(self, identifier: str, size: int, position=None, data_type: str = None):
        super().__init__(identifier, position, data_type)
        if size < 1:
            raise AssertionError(identifier, 'invalid array size', size, position)
        else:
            self.size = size

    def __repr__(self):
        return f".comm {self.identifier}, {self.size * Statement.data_type_size(self.data_type)}"

    def __str__(self):
        return f"{self.__class__.__name__} -> " \
               f"{{data_type={self.data_type}, identifier='{self.identifier}', size={self.size}}}"


class DeclarationStatement(Statement):

    def __init__(self, declaration_list: [Declaration], data_type: str, position=None):
        super().__init__(position)

        self.declaration_list = declaration_list

        for declaration in self.declaration_list:
            declaration.data_type = data_type

    def __getitem__(self, index):
        return self.declaration_list[index]


class Expression:

    identifier: str

    def __init__(self, position):
        self.position = position

    data_type: str

    def create_temp_var(self, symbols_table):
        self.identifier = symbols_table.add_temporary_variable(self.data_type).identifier
        return self


class NumericConstant(Expression):

    def __init__(self, value: int or float, constant_type: str, position):
        super().__init__(position)

        self.data_type = constant_type
        self.value = value

        self.identifier = '_nc'

        self.create_temp_var = None  # do not call this here

    @property
    def identifier(self):
        return self.__identifier

    @identifier.setter
    def identifier(self, new_identifier):
        self.__identifier = new_identifier
        self.constant_id = self.__identifier

    def __eq__(self, other):
        return ((self.value == other.value) and (self.data_type == other.data_type)) \
            if type(other) not in (int, float) \
            else self.value == other

    def __repr__(self):
        return f"{self.constant_id}: {Statement.numeric_constant_type(self.data_type)} {self.value}"

    def __str__(self):
        return f"{self.__class__.__name__} -> " \
               f"{{constant_type={self.data_type}, constant_id='{self.constant_id}', value={self.value}}}"


class IntegralConstant(NumericConstant):

    def __init__(self, value: int, position):
        super().__init__(value, 'int', position)


class DecimalConstant(NumericConstant):

    def __init__(self, value: float, position):
        super().__init__(value, 'double', position)


class VariableUsage(Expression):

    def __init__(self, identifier: str, data_type: str, position):
        super().__init__(position)

        self.identifier = identifier
        self.data_type = data_type

        self.create_temp_var = None  # useless

    def __repr__(self):
        return f"mov{Statement.instruction_data_suffix(self.data_type)} {self.identifier}(%rip), "

    def __str__(self):
        return f"{self.__class__.__name__} -> " \
               f"{{data_type={self.data_type}, identifier='{self.identifier}'}}"


class ArrayUsage(Expression):

    def __init__(self, identifier: str, data_type: str, size: int, index: IntegralConstant, position):
        super().__init__(position)

        self.identifier = identifier

        self.data_type = data_type
        self.size = size

        if type(index) == IntegralConstant:
            if 0 <= index.value < self.size:
                self.index = index
            else:
                raise IndexError("array index out of bounds")
        else:
            if index.data_type in integral_types:
                self.index = index
            else:
                raise TypeError("non-integral indexer")

        self.create_temp_var = None  # useless

    def __repr__(self):  # maybe some cleanup?
        if type(self.index) == ArrayUsage:
            return f"{self.index.__repr__()}" \
                   f"%{Statement.register_name_prefix(self.index.data_type)}dx\n" \
                   f"\n" \
                   f"leaq {self.identifier}(%rip), %rsi\n" \
                   f"xor %rdi, %rdi\n" \
                   f"movl %{Statement.register_name_prefix(self.index.data_type)}dx, " \
                   f"%{Statement.register_name_prefix(self.index.data_type)}di\n" \
                   f"xor %rdx, %rdx\n" \
                   f"mov{Statement.instruction_data_suffix(self.data_type)} " \
                   f"(%rsi, %rdi, {Statement.data_type_size(self.data_type)}), "
        elif isinstance(self.index, (Unary, Binary, FunctionCall)):
            return f"{self.index.__repr__()}\n" \
                   f"leaq {self.identifier}(%rip), %rsi\n" \
                   f"xor %rdi, %rdi\n" \
                   f"mov{Statement.instruction_data_suffix(self.index.data_type)} " \
                   f"{self.index.identifier}(%rip), " \
                   f"%{Statement.register_name_prefix(self.index.data_type)}di\n" \
                   f"mov{Statement.instruction_data_suffix(self.data_type)} " \
                   f"(%rsi, %rdi, {Statement.data_type_size(self.data_type)}), "
        else:
            return f"leaq {self.identifier}(%rip), %rsi\n" \
                   f"xor %rdi, %rdi\n" \
                   f"mov{Statement.instruction_data_suffix(self.index.data_type)} " \
                   f"{self.index.identifier}(%rip), " \
                   f"%{Statement.register_name_prefix(self.index.data_type)}di\n" \
                   f"mov{Statement.instruction_data_suffix(self.data_type)} " \
                   f"(%rsi, %rdi, {Statement.data_type_size(self.data_type)}), "

    def __str__(self):
        return f"{self.__class__.__name__} -> " \
               f"{{data_type={self.data_type}, identifier='{self.identifier}', index={self.index}}}"


class FunctionCall(Expression):

    def __init__(self, function: str, argument: Expression, position, p):
        super().__init__(position)

        self.identifier = self.function = function
        self.argument = argument

        if self.function in trigonometric_functions.keys():
            self.data_type = 'double'
        else:  # !?
            raise NameError("unknown function name?")

    @property
    def identifier(self):
        return self.__identifier

    @identifier.setter
    def identifier(self, new_identifier):
        self.__identifier = new_identifier

    @property
    def data_type(self):
        return self.__data_type

    @data_type.setter
    def data_type(self, new_data_type):
        self.__data_type = new_data_type
        self.return_type = self.__data_type

    def __repr__(self):
        function = ''
        if not isinstance(self.argument, (Unary, Binary, FunctionCall, NumericConstant)):  # var or array usage
            function += f"{self.argument.__repr__()}" \
                        f"%{Statement.register_name_prefix(self.argument.data_type)}ax\n"
        elif isinstance(self.argument, NumericConstant):
            function += f"mov{Statement.instruction_data_suffix(self.argument.data_type)} {self.argument.identifier}" \
                        f"(%rip), %{Statement.register_name_prefix(self.argument.data_type)}ax"
        else:  # unary, binary or function call
            function += f"{self.argument.__repr__()}\n" \
                        f"mov{Statement.instruction_data_suffix(self.argument.data_type)} " \
                        f"{self.argument.identifier}(%rip), " \
                        f"%{Statement.register_name_prefix(self.argument.data_type)}ax\n"
        function += f"\n" \
                    f"pushq %rax\n" \
                    f"f{'' if self.argument.data_type in fractional_types else 'i'}ldl (%rsp)\n" \
                    f"f{self.function}\n" \
                    f"fstp{Statement.instruction_data_suffix(self.data_type, fpu=True)} (%rsp)\n" \
                    f"popq %rax\n"
        return function + f"\n" \
                          f"mov{Statement.instruction_data_suffix(self.data_type)} " \
                          f"%{Statement.register_name_prefix(self.data_type)}ax, " \
                          f"{self.identifier}(%rip)\n" \
                          f"\n" \
                          f"xor %rax, %rax" \
                          f"\n"

    def __str__(self):
        return f"{self.__class__.__name__} -> " \
               f"{{function={self.function}, argument={self.argument}}}"


class Unary(Expression):

    operation: dict

    def __init__(self, expression: Expression, position):
        super().__init__(position)

        self.expression = expression

        self.data_type = expression.data_type

    def __str__(self):
        return f"{self.__class__.__name__} -> " \
               f"{{expression={self.expression}}}"


class Minus(Unary):

    def __init__(self, expression: Expression, position):
        super().__init__(expression, position)

    def __repr__(self):
        expression = ''
        if not isinstance(self.expression, (Unary, Binary, FunctionCall)):  # const, var or array usage
            if isinstance(self.expression, NumericConstant):
                expression += f"mov{Statement.instruction_data_suffix(self.expression.data_type)} " \
                              f"{self.expression.identifier}(%rip), "
            else:
                expression += f"{self.expression.__repr__()}"
            expression += f"%{Statement.register_name_prefix(self.expression.data_type)}ax\n"
        else:  # unary, binary or function call
            expression += f"{self.expression.__repr__()}\n" \
                          f"mov{Statement.instruction_data_suffix(self.expression.data_type)} " \
                          f"{self.expression.identifier}(%rip), " \
                          f"%{Statement.register_name_prefix(self.expression.data_type)}ax\n"
        if self.expression.data_type in fractional_types:
            expression += f"\n" \
                          f"pushq %rax\n" \
                          f"fldl (%rsp)\n" \
                          f"fchs\n" \
                          f"fstp{Statement.instruction_data_suffix(self.data_type, fpu=True)} (%rsp)\n" \
                          f"popq %rax\n"
        else:  # elif self.expression.data_type in integral_types:
            expression += f"\n" \
                          f"neg{Statement.instruction_data_suffix(self.expression.data_type)} " \
                          f"%{Statement.register_name_prefix(self.expression.data_type)}ax\n"
        return expression + f"\n" \
                            f"mov{Statement.instruction_data_suffix(self.expression.data_type)} " \
                            f"%{Statement.register_name_prefix(self.expression.data_type)}ax, " \
                            f"{self.identifier}(%rip)\n" \
                            f"\n" \
                            f"xor %rax, %rax" \
                            f"\n"


Unary.operation = {
    '-': Minus,
    '+': (lambda expr, pos: expr)
}


class Binary(Expression):

    operation: dict

    def __init__(self, left: Expression, right: Expression, position):
        super().__init__(position)

        self.left = left
        self.right = right

        self.data_type = Statement.data_type_conversion(left.data_type, right.data_type)

    def __str__(self):
        return f"{self.__class__.__name__} -> " \
               f"{{left={self.left}, right={self.right}}}"


class Add(Binary):

    def __init__(self, left: Expression, right: Expression, position):
        super().__init__(left, right, position)

    def __repr__(self):
        arithmetic = ''

        # generating code for left operand
        if not isinstance(self.left, (Unary, Binary, FunctionCall)):  # const, var or array usage
            if isinstance(self.left, NumericConstant):
                arithmetic += f"mov{Statement.instruction_data_suffix(self.left.data_type)} " \
                              f"{self.left.identifier}(%rip), "
            else:
                arithmetic += f"{self.left.__repr__()}"
            arithmetic += f"%{Statement.register_name_prefix(self.left.data_type)}ax\n"
            arithmetic += f"pushq %rax" \
                          f"\n"
            if not ((self.data_type == 'short') and (self.left.data_type == 'int')) and \
               not ((self.data_type == 'int') and (self.left.data_type == 'short')) and \
                    (self.data_type != self.left.data_type):
                if self.data_type in fractional_types:
                    if self.left.data_type in fractional_types:
                        arithmetic += f"fld{Statement.instruction_data_suffix(self.left.data_type, fpu=True)} " \
                                      f"(%rsp)\n"
                    else:  # elif self.left.data_type in integral_types:
                        arithmetic += f"fildl (%rsp)\n"
                    arithmetic += f"fstp{Statement.instruction_data_suffix(self.data_type, fpu=True)} " \
                                  f"(%rsp)\n"
                elif self.data_type in integral_types:
                    arithmetic += f"fld{Statement.instruction_data_suffix(self.left.data_type, fpu=True)} " \
                                  f"(%rsp)\n" \
                                  f"fistpl (%rsp)\n"
                else:
                    arithmetic += f"\n"
        else:  # unary, binary or function call
            arithmetic += f"{self.left.__repr__()}\n" \
                          f"mov{Statement.instruction_data_suffix(self.left.data_type)} " \
                          f"{self.left.identifier}(%rip), " \
                          f"%{Statement.register_name_prefix(self.left.data_type)}ax\n"
            arithmetic += f"pushq %rax" \
                          f"\n"
            if not ((self.data_type == 'short') and (self.left.data_type == 'int')) and \
               not ((self.data_type == 'int') and (self.left.data_type == 'short')) and \
                    (self.data_type != self.left.data_type):
                if self.data_type in fractional_types:
                    if self.left.data_type in fractional_types:
                        arithmetic += f"fld{Statement.instruction_data_suffix(self.left.data_type, fpu=True)} " \
                                      f"(%rsp)\n"
                    else:  # elif self.left.data_type in integral_types:
                        arithmetic += f"fildl (%rsp)\n"
                    arithmetic += f"fstp{Statement.instruction_data_suffix(self.data_type, fpu=True)} " \
                                  f"(%rsp)\n"
                elif self.data_type in integral_types:
                    arithmetic += f"fld{Statement.instruction_data_suffix(self.left.data_type, fpu=True)} " \
                                  f"(%rsp)\n" \
                                  f"fistpl (%rsp)\n"
                else:
                    arithmetic += f"\n"

        # generating code for right operand
        if not isinstance(self.right, (Unary, Binary, FunctionCall)):  # const, var or array usage
            if isinstance(self.right, NumericConstant):
                arithmetic += f"mov{Statement.instruction_data_suffix(self.right.data_type)} " \
                              f"{self.right.identifier}(%rip), "
            else:
                arithmetic += f"{self.right.__repr__()}"
            arithmetic += f"%{Statement.register_name_prefix(self.right.data_type)}ax\n"
            arithmetic += f"pushq %rax" \
                          f"\n"
            if not ((self.data_type == 'short') and (self.right.data_type == 'int')) and \
               not ((self.data_type == 'int') and (self.right.data_type == 'short')) and \
                    (self.data_type != self.right.data_type):
                if self.data_type in fractional_types:
                    if self.right.data_type in fractional_types:
                        arithmetic += f"fld{Statement.instruction_data_suffix(self.right.data_type, fpu=True)} " \
                                      f"(%rsp)\n"
                    else:  # elif self.left.data_type in integral_types:
                        arithmetic += f"fildl (%rsp)\n"
                    arithmetic += f"fstp{Statement.instruction_data_suffix(self.data_type, fpu=True)} " \
                                  f"(%rsp)\n"
                elif self.data_type in integral_types:
                    arithmetic += f"fld{Statement.instruction_data_suffix(self.right.data_type, fpu=True)} " \
                                  f"(%rsp)\n" \
                                  f"fistpl (%rsp)\n"
                else:
                    arithmetic += f"\n"
        else:  # unary, binary or function call
            arithmetic += f"{self.right.__repr__()}\n" \
                          f"mov{Statement.instruction_data_suffix(self.right.data_type)} " \
                          f"{self.right.identifier}(%rip), " \
                          f"%{Statement.register_name_prefix(self.right.data_type)}ax\n"
            arithmetic += f"pushq %rax" \
                          f"\n"
            if not ((self.data_type == 'short') and (self.right.data_type == 'int')) and \
               not ((self.data_type == 'int') and (self.right.data_type == 'short')) and \
                    (self.data_type != self.right.data_type):
                if self.data_type in fractional_types:
                    if self.right.data_type in fractional_types:
                        arithmetic += f"fld{Statement.instruction_data_suffix(self.right.data_type, fpu=True)} " \
                                      f"(%rsp)\n"
                    else:  # elif self.left.data_type in integral_types:
                        arithmetic += f"fildl (%rsp)\n"
                    arithmetic += f"fstp{Statement.instruction_data_suffix(self.data_type, fpu=True)} " \
                                  f"(%rsp)\n"
                elif self.data_type in integral_types:
                    arithmetic += f"fld{Statement.instruction_data_suffix(self.right.data_type, fpu=True)} " \
                                  f"(%rsp)\n" \
                                  f"fistpl (%rsp)\n"
                else:
                    arithmetic += f"\n"

        arithmetic += f"\npopq %rdx\npopq %rax\n" \
                      f"\n"

        if self.data_type in fractional_types:
            arithmetic += f"pushq %rdx\n" \
                          f"fld{Statement.instruction_data_suffix(self.data_type, fpu=True)} (%rsp)\n" \
                          f"popq %rdx\npushq %rax\n" \
                          f"fld{Statement.instruction_data_suffix(self.data_type, fpu=True)} (%rsp)\n" \
                          f"\n" \
                          f"faddp\n" \
                          f"\n" \
                          f"fstp{Statement.instruction_data_suffix(self.data_type, fpu=True)} (%rsp)\n" \
                          f"popq %rax\n" \
                          f"\n"
        else:  # elif self.data_type in integral_types:
            arithmetic += f"add{Statement.instruction_data_suffix(self.data_type)} " \
                          f"%{Statement.register_name_prefix(self.data_type)}dx, " \
                          f"%{Statement.register_name_prefix(self.data_type)}ax\n" \
                          f"\n"

        return arithmetic + f"mov{Statement.instruction_data_suffix(self.data_type)} " \
                            f"%{Statement.register_name_prefix(self.data_type)}ax, " \
                            f"{self.identifier}(%rip)\n" \
                            f"\nxor %rdx, %rdx\nxor %rax, %rax\n"


class Sub(Binary):

    def __init__(self, left: Expression, right: Expression, position):
        super().__init__(left, right, position)

    def __repr__(self):
        arithmetic = ''

        # generating code for left operand
        if not isinstance(self.left, (Unary, Binary, FunctionCall)):  # const, var or array usage
            if isinstance(self.left, NumericConstant):
                arithmetic += f"mov{Statement.instruction_data_suffix(self.left.data_type)} " \
                              f"{self.left.identifier}(%rip), "
            else:
                arithmetic += f"{self.left.__repr__()}"
            arithmetic += f"%{Statement.register_name_prefix(self.left.data_type)}ax\n"
            arithmetic += f"pushq %rax" \
                          f"\n"
            if not ((self.data_type == 'short') and (self.left.data_type == 'int')) and \
               not ((self.data_type == 'int') and (self.left.data_type == 'short')) and \
                    (self.data_type != self.left.data_type):
                if self.data_type in fractional_types:
                    if self.left.data_type in fractional_types:
                        arithmetic += f"fld{Statement.instruction_data_suffix(self.left.data_type, fpu=True)} " \
                                      f"(%rsp)\n"
                    else:  # elif self.left.data_type in integral_types:
                        arithmetic += f"fildl (%rsp)\n"
                    arithmetic += f"fstp{Statement.instruction_data_suffix(self.data_type, fpu=True)} " \
                                  f"(%rsp)\n"
                elif self.data_type in integral_types:
                    arithmetic += f"fld{Statement.instruction_data_suffix(self.left.data_type, fpu=True)} " \
                                  f"(%rsp)\n" \
                                  f"fistpl (%rsp)\n"
                else:
                    arithmetic += f"\n"
        else:  # unary, binary or function call
            arithmetic += f"{self.left.__repr__()}\n" \
                          f"mov{Statement.instruction_data_suffix(self.left.data_type)} " \
                          f"{self.left.identifier}(%rip), " \
                          f"%{Statement.register_name_prefix(self.left.data_type)}ax\n"
            arithmetic += f"pushq %rax" \
                          f"\n"
            if not ((self.data_type == 'short') and (self.left.data_type == 'int')) and \
               not ((self.data_type == 'int') and (self.left.data_type == 'short')) and \
                    (self.data_type != self.left.data_type):
                if self.data_type in fractional_types:
                    if self.left.data_type in fractional_types:
                        arithmetic += f"fld{Statement.instruction_data_suffix(self.left.data_type, fpu=True)} " \
                                      f"(%rsp)\n"
                    else:  # elif self.left.data_type in integral_types:
                        arithmetic += f"fildl (%rsp)\n"
                    arithmetic += f"fstp{Statement.instruction_data_suffix(self.data_type, fpu=True)} " \
                                  f"(%rsp)\n"
                elif self.data_type in integral_types:
                    arithmetic += f"fld{Statement.instruction_data_suffix(self.left.data_type, fpu=True)} " \
                                  f"(%rsp)\n" \
                                  f"fistpl (%rsp)\n"
                else:
                    arithmetic += f"\n"

        # generating code for right operand
        if not isinstance(self.right, (Unary, Binary, FunctionCall)):  # const, var or array usage
            if isinstance(self.right, NumericConstant):
                arithmetic += f"mov{Statement.instruction_data_suffix(self.right.data_type)} " \
                              f"{self.right.identifier}(%rip), "
            else:
                arithmetic += f"{self.right.__repr__()}"
            arithmetic += f"%{Statement.register_name_prefix(self.right.data_type)}ax\n"
            arithmetic += f"pushq %rax" \
                          f"\n"
            if not ((self.data_type == 'short') and (self.right.data_type == 'int')) and \
               not ((self.data_type == 'int') and (self.right.data_type == 'short')) and \
                    (self.data_type != self.right.data_type):
                if self.data_type in fractional_types:
                    if self.right.data_type in fractional_types:
                        arithmetic += f"fld{Statement.instruction_data_suffix(self.right.data_type, fpu=True)} " \
                                      f"(%rsp)\n"
                    else:  # elif self.left.data_type in integral_types:
                        arithmetic += f"fildl (%rsp)\n"
                    arithmetic += f"fstp{Statement.instruction_data_suffix(self.data_type, fpu=True)} " \
                                  f"(%rsp)\n"
                elif self.data_type in integral_types:
                    arithmetic += f"fld{Statement.instruction_data_suffix(self.right.data_type, fpu=True)} " \
                                  f"(%rsp)\n" \
                                  f"fistpl (%rsp)\n"
                else:
                    arithmetic += f"\n"
        else:  # unary, binary or function call
            arithmetic += f"{self.right.__repr__()}\n" \
                          f"mov{Statement.instruction_data_suffix(self.right.data_type)} " \
                          f"{self.right.identifier}(%rip), " \
                          f"%{Statement.register_name_prefix(self.right.data_type)}ax\n"
            arithmetic += f"pushq %rax" \
                          f"\n"
            if not ((self.data_type == 'short') and (self.right.data_type == 'int')) and \
               not ((self.data_type == 'int') and (self.right.data_type == 'short')) and \
                    (self.data_type != self.right.data_type):
                if self.data_type in fractional_types:
                    if self.right.data_type in fractional_types:
                        arithmetic += f"fld{Statement.instruction_data_suffix(self.right.data_type, fpu=True)} " \
                                      f"(%rsp)\n"
                    else:  # elif self.left.data_type in integral_types:
                        arithmetic += f"fildl (%rsp)\n"
                    arithmetic += f"fstp{Statement.instruction_data_suffix(self.data_type, fpu=True)} " \
                                  f"(%rsp)\n"
                elif self.data_type in integral_types:
                    arithmetic += f"fld{Statement.instruction_data_suffix(self.right.data_type, fpu=True)} " \
                                  f"(%rsp)\n" \
                                  f"fistpl (%rsp)\n"
                else:
                    arithmetic += f"\n"

        arithmetic += f"\npopq %rdx\npopq %rax\n" \
                      f"\n"

        if self.data_type in fractional_types:
            arithmetic += f"pushq %rdx\n" \
                          f"fld{Statement.instruction_data_suffix(self.data_type, fpu=True)} (%rsp)\n" \
                          f"popq %rdx\npushq %rax\n" \
                          f"fld{Statement.instruction_data_suffix(self.data_type, fpu=True)} (%rsp)\n" \
                          f"\n" \
                          f"fsubp\n" \
                          f"\n" \
                          f"fstp{Statement.instruction_data_suffix(self.data_type, fpu=True)} (%rsp)\n" \
                          f"popq %rax\n" \
                          f"\n"
        else:  # elif self.data_type in integral_types:
            arithmetic += f"sub{Statement.instruction_data_suffix(self.data_type)} " \
                          f"%{Statement.register_name_prefix(self.data_type)}dx, " \
                          f"%{Statement.register_name_prefix(self.data_type)}ax\n" \
                          f"\n"

        return arithmetic + f"mov{Statement.instruction_data_suffix(self.data_type)} " \
                            f"%{Statement.register_name_prefix(self.data_type)}ax, " \
                            f"{self.identifier}(%rip)\n" \
                            f"\nxor %rdx, %rdx\nxor %rax, %rax\n"


class Mul(Binary):

    def __init__(self, left: Expression, right: Expression, position):
        super().__init__(left, right, position)

    def __repr__(self):
        arithmetic = ''

        # generating code for left operand
        if not isinstance(self.left, (Unary, Binary, FunctionCall)):  # const, var or array usage
            if isinstance(self.left, NumericConstant):
                arithmetic += f"mov{Statement.instruction_data_suffix(self.left.data_type)} " \
                              f"{self.left.identifier}(%rip), "
            else:
                arithmetic += f"{self.left.__repr__()}"
            arithmetic += f"%{Statement.register_name_prefix(self.left.data_type)}ax\n"
            arithmetic += f"pushq %rax" \
                          f"\n"
            if not ((self.data_type == 'short') and (self.left.data_type == 'int')) and \
               not ((self.data_type == 'int') and (self.left.data_type == 'short')) and \
                    (self.data_type != self.left.data_type):
                if self.data_type in fractional_types:
                    if self.left.data_type in fractional_types:
                        arithmetic += f"fld{Statement.instruction_data_suffix(self.left.data_type, fpu=True)} " \
                                      f"(%rsp)\n"
                    else:  # elif self.left.data_type in integral_types:
                        arithmetic += f"fildl (%rsp)\n"
                    arithmetic += f"fstp{Statement.instruction_data_suffix(self.data_type, fpu=True)} " \
                                  f"(%rsp)\n"
                elif self.data_type in integral_types:
                    arithmetic += f"fld{Statement.instruction_data_suffix(self.left.data_type, fpu=True)} " \
                                  f"(%rsp)\n" \
                                  f"fistpl (%rsp)\n"
                else:
                    arithmetic += f"\n"
        else:  # unary, binary or function call
            arithmetic += f"{self.left.__repr__()}\n" \
                          f"mov{Statement.instruction_data_suffix(self.left.data_type)} " \
                          f"{self.left.identifier}(%rip), " \
                          f"%{Statement.register_name_prefix(self.left.data_type)}ax\n"
            arithmetic += f"pushq %rax" \
                          f"\n"
            if not ((self.data_type == 'short') and (self.left.data_type == 'int')) and \
               not ((self.data_type == 'int') and (self.left.data_type == 'short')) and \
                    (self.data_type != self.left.data_type):
                if self.data_type in fractional_types:
                    if self.left.data_type in fractional_types:
                        arithmetic += f"fld{Statement.instruction_data_suffix(self.left.data_type, fpu=True)} " \
                                      f"(%rsp)\n"
                    else:  # elif self.left.data_type in integral_types:
                        arithmetic += f"fildl (%rsp)\n"
                    arithmetic += f"fstp{Statement.instruction_data_suffix(self.data_type, fpu=True)} " \
                                  f"(%rsp)\n"
                elif self.data_type in integral_types:
                    arithmetic += f"fld{Statement.instruction_data_suffix(self.left.data_type, fpu=True)} " \
                                  f"(%rsp)\n" \
                                  f"fistpl (%rsp)\n"
                else:
                    arithmetic += f"\n"

        # generating code for right operand
        if not isinstance(self.right, (Unary, Binary, FunctionCall)):  # const, var or array usage
            if isinstance(self.right, NumericConstant):
                arithmetic += f"mov{Statement.instruction_data_suffix(self.right.data_type)} " \
                              f"{self.right.identifier}(%rip), "
            else:
                arithmetic += f"{self.right.__repr__()}"
            arithmetic += f"%{Statement.register_name_prefix(self.right.data_type)}ax\n"
            arithmetic += f"pushq %rax" \
                          f"\n"
            if not ((self.data_type == 'short') and (self.right.data_type == 'int')) and \
               not ((self.data_type == 'int') and (self.right.data_type == 'short')) and \
                    (self.data_type != self.right.data_type):
                if self.data_type in fractional_types:
                    if self.right.data_type in fractional_types:
                        arithmetic += f"fld{Statement.instruction_data_suffix(self.right.data_type, fpu=True)} " \
                                      f"(%rsp)\n"
                    else:  # elif self.left.data_type in integral_types:
                        arithmetic += f"fildl (%rsp)\n"
                    arithmetic += f"fstp{Statement.instruction_data_suffix(self.data_type, fpu=True)} " \
                                  f"(%rsp)\n"
                elif self.data_type in integral_types:
                    arithmetic += f"fld{Statement.instruction_data_suffix(self.right.data_type, fpu=True)} " \
                                  f"(%rsp)\n" \
                                  f"fistpl (%rsp)\n"
                else:
                    arithmetic += f"\n"
        else:  # unary, binary or function call
            arithmetic += f"{self.right.__repr__()}\n" \
                          f"mov{Statement.instruction_data_suffix(self.right.data_type)} " \
                          f"{self.right.identifier}(%rip), " \
                          f"%{Statement.register_name_prefix(self.right.data_type)}ax\n"
            arithmetic += f"pushq %rax" \
                          f"\n"
            if not ((self.data_type == 'short') and (self.right.data_type == 'int')) and \
               not ((self.data_type == 'int') and (self.right.data_type == 'short')) and \
                    (self.data_type != self.right.data_type):
                if self.data_type in fractional_types:
                    if self.right.data_type in fractional_types:
                        arithmetic += f"fld{Statement.instruction_data_suffix(self.right.data_type, fpu=True)} " \
                                      f"(%rsp)\n"
                    else:  # elif self.left.data_type in integral_types:
                        arithmetic += f"fildl (%rsp)\n"
                    arithmetic += f"fstp{Statement.instruction_data_suffix(self.data_type, fpu=True)} " \
                                  f"(%rsp)\n"
                elif self.data_type in integral_types:
                    arithmetic += f"fld{Statement.instruction_data_suffix(self.right.data_type, fpu=True)} " \
                                  f"(%rsp)\n" \
                                  f"fistpl (%rsp)\n"
                else:
                    arithmetic += f"\n"

        arithmetic += f"\npopq %rdx\npopq %rax\n" \
                      f"\n"

        if self.data_type in fractional_types:
            arithmetic += f"pushq %rdx\n" \
                          f"fld{Statement.instruction_data_suffix(self.data_type, fpu=True)} (%rsp)\n" \
                          f"popq %rdx\npushq %rax\n" \
                          f"fld{Statement.instruction_data_suffix(self.data_type, fpu=True)} (%rsp)\n" \
                          f"\n" \
                          f"fmulp\n" \
                          f"\n" \
                          f"fstp{Statement.instruction_data_suffix(self.data_type, fpu=True)} (%rsp)\n" \
                          f"popq %rax\n" \
                          f"\n"
        else:  # elif self.data_type in integral_types:
            arithmetic += f"imul{Statement.instruction_data_suffix(self.data_type)} " \
                          f"%{Statement.register_name_prefix(self.data_type)}dx\n" \
                          f"\n"

        return arithmetic + f"mov{Statement.instruction_data_suffix(self.data_type)} " \
                            f"%{Statement.register_name_prefix(self.data_type)}ax, " \
                            f"{self.identifier}(%rip)\n" \
                            f"\nxor %rdx, %rdx\nxor %rax, %rax\n"


class Div(Binary):

    def __init__(self, left: Expression, right: Expression, position):
        super().__init__(left, right, position)

    def __repr__(self):
        arithmetic = ''

        # generating code for left operand
        if not isinstance(self.left, (Unary, Binary, FunctionCall)):  # const, var or array usage
            if isinstance(self.left, NumericConstant):
                arithmetic += f"mov{Statement.instruction_data_suffix(self.left.data_type)} " \
                              f"{self.left.identifier}(%rip), "
            else:
                arithmetic += f"{self.left.__repr__()}"
            arithmetic += f"%{Statement.register_name_prefix(self.left.data_type)}ax\n"
            arithmetic += f"pushq %rax" \
                          f"\n"
            if not ((self.data_type == 'short') and (self.left.data_type == 'int')) and \
               not ((self.data_type == 'int') and (self.left.data_type == 'short')) and \
                    (self.data_type != self.left.data_type):
                if self.data_type in fractional_types:
                    if self.left.data_type in fractional_types:
                        arithmetic += f"fld{Statement.instruction_data_suffix(self.left.data_type, fpu=True)} " \
                                      f"(%rsp)\n"
                    else:  # elif self.left.data_type in integral_types:
                        arithmetic += f"fildl (%rsp)\n"
                    arithmetic += f"fstp{Statement.instruction_data_suffix(self.data_type, fpu=True)} " \
                                  f"(%rsp)\n"
                elif self.data_type in integral_types:
                    arithmetic += f"fld{Statement.instruction_data_suffix(self.left.data_type, fpu=True)} " \
                                  f"(%rsp)\n" \
                                  f"fistpl (%rsp)\n"
                else:
                    arithmetic += f"\n"
        else:  # unary, binary or function call
            arithmetic += f"{self.left.__repr__()}\n" \
                          f"mov{Statement.instruction_data_suffix(self.left.data_type)} " \
                          f"{self.left.identifier}(%rip), " \
                          f"%{Statement.register_name_prefix(self.left.data_type)}ax\n"
            arithmetic += f"pushq %rax" \
                          f"\n"
            if not ((self.data_type == 'short') and (self.left.data_type == 'int')) and \
               not ((self.data_type == 'int') and (self.left.data_type == 'short')) and \
                    (self.data_type != self.left.data_type):
                if self.data_type in fractional_types:
                    if self.left.data_type in fractional_types:
                        arithmetic += f"fld{Statement.instruction_data_suffix(self.left.data_type, fpu=True)} " \
                                      f"(%rsp)\n"
                    else:  # elif self.left.data_type in integral_types:
                        arithmetic += f"fildl (%rsp)\n"
                    arithmetic += f"fstp{Statement.instruction_data_suffix(self.data_type, fpu=True)} " \
                                  f"(%rsp)\n"
                elif self.data_type in integral_types:
                    arithmetic += f"fld{Statement.instruction_data_suffix(self.left.data_type, fpu=True)} " \
                                  f"(%rsp)\n" \
                                  f"fistpl (%rsp)\n"
                else:
                    arithmetic += f"\n"

        # generating code for right operand
        if not isinstance(self.right, (Unary, Binary, FunctionCall)):  # const, var or array usage
            if isinstance(self.right, NumericConstant):
                arithmetic += f"mov{Statement.instruction_data_suffix(self.right.data_type)} " \
                              f"{self.right.identifier}(%rip), "
            else:
                arithmetic += f"{self.right.__repr__()}"
            arithmetic += f"%{Statement.register_name_prefix(self.right.data_type)}ax\n"
            arithmetic += f"pushq %rax" \
                          f"\n"
            if not ((self.data_type == 'short') and (self.right.data_type == 'int')) and \
               not ((self.data_type == 'int') and (self.right.data_type == 'short')) and \
                    (self.data_type != self.right.data_type):
                if self.data_type in fractional_types:
                    if self.right.data_type in fractional_types:
                        arithmetic += f"fld{Statement.instruction_data_suffix(self.right.data_type, fpu=True)} " \
                                      f"(%rsp)\n"
                    else:  # elif self.left.data_type in integral_types:
                        arithmetic += f"fildl (%rsp)\n"
                    arithmetic += f"fstp{Statement.instruction_data_suffix(self.data_type, fpu=True)} " \
                                  f"(%rsp)\n"
                elif self.data_type in integral_types:
                    arithmetic += f"fld{Statement.instruction_data_suffix(self.right.data_type, fpu=True)} " \
                                  f"(%rsp)\n" \
                                  f"fistpl (%rsp)\n"
                else:
                    arithmetic += f"\n"
        else:  # unary, binary or function call
            arithmetic += f"{self.right.__repr__()}\n" \
                          f"mov{Statement.instruction_data_suffix(self.right.data_type)} " \
                          f"{self.right.identifier}(%rip), " \
                          f"%{Statement.register_name_prefix(self.right.data_type)}ax\n"
            arithmetic += f"pushq %rax" \
                          f"\n"
            if not ((self.data_type == 'short') and (self.right.data_type == 'int')) and \
               not ((self.data_type == 'int') and (self.right.data_type == 'short')) and \
                    (self.data_type != self.right.data_type):
                if self.data_type in fractional_types:
                    if self.right.data_type in fractional_types:
                        arithmetic += f"fld{Statement.instruction_data_suffix(self.right.data_type, fpu=True)} " \
                                      f"(%rsp)\n"
                    else:  # elif self.left.data_type in integral_types:
                        arithmetic += f"fildl (%rsp)\n"
                    arithmetic += f"fstp{Statement.instruction_data_suffix(self.data_type, fpu=True)} " \
                                  f"(%rsp)\n"
                elif self.data_type in integral_types:
                    arithmetic += f"fld{Statement.instruction_data_suffix(self.right.data_type, fpu=True)} " \
                                  f"(%rsp)\n" \
                                  f"fistpl (%rsp)\n"
                else:
                    arithmetic += f"\n"

        arithmetic += f"\npopq %rcx\npopq %rax\n" \
                      f"\n"

        if self.data_type in fractional_types:
            arithmetic += f"pushq %rcx\n" \
                          f"fld{Statement.instruction_data_suffix(self.data_type, fpu=True)} (%rsp)\n" \
                          f"popq %rcx\npushq %rax\n" \
                          f"fld{Statement.instruction_data_suffix(self.data_type, fpu=True)} (%rsp)\n" \
                          f"\n" \
                          f"fdivp\n" \
                          f"\n" \
                          f"fstp{Statement.instruction_data_suffix(self.data_type, fpu=True)} (%rsp)\n" \
                          f"popq %rax\n" \
                          f"\n"
        else:  # elif self.data_type in integral_types:
            if self.data_type == 'short':
                arithmetic += f"cwd\n"
            else:  # elif self.data_type == 'int':
                arithmetic += f"cdq\n"
            arithmetic += f"idiv{Statement.instruction_data_suffix(self.data_type)} " \
                          f"%{Statement.register_name_prefix(self.data_type)}cx\n" \
                          f"\n"

        return arithmetic + f"mov{Statement.instruction_data_suffix(self.data_type)} " \
                            f"%{Statement.register_name_prefix(self.data_type)}ax, " \
                            f"{self.identifier}(%rip)\n" \
                            f"\nxor %rcx, %rcx\nxor %rax, %rax\n"


Binary.operation = {
    '+': Add,
    '-': Sub,
    '*': Mul,
    '/': Div
}


class AssignmentStatement(Statement):

    def __init__(self, destination: VariableUsage or ArrayUsage, value: Expression, position, p):
        super().__init__(position)

        self.value = value
        self.destination = destination

        data_types_priority = integral_types + fractional_types
        if data_types_priority.index(destination.data_type) < data_types_priority.index(value.data_type):
            print(
                NEWLINE +
                colorize('yellow', f"warning: type conversion may result in loss of data or precision! "
                                   f"({self.value.data_type} assigned to {self.destination.data_type}), here:\n"
                                   f"{p.lexer.lexdata.split(NEWLINE)[p.lineno(2) - 1]}\n"
                                   f"{' ' * (p.lexpos(2) - p.lexer.lexdata.rfind(NEWLINE, 0, p.lexpos(2)) - 1) + '^'}"
                         )
                + NEWLINE +
                colorize('violet', f"hint: in assignment statement, at "
                                   f"{position[0]}:{position[1] - p.lexer.lexdata.rfind(NEWLINE, 0, position[1])}")
            )

    def __repr__(self):

        destination, conversion, value = "", None, ''

        if type(self.value) in (VariableUsage, ArrayUsage):
            value += self.value.__repr__()+f"%{self.register_name_prefix(self.value.data_type)}ax\n"
        elif isinstance(self.value, NumericConstant):
            value += f"mov{self.instruction_data_suffix(self.value.data_type)} " \
                     f"{self.value.identifier}(%rip), %{self.register_name_prefix(self.value.data_type)}ax\n"
        else:  # elif isinstance(self.value, (Unary, Binary, FunctionCall))
            value += f"{self.value.__repr__()}\n" \
                     f"mov{self.instruction_data_suffix(self.value.data_type)} " \
                     f"{self.value.identifier}(%rip), %{self.register_name_prefix(self.value.data_type)}ax\n"

        conversion = NEWLINE
        if not ((self.destination.data_type == 'short') and (self.value.data_type == 'int')) and \
           not ((self.destination.data_type == 'int') and (self.value.data_type == 'short')) and \
           (self.destination.data_type != self.value.data_type):

            conversion += f"pushq %rax\n"
            if self.destination.data_type in fractional_types:
                if self.value.data_type in fractional_types:
                    conversion += f"fld{self.instruction_data_suffix(self.value.data_type, fpu=True)} (%rsp)\n"
                else:  # elif self.value.data_type in integral_types:
                    conversion += f"fildl (%rsp)\n"
                conversion += f"fstp{self.instruction_data_suffix(self.destination.data_type, fpu=True)} (%rsp)\n"
            else:  # elif self.destination.data_type in integral_types:
                conversion += f"fld{self.instruction_data_suffix(self.value.data_type, fpu=True)} (%rsp)\n" \
                              f"fistpl (%rsp)\n"
            conversion += f"\n"
        else:
            conversion += f"pushq %rax\n" \
                          f"\n"

        if type(self.destination) == VariableUsage:
            destination += f"popq %rax\n" \
                           f"\n" \
                           f"mov{self.instruction_data_suffix(self.destination.data_type)} " \
                           f"%{self.register_name_prefix(self.destination.data_type)}ax, " \
                           f"{self.destination.identifier}(%rip)\n" \
                           f"\n" \
                           f"xor %rax, %rax" \
                           f"\n"
        else:  # elif type(self.destination) == ArrayUsage
            if type(self.destination.index) == ArrayUsage:
                destination += f"{self.destination.index.__repr__()}" \
                               f"%{self.register_name_prefix(self.destination.index.data_type)}di\n" \
                               f"\n" \
                               f"leaq {self.destination.identifier}(%rip), %rsi\n"
            elif not isinstance(self.destination.index, (Unary, Binary, FunctionCall)):
                destination += f"leaq {self.destination.identifier}(%rip), %rsi\n" \
                               f"xor %rdi, %rdi\n" \
                               f"mov{self.instruction_data_suffix(self.destination.index.data_type)} " \
                               f"{self.destination.index.identifier}(%rip), " \
                               f"%{self.register_name_prefix(self.destination.index.data_type)}di\n"
            else:  # isinstance(self.index, (Unary, Binary, FunctionCall)):
                destination += f"{self.destination.index.__repr__()}" \
                               f"\n" \
                               f"leaq {self.destination.identifier}(%rip), %rsi\n" \
                               f"mov{self.instruction_data_suffix(self.destination.index.data_type)} " \
                               f"{self.destination.index.identifier}(%rip), " \
                               f"%rdi" \
                               f"\n"
            destination += f"popq %rax\n" \
                           f"\n" \
                           f"mov{self.instruction_data_suffix(self.destination.data_type)} " \
                           f"%{self.register_name_prefix(self.destination.data_type)}ax, " \
                           f"(%rsi, %rdi, {self.data_type_size(self.destination.data_type)})\n" \
                           f"\n" \
                           f"xor %rax, %rax" \
                           f"\n"

        return value + conversion + destination

    def __str__(self):
        return f"{self.__class__.__name__} -> " \
               f"{{destination={self.destination}, value={self.value}}}"


@dataclass
class SymbolsTable:
    """ ~ symbols table ~ """

    numeric_constant_id: int = -1
    temporary_variable_id: int = -1

    declarations: [Declaration] = \
        field(default_factory=list)
    temporary_variables: [VariableDeclaration] = \
        field(default_factory=list)
    numeric_constants: [NumericConstant] = \
        field(default_factory=list)

    def add_declaration(self, symbol: Declaration) -> None:
        declaration = self.get_declaration(symbol)
        if declaration:
            raise LookupError(symbol, "already defined!", declaration, symbol)
        else:
            self.declarations.append(symbol)

    def get_declaration(self, symbol: Declaration or str) -> Declaration or None:
        return next(filter(lambda d: d == symbol, self.declarations), None)

    def has_declaration(self, symbol: str, node_kind: type):
        declaration = self.get_declaration(symbol)
        return declaration if type(declaration) == node_kind else None

    def add_temporary_variable(self, data_type: str):
        self.temporary_variable_id += 1
        temp_var = VariableDeclaration(f"_tv{self.temporary_variable_id}", None, data_type)
        self.temporary_variables.append(temp_var)
        return temp_var

    def add_numeric_constant(self, symbol: NumericConstant) -> NumericConstant or None:
        numeric_constant = self.get_numeric_constant(symbol)
        if not self.get_numeric_constant(symbol):
            self.numeric_constant_id += 1
            symbol.identifier += str(self.numeric_constant_id)
            self.numeric_constants.append(symbol)
            return self.numeric_constants[-1]
        else:
            return numeric_constant

    def get_numeric_constant(self, symbol: NumericConstant) -> NumericConstant or None:
        return next(filter(lambda nc: nc == symbol, self.numeric_constants), None)

    def __str__(self):
        return f"{self.__class__.__name__} -> " \
               f"{{" \
               f"\n{NEWLINE.join(declaration.__str__() for declaration in self.declarations)}\n" \
               f"\n{NEWLINE.join(numeric_constant.__str__() for numeric_constant in self.numeric_constants)}\n" \
               f"}}"


class ProgramStatements:

    def __init__(self, statements: [Statement], symbols_table: SymbolsTable):
        self.statements = statements

        self.symbols_table = symbols_table

    def __repr__(self):
        return f"\n.bss // declared variables\n" \
               f"\n{NEWLINE.join(statement.__repr__() for statement in self.symbols_table.declarations)}\n" \
               f"\n.data // constants\n" \
               f"\n{NEWLINE.join(statement.__repr__() for statement in self.symbols_table.numeric_constants)}\n" \
               f"\n.text // assembly instructions\n" \
               f"\n.globl _example\n" \
               f"\n_example:\n" \
               f"\nxor %rax, %rax\n" \
               f"\n{NEWLINE.join(statement.__repr__() for statement in self.statements)}\n" \
               f"\nxor %rax, %rax /* exit code 0, no runtime errors */\n" \
               f"\nretq\n" \
               f"\n// temporary variables" \
               f"\n{NEWLINE.join(statement.__repr__() for statement in self.symbols_table.temporary_variables)}\n" \
               f"\n.end" \
               f"\n"
