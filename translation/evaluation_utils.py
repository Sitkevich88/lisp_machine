from translation.common import SymbolicExpression


def convert_lisp_string_to_string(lisp_string):
    return lisp_string.replace('\"', '')


def get_all_string_values_from_s_expressions(s_expressions):
    const_strings = []

    for expression in s_expressions:
        const_strings += get_string_values_from_s_expression(expression)

    return sorted(set(const_strings))


def get_string_values_from_s_expression(s_expression: SymbolicExpression):
    const_strings = []
    stringy_functions = ['setq', 'print', 'if', 'return']

    if s_expression.operator in stringy_functions:
        for arg in s_expression.args:
            if isinstance(arg, SymbolicExpression):
                const_strings += get_string_values_from_s_expression(arg)
            elif isinstance(arg, str) and arg[0] == '\"' and arg[-1] == '\"':
                const_strings.append(convert_lisp_string_to_string(arg))

    return const_strings


def count_read_operations_in_many_expressions(s_expressions):
    res = 0
    for expression in s_expressions:
        res += count_read_operations_in_one_expression(expression)

    return res


def count_read_operations_in_one_expression(s_expression):
    res = 0

    if s_expression.operator == 'read':
        res = 1
    else:
        for arg in s_expression.args:
            if isinstance(arg, SymbolicExpression):
                res += count_read_operations_in_one_expression(arg)

    return res


def get_variables(s_expressions):
    variables = []

    for expression in s_expressions:
        variables += get_variable(expression)

    return sorted(set(variables))


def get_variable(s_expression):
    variables = []

    if s_expression.operator == 'setq':
        assert isinstance(s_expression.args[0], str), 'Incorrect lisp syntax in setq'
        variables.append(s_expression.args[0])
    else:
        for arg in s_expression.args:
            if isinstance(arg, SymbolicExpression):
                variables += get_variable(arg)

    return variables
