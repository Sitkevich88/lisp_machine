"""
Типы данных для представления и сериализации/десериализации машинного кода.
"""

import json
from collections import namedtuple
from enum import Enum


functions = ['setq', 'read', 'print', 'loop', 'if', 'return', '+', '-', '>', '<', '=', 'mod']


class Opcode(str, Enum):
    """Opcode для ISA."""
    LOAD = 'load'
    LOAD_CONST = 'loadc'
    LOAD_INDIRECT = 'load_indir'
    STORE = 'store'
    STORE_INDIRECT = 'store_indir'
    ADD = 'add'
    ADD_CONST = 'addc'
    SUB = 'sub'
    PRINT = 'print'
    PRINT_INT = 'print_int'
    READ = 'read'
    JMP = 'jmp'
    JE = 'je'
    JNE = 'jne'
    JG = 'jg'
    JL = 'jl'
    HLT = 'halt'


class Term(namedtuple('Term', 'pos')):
    """Описание выражения из исходного текста программы."""
    # сделано через класс, чтобы был docstring


def write_code(filename, code):
    """Записать машинный код в файл."""
    with open(filename, "w", encoding="utf-8") as file:
        file.write(json.dumps(code, indent=4))


def read_code(filename):
    """Прочесть машинный код из файла."""
    with open(filename, encoding="utf-8") as file:
        code = json.loads(file.read())

    for instr in code:
        # Конвертация строки в Opcode
        instr['opcode'] = Opcode(instr['opcode'])
        instr['term'] = Term(instr['term'])

    return code
