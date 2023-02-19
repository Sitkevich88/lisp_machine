from enum import Enum
from isa import Opcode
from translation.evaluation_utils import *


class LispVarType(Enum):
    STRING = 3
    BOOLEAN = 2
    INTEGER = 1
    UNDEF = 0


addr = 0
instruction_counter = 0

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


#def lisp_equal(expression):
#    assert len(expression.args) == 2, 'У "=" должно быть ровно 2 аргумента'
#    machine_code = []
#
#    if isinstance(expression.args[0], int) and isinstance(expression.args[1], int):
#        pass


def lisp_setq(var_name):
    assert is_lisp_var(var_name), f'{var_name} is not correct lisp var name'

    global addr
    global lisp_vars_addresses
    machine_code = []
    var_addr = lisp_vars_addresses[var_name]

    addr -= 2
    machine_code.append(get_instruction(Opcode.LOAD, addr))
    machine_code.append(get_instruction(Opcode.STORE, var_addr))
    machine_code.append(get_instruction(Opcode.LOAD, addr + 1))
    machine_code.append(get_instruction(Opcode.STORE, var_addr + 1))

    addr += 2

    return machine_code


def lisp_print():
    global addr
    global instruction_counter
    machine_code = []

    lisp_var_addr = addr
    lisp_var_type_addr = addr - 2

    # копирование значения переменной
    machine_code.append(get_instruction(Opcode.LOAD, lisp_var_addr - 1))
    machine_code.append(get_instruction(Opcode.STORE, lisp_var_addr))
    machine_code.append(get_instruction(Opcode.LOAD, lisp_var_type_addr))

    first_jump_addr = machine_code[-1]["term"] + 1

    # определение типа переменной
    machine_code.append(get_instruction(Opcode.JE, first_jump_addr + 11))  # jump на print false
    machine_code.append(get_instruction(Opcode.ADD_CONST, -1))
    machine_code.append(get_instruction(Opcode.JE, first_jump_addr + 21))  # jump на print integer
    machine_code.append(get_instruction(Opcode.ADD_CONST, -1))
    machine_code.append(get_instruction(Opcode.JE, first_jump_addr + 9))  # jump на print boolean

    # print string
    machine_code.append(get_instruction(Opcode.LOAD_MEM, lisp_var_addr))
    load_instruction_addr = machine_code[-1]["term"]

    machine_code.append(get_instruction(Opcode.PRINT, ""))
    machine_code.append(get_instruction(Opcode.JNE, load_instruction_addr))
    machine_code.append(get_instruction(Opcode.JMP, first_jump_addr + 23))  # jump в конец принта

    # print boolean
    machine_code.append(get_instruction(Opcode.LOAD, lisp_var_addr))
    machine_code.append(get_instruction(Opcode.JNE, first_jump_addr + 18))  # jump на print true
    # print false
    machine_code.append(get_instruction(Opcode.LOAD_CONST, ord('N')))
    machine_code.append(get_instruction(Opcode.PRINT, ""))
    machine_code.append(get_instruction(Opcode.LOAD_CONST, ord('I')))
    machine_code.append(get_instruction(Opcode.PRINT, ""))
    machine_code.append(get_instruction(Opcode.LOAD_CONST, ord('L')))
    machine_code.append(get_instruction(Opcode.PRINT, ""))
    machine_code.append(get_instruction(Opcode.JMP, first_jump_addr + 23))  # jump в конец принта
    # print true
    machine_code.append(get_instruction(Opcode.LOAD_CONST, ord('t')))
    machine_code.append(get_instruction(Opcode.PRINT, ""))
    machine_code.append(get_instruction(Opcode.JMP, first_jump_addr + 23))  # jump в конец принта

    # print integer
    machine_code.append(get_instruction(Opcode.LOAD, lisp_var_addr))
    machine_code.append(get_instruction(Opcode.PRINT_INT, ""))

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
    elif isinstance(lisp_val, int):
        machine_code += store_const(LispVarType.INTEGER.value)
        machine_code += store_const(lisp_val)
    elif isinstance(lisp_val, bool):
        machine_code += store_const(LispVarType.BOOLEAN.value)
        machine_code += store_const(1 if lisp_val else 0)
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
        if isinstance(expression.args[0], SymbolicExpression):
            machine_code += convert_expression_to_instructions(expression.args[0])
        else:
            machine_code += push_lisp_val(expression.args[0])
        machine_code += lisp_print()
    elif expression.operator == 'setq':
        if isinstance(expression.args[1], SymbolicExpression):
            machine_code += convert_expression_to_instructions(expression.args[1])
        else:
            machine_code += push_lisp_val(expression.args[1])
        machine_code += lisp_setq(expression.args[0])

    return machine_code


def store_const(const_val):
    global addr
    machine_code = [
        get_instruction(
            Opcode.LOAD_CONST,
            const_val
        ),
        get_instruction(
            Opcode.STORE,
            addr
        )
    ]
    addr += 1

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
    temp_region_addr = addr
    print('vars adds:', lisp_vars_addresses)
    print('string adds:', strings_addresses)
    print()

    for exp in s_expressions:
        machine_code += convert_expression_to_instructions(exp)
        addr = temp_region_addr

    machine_code.append(get_instruction(Opcode.HLT, ''))

    return machine_code
