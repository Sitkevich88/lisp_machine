#!/usr/bin/python3
# pylint: disable=missing-function-docstring  # чтобы не быть Капитаном Очевидностью
# pylint: disable=invalid-name                # сохраним традиционные наименования сигналов
# pylint: disable=consider-using-f-string     # избыточный синтаксис


from isa import *
from translation.reader import read
from translation.evaluator import evaluate
import sys


def translate(code):
    s_expressions = read(code)
    machine_code = evaluate(s_expressions)

    return machine_code


def main(args):
    assert len(args) == 2, \
        "Wrong arguments: translation.py <input_file> <target_file>"
    source, target = args

    with open(source, "rt", encoding="utf-8") as file:
        source = file.read()

    code = translate(source)
    print("source LoC:", len(source.split()), ", code instr:", len(code))
    write_code(target, code)


if __name__ == '__main__':
    main(sys.argv[1:])
