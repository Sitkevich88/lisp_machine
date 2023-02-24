from enum import Enum
from isa import Opcode
from translation.evaluation_utils import *


class LispVarType(Enum):
    STRING = 3
    BOOLEAN = 2
    INTEGER = 1
    UNDEF = 0


addr = 0
instruction_counter = -1

read_address = 0
read_counter = 0
max_input_size = 0

lisp_vars_addresses = {}
strings_addresses = {}


def get_instruction(name, arg):
    global instruction_counter

    instruction_counter += 1
    return {"opcode": name, "arg": arg, "term": instruction_counter}


def is_lisp_string(lisp_arg):
    return isinstance(lisp_arg, str) and lisp_arg[0] == '\"' and lisp_arg[-1] == '\"'


def is_lisp_var(lisp_arg):
    return isinstance(lisp_arg, str) and lisp_arg[0] != '\"' and lisp_arg[-1] != '\"'


def lisp_loop(expression: SymbolicExpression):
    global addr
    global instruction_counter
    machine_code = []

    loop_start_term = instruction_counter + 1
    machine_code += iterate_over_expressions(expression.args)
    machine_code.append(get_instruction(Opcode.JMP, loop_start_term))
    loop_end_term = instruction_counter + 1

    for code in machine_code:
        if code["arg"] == 'go to loop end':
            code["arg"] = loop_end_term

    return machine_code


def lisp_return(expression: SymbolicExpression):
    global addr
    machine_code = []

    if len(expression.args) > 0:
        if isinstance(expression.args[0], SymbolicExpression):
            machine_code += convert_expression_to_instructions(expression.args[0])
        else:
            machine_code += push_lisp_val(expression.args[0])

    machine_code.append(get_instruction(Opcode.JMP, 'go to loop end'))

    return machine_code


def lisp_if(expression: SymbolicExpression):
    assert len(expression.args) <= 3, "Incorrect lisp 'if' syntax"
    global addr
    machine_code = []

    if isinstance(expression.args[0], SymbolicExpression):
        machine_code += convert_expression_to_instructions(expression.args[0])
    else:
        machine_code += push_lisp_val(expression.args[0])

    #  if
    machine_code.append(get_instruction(Opcode.LOAD, addr - 2))
    machine_code.append(get_instruction(Opcode.ADD_CONST, - LispVarType.BOOLEAN.value))
    machine_code.append(get_instruction(Opcode.JNE, "go to true"))  # if not boolean jump to true
    machine_code.append(get_instruction(Opcode.LOAD, addr - 1))
    machine_code.append(get_instruction(Opcode.JE, "go to false"))  # if false go to false
    addr -= 2
    true_term = machine_code[-1]["term"] + 1

    #  true
    if isinstance(expression.args[1], SymbolicExpression):
        machine_code += convert_expression_to_instructions(expression.args[1])
    else:
        machine_code += push_lisp_val(expression.args[1])

    # add jump addresses
    machine_code.append(get_instruction(Opcode.JMP, "go to end"))
    false_term = machine_code[-1]["term"] + 1
    for code in machine_code:
        if code["arg"] == "go to true":
            code["arg"] = true_term
        elif code["arg"] == "go to false":
            code["arg"] = false_term

    #  false
    if len(expression.args) == 3:
        if isinstance(expression.args[2], SymbolicExpression):
            machine_code += convert_expression_to_instructions(expression.args[2])
        else:
            machine_code += push_lisp_val(expression.args[2])

    # add jump address
    end_term = machine_code[-1]["term"] + 1
    for code in machine_code:
        if code["arg"] == "go to end":
            code["arg"] = end_term

    return machine_code


def lisp_mod(expression: SymbolicExpression):
    global addr
    machine_code = []

    #  сохраним два аргумента в temp
    machine_code += store_args(expression.args)

    machine_code.append(get_instruction(Opcode.LOAD, addr - 3))
    machine_code.append(get_instruction(Opcode.STORE, addr))

    #  loop
    loop_start = machine_code[-1]["term"] + 1
    machine_code.append(get_instruction(Opcode.SUB, addr - 1))
    machine_code.append(get_instruction(Opcode.JL, loop_start + 4))  # go to save result
    machine_code.append(get_instruction(Opcode.STORE, addr))
    machine_code.append(get_instruction(Opcode.JMP, loop_start))

    #  save result
    machine_code.append(get_instruction(Opcode.LOAD_CONST, LispVarType.INTEGER.value))
    machine_code.append(get_instruction(Opcode.STORE, addr - 4))
    machine_code.append(get_instruction(Opcode.LOAD, addr))
    machine_code.append(get_instruction(Opcode.STORE, addr - 3))

    addr -= 2

    return machine_code


def lisp_greater_than(expression: SymbolicExpression, is_greater: bool):
    global addr
    machine_code = []

    if not is_greater:  # is lower
        expression.args[0], expression.args[1] = expression.args[1], expression.args[0]

    # сохраним два аргумента в temp
    machine_code += store_args(expression.args)
    calculations_term = machine_code[-1]["term"] + 1

    # calculations
    machine_code.append(get_instruction(Opcode.LOAD, addr - 3))
    machine_code.append(get_instruction(Opcode.SUB, addr - 1))
    machine_code.append(get_instruction(Opcode.JG, calculations_term + 5))

    # false
    machine_code.append(get_instruction(Opcode.LOAD_CONST, 0))
    machine_code.append(get_instruction(Opcode.JMP, calculations_term + 6))

    # true
    machine_code.append(get_instruction(Opcode.LOAD_CONST, 1))

    machine_code.append(get_instruction(Opcode.STORE, addr - 3))
    machine_code.append(get_instruction(Opcode.LOAD_CONST, LispVarType.BOOLEAN.value))
    machine_code.append(get_instruction(Opcode.STORE, addr - 4))

    addr -= 2

    return machine_code


def lisp_minus(expression: SymbolicExpression):
    global addr
    machine_code = []

    #  считаем результат сразу, если оба аргумента числа
    if isinstance(expression.args[0], int) and isinstance(expression.args[1], int):
        machine_code += store_const(LispVarType.INTEGER.value)
        machine_code += store_const(expression.args[0] - expression.args[1])
        return machine_code

    #  сохраним два аргумента в temp
    machine_code += store_args(expression.args)

    #  сам plus
    machine_code.append(get_instruction(Opcode.LOAD, addr - 3))
    machine_code.append(get_instruction(Opcode.SUB, addr - 1))
    machine_code.append(get_instruction(Opcode.STORE, addr - 3))
    machine_code.append(get_instruction(Opcode.LOAD_CONST, LispVarType.INTEGER.value))
    machine_code.append(get_instruction(Opcode.STORE, addr - 4))

    addr -= 2

    return machine_code


def lisp_plus(expression: SymbolicExpression):
    global addr
    global lisp_vars_addresses
    machine_code = []

    #  считаем результат сразу, если оба аргумента числа
    if isinstance(expression.args[0], int) and isinstance(expression.args[1], int):
        machine_code += store_const(LispVarType.INTEGER.value)
        machine_code += store_const(expression.args[0] + expression.args[1])
        return machine_code

    #  сохраним два аргумента в temp
    machine_code += store_args(expression.args)

    #  сам plus
    machine_code.append(get_instruction(Opcode.LOAD, addr - 3))
    machine_code.append(get_instruction(Opcode.ADD, addr - 1))
    machine_code.append(get_instruction(Opcode.STORE, addr - 3))
    machine_code.append(get_instruction(Opcode.LOAD_CONST, LispVarType.INTEGER.value))
    machine_code.append(get_instruction(Opcode.STORE, addr - 4))

    addr -= 2

    return machine_code


def lisp_equal(expression: SymbolicExpression):
    global addr
    global lisp_vars_addresses
    machine_code = []

    #  считаем результат сразу, если оба аргумента числа
    if isinstance(expression.args[0], int) and isinstance(expression.args[1], int):
        machine_code += store_const(LispVarType.BOOLEAN.value)
        machine_code += store_const(1 if expression.args[0] == expression.args[1] else 0)
        return machine_code

    #  сохраним два аргумента в temp
    machine_code += store_args(expression.args)

    #  сам equal
    machine_code.append(get_instruction(Opcode.LOAD, addr - 3))
    machine_code.append(get_instruction(Opcode.SUB, addr - 1))
    sub_instruction_term = machine_code[-1]["term"]

    machine_code.append(get_instruction(Opcode.JE, sub_instruction_term + 4))  # объекты равны, загружаем единицу
    machine_code.append(get_instruction(Opcode.LOAD_CONST, 0))
    machine_code.append(get_instruction(Opcode.JMP, sub_instruction_term + 5))
    machine_code.append(get_instruction(Opcode.LOAD_CONST, 1))

    machine_code.append(get_instruction(Opcode.STORE, addr - 3))
    machine_code.append(get_instruction(Opcode.LOAD_CONST, LispVarType.BOOLEAN.value))
    machine_code.append(get_instruction(Opcode.STORE, addr - 4))

    addr -= 2

    return machine_code


def lisp_setq(expression: SymbolicExpression):
    global addr
    global lisp_vars_addresses
    machine_code = []
    var_name = expression.args[0]
    assert is_lisp_var(var_name), f'{var_name} is an incorrect lisp var name'

    if isinstance(expression.args[1], SymbolicExpression):
        machine_code += convert_expression_to_instructions(expression.args[1])
    else:
        machine_code += push_lisp_val(expression.args[1])

    var_addr = lisp_vars_addresses[var_name]

    addr -= 2
    machine_code.append(get_instruction(Opcode.LOAD, addr))
    machine_code.append(get_instruction(Opcode.STORE, var_addr))
    machine_code.append(get_instruction(Opcode.LOAD, addr + 1))
    machine_code.append(get_instruction(Opcode.STORE, var_addr + 1))

    addr += 2

    return machine_code


def lisp_print(expression: SymbolicExpression):
    global addr
    global instruction_counter
    machine_code = []

    if isinstance(expression.args[0], SymbolicExpression):
        machine_code += convert_expression_to_instructions(expression.args[0])
    else:
        machine_code += push_lisp_val(expression.args[0])

    lisp_var_addr = addr
    lisp_var_type_addr = addr - 2

    # копирование значения переменной
    machine_code.append(get_instruction(Opcode.LOAD, lisp_var_addr - 1))
    machine_code.append(get_instruction(Opcode.STORE, lisp_var_addr))
    machine_code.append(get_instruction(Opcode.LOAD, lisp_var_type_addr))

    # определение типа переменной
    machine_code.append(get_instruction(Opcode.JE, 'false'))  # jump на print false
    machine_code.append(get_instruction(Opcode.ADD_CONST, -1))
    machine_code.append(get_instruction(Opcode.JE, 'integer'))  # jump на print integer
    machine_code.append(get_instruction(Opcode.ADD_CONST, -1))
    machine_code.append(get_instruction(Opcode.JE, 'boolean'))  # jump на print boolean

    # print string
    string_term = machine_code[-1]["term"] + 1
    machine_code.append(get_instruction(Opcode.LOAD_MEM, lisp_var_addr))
    machine_code.append(get_instruction(Opcode.PRINT, ""))
    machine_code.append(get_instruction(Opcode.JE, 'end'))  # jump на end
    machine_code.append(get_instruction(Opcode.LOAD, lisp_var_addr))
    machine_code.append(get_instruction(Opcode.ADD_CONST, 1))
    machine_code.append(get_instruction(Opcode.STORE, lisp_var_addr))
    machine_code.append(get_instruction(Opcode.JMP, string_term))  # jump в print string

    # print boolean
    boolean_term = machine_code[-1]['term'] + 1
    machine_code.append(get_instruction(Opcode.LOAD, lisp_var_addr))
    machine_code.append(get_instruction(Opcode.JNE, 'true'))  # jump на print true
    # print false
    false_term = machine_code[-1]['term'] + 1
    machine_code.append(get_instruction(Opcode.LOAD_CONST, ord('N')))
    machine_code.append(get_instruction(Opcode.PRINT, ""))
    machine_code.append(get_instruction(Opcode.LOAD_CONST, ord('I')))
    machine_code.append(get_instruction(Opcode.PRINT, ""))
    machine_code.append(get_instruction(Opcode.LOAD_CONST, ord('L')))
    machine_code.append(get_instruction(Opcode.PRINT, ""))
    machine_code.append(get_instruction(Opcode.JMP, 'end'))  # jump в конец принта
    # print true
    true_term = machine_code[-1]['term'] + 1
    machine_code.append(get_instruction(Opcode.LOAD_CONST, ord('t')))
    machine_code.append(get_instruction(Opcode.PRINT, ""))
    machine_code.append(get_instruction(Opcode.JMP, 'end'))  # jump в конец принта

    # print integer
    integer_term = machine_code[-1]['term'] + 1
    machine_code.append(get_instruction(Opcode.LOAD, lisp_var_addr))
    machine_code.append(get_instruction(Opcode.PRINT_INT, ""))
    end_term = machine_code[-1]['term'] + 1

    for inst in machine_code:
        if inst['arg'] == 'boolean':
            inst['arg'] = boolean_term
        elif inst['arg'] == 'false':
            inst['arg'] = false_term
        elif inst['arg'] == 'true':
            inst['arg'] = true_term
        elif inst['arg'] == 'end':
            inst['arg'] = end_term
        elif inst['arg'] == 'integer':
            inst['arg'] = integer_term

    return machine_code


def lisp_read():
    global addr
    global read_address
    global read_counter
    global max_input_size
    machine_code = []

    input_addr = read_address + read_counter * max_input_size
    machine_code += store_const(input_addr)
    addr -= 1

    machine_code.append(get_instruction(Opcode.READ, ""))  # прочитали символ в акк
    read_command_address = machine_code[-1]["term"]

    machine_code.append(get_instruction(Opcode.STORE_MEM, addr))  # сохранили символ
    machine_code.append(get_instruction(Opcode.JE, read_command_address + 7))  # перескок на сохранение переменной
    machine_code.append(get_instruction(Opcode.LOAD, addr))
    machine_code.append(get_instruction(Opcode.ADD_CONST, 1))  # инкремент адреса ячейки для следующего символа
    machine_code.append(get_instruction(Opcode.STORE, addr))
    machine_code.append(get_instruction(Opcode.JMP, read_command_address))

    machine_code += store_const(LispVarType.STRING.value)  # сохранение переменной
    machine_code += store_const(input_addr)

    read_counter += 1

    return machine_code


def push_lisp_val(lisp_val):
    global strings_addresses
    global lisp_vars_addresses
    global addr
    machine_code = []

    if is_lisp_string(lisp_val):
        machine_code += store_const(LispVarType.STRING.value)
        machine_code += store_const(strings_addresses[convert_lisp_string_to_string(lisp_val)])
    elif is_lisp_var(lisp_val):
        var_addr = lisp_vars_addresses[lisp_val]

        machine_code.append(get_instruction(Opcode.LOAD, var_addr))
        machine_code.append(get_instruction(Opcode.STORE, addr))
        addr += 1
        machine_code.append(get_instruction(Opcode.LOAD, var_addr + 1))
        machine_code.append(get_instruction(Opcode.STORE, addr))
        addr += 1
    elif isinstance(lisp_val, bool):
        machine_code += store_const(LispVarType.BOOLEAN.value)
        machine_code += store_const(1 if lisp_val else 0)
    elif isinstance(lisp_val, int):
        machine_code += store_const(LispVarType.INTEGER.value)
        machine_code += store_const(lisp_val)
    else:
        # undefined
        machine_code += store_const(LispVarType.UNDEF.value)
        machine_code += store_const(0)

    return machine_code


def convert_expression_to_instructions(expression: SymbolicExpression):
    global addr
    machine_code = []

    if expression.operator == 'read':
        machine_code += lisp_read()
    elif expression.operator == 'print':
        machine_code += lisp_print(expression)
    elif expression.operator == 'setq':
        machine_code += lisp_setq(expression)
    elif expression.operator == '=':
        machine_code += lisp_equal(expression)
    elif expression.operator == '+':
        machine_code += lisp_plus(expression)
    elif expression.operator == '-':
        machine_code += lisp_minus(expression)
    elif expression.operator == '>':
        machine_code += lisp_greater_than(expression, True)
    elif expression.operator == '<':
        machine_code += lisp_greater_than(expression, False)
    elif expression.operator == 'mod':
        machine_code += lisp_mod(expression)
    elif expression.operator == 'if':
        machine_code += lisp_if(expression)
    elif expression.operator == 'loop':
        machine_code += lisp_loop(expression)
    elif expression.operator == 'return':
        machine_code += lisp_return(expression)
    else:
        raise RuntimeError(f'"{expression.operator}" operator is not supported by evaluator')

    return machine_code


def store_const(const_val):
    global addr
    machine_code = [
        get_instruction(Opcode.LOAD_CONST, const_val),
        get_instruction(Opcode.STORE, addr)
    ]
    addr += 1

    return machine_code


def store_args(args):
    machine_code = []

    for i in range(2):
        if isinstance(args[i], SymbolicExpression):
            machine_code += convert_expression_to_instructions(args[i])
        else:
            machine_code += push_lisp_val(args[i])

    return machine_code


def load_const_strings(const_strings):
    global addr
    global strings_addresses
    machine_code = []

    for const_string in const_strings:
        strings_addresses[const_string] = addr

        for i in range(len(const_string)):
            machine_code += store_const(
                ord(const_string[i])
            )
        machine_code += store_const(0)

    return machine_code


def add_buffers(read_amount):
    global max_input_size
    global addr
    global read_address

    max_input_size = 100
    read_address = addr

    addr += max_input_size * read_amount


def add_variables(lisp_variables):
    global lisp_vars_addresses
    global addr
    machine_code = []

    for lisp_var in lisp_variables:
        lisp_vars_addresses[lisp_var] = addr
        # store type later
        # machine_code += store_const(LispVarType.UNDEF.value)
        addr += 1  # если вернешь верхнюю строку, то удали это
        # store value later
        addr += 1

    return machine_code


def iterate_over_expressions(s_expressions):
    global addr
    temp_region_addr = addr
    machine_code = []

    for exp in s_expressions:
        machine_code += convert_expression_to_instructions(exp)
        addr = temp_region_addr

    return machine_code


def evaluate(s_expressions):
    global strings_addresses
    global lisp_vars_addresses
    global addr

    print()

    machine_code = []
    const_strings = get_all_string_values_from_s_expressions(s_expressions)
    read_amount = count_read_operations_in_many_expressions(s_expressions)
    lisp_variables = get_variables(s_expressions)

    machine_code += load_const_strings(const_strings)
    add_buffers(read_amount)
    machine_code += add_variables(lisp_variables)
    print('vars adds:', lisp_vars_addresses)
    print('string adds:', strings_addresses)
    print()

    machine_code += iterate_over_expressions(s_expressions)
    machine_code.append(get_instruction(Opcode.HLT, ''))

    return machine_code
