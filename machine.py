#!/usr/bin/python3
# pylint: disable=missing-function-docstring  # чтобы не быть Капитаном Очевидностью
# pylint: disable=invalid-name                # сохраним традиционные наименования сигналов
# pylint: disable=consider-using-f-string     # избыточный синтаксис

import logging
import sys
from isa import Opcode, read_code

    
class DataPath:
    def __init__(self, data_memory_size: int, input_buffer: list):
        assert data_memory_size > 0, "Data_memory size should be non-zero"
        self.data_memory_size = data_memory_size
        self.data_memory = [0] * data_memory_size
        self.da = 0  # data address
        self.acc = 0  # accumulator
        self.dr = 0  # data register
        self.sr = 0  # storage register (stores instruction's argument)
        self.input_buffer = input_buffer
        self.output_buffer = []
        self.flags = {"zero": 1, "sign": 0}

    def latch_sr(self, arg: int):
        self.sr = arg

    def latch_dr(self, sel_memory: bool):
        if sel_memory:
            self.dr = self.data_memory[self.da]
        else:
            self.dr = self.sr

    def latch_acc(self, sel: Opcode):
        assert sel in [Opcode.READ, Opcode.LOAD, Opcode.LOAD_CONST,
                       Opcode.LOAD_INDIRECT, Opcode.ADD, Opcode.ADD_CONST,
                       Opcode.SUB], 'Internal error'
        if sel is Opcode.READ:
            if len(self.input_buffer) == 0:
                raise EOFError()
            symbol = self.input_buffer.pop(0)
            symbol_code = ord(symbol)
            self.acc = symbol_code
            logging.debug('input: %s', repr(symbol))
        elif sel in [Opcode.LOAD, Opcode.LOAD_CONST, Opcode.LOAD_INDIRECT]:
            self.acc = self.dr
        elif sel in [Opcode.ADD, Opcode.ADD_CONST, Opcode.SUB]:
            if sel is Opcode.SUB:
                self.acc -= self.dr
            else:
                self.acc += self.dr

            if self.acc > 2**31 - 1:
                self.acc -= 2*32
            elif self.acc < -2**31:
                self.acc += 2**32

        self.flags = {"zero": 1 if self.acc == 0 else 0,
                      "sign": 1 if self.acc < 0 else 0}

    def latch_da(self, sel_sr: bool):
        if sel_sr:
            self.da = self.sr
        else:
            self.da = self.dr

    def output(self, sel: Opcode):
        assert sel in [Opcode.PRINT, Opcode.PRINT_INT], 'Internal error'
        if sel is Opcode.PRINT:
            symbol = chr(self.acc)
        else:
            symbol = str(self.acc)
        logging.debug('output: %s << %s', repr(
            ''.join(self.output_buffer)), repr(symbol))
        self.output_buffer.append(symbol)

    def wr(self):
        self.data_memory[self.da] = self.acc


class ControlUnit:
    def __init__(self, program: list, data_path: DataPath):
        self.program = program
        self.ip = 0  # instruction pointer
        self.data_path = data_path
        self._tick = 0

    def tick(self):
        self._tick += 1

    def current_tick(self):
        return self._tick

    def latch_ip(self, sel_next: bool):
        if sel_next:
            self.ip += 1
        else:
            instr = self.program[self.ip]
            assert 'arg' in instr, "internal error"
            self.ip = instr["arg"]

    def decode_and_execute_instruction(self):
        instr = self.program[self.ip]
        opcode = instr["opcode"]
        arg = instr["arg"]

        if arg != "":
            self.data_path.latch_sr(arg)

        if opcode is Opcode.LOAD:
            self.latch_ip(sel_next=True)
            self.data_path.latch_da(sel_sr=True)
            self.data_path.latch_dr(sel_memory=True)
            self.data_path.latch_acc(opcode)

            self.tick()
        elif opcode is Opcode.LOAD_CONST:
            self.latch_ip(sel_next=True)
            self.data_path.latch_dr(sel_memory=False)
            self.data_path.latch_acc(opcode)

            self.tick()
        elif opcode is Opcode.LOAD_INDIRECT:
            self.latch_ip(sel_next=True)
            self.data_path.latch_da(sel_sr=True)
            self.data_path.latch_dr(sel_memory=True)
            self.tick()

            self.data_path.latch_da(sel_sr=False)
            self.tick()

            self.data_path.latch_dr(sel_memory=True)
            self.data_path.latch_acc(opcode)
            self.tick()
        elif opcode is Opcode.STORE:
            self.latch_ip(sel_next=True)
            self.data_path.latch_da(sel_sr=True)
            self.data_path.wr()

            self.tick()
        elif opcode is Opcode.STORE_INDIRECT:
            self.latch_ip(sel_next=True)
            self.data_path.latch_da(sel_sr=True)
            self.data_path.latch_dr(sel_memory=True)
            self.tick()

            self.data_path.latch_da(sel_sr=False)
            self.data_path.wr()
            self.tick()
        elif opcode is Opcode.ADD:
            self.latch_ip(sel_next=True)
            self.data_path.latch_da(sel_sr=True)
            self.data_path.latch_dr(sel_memory=True)
            self.data_path.latch_acc(opcode)

            self.tick()
        elif opcode is Opcode.ADD_CONST:
            self.latch_ip(sel_next=True)
            self.data_path.latch_dr(sel_memory=False)
            self.data_path.latch_acc(opcode)

            self.tick()
        elif opcode is Opcode.SUB:
            self.latch_ip(sel_next=True)
            self.data_path.latch_da(sel_sr=True)
            self.data_path.latch_dr(sel_memory=True)
            self.data_path.latch_acc(opcode)

            self.tick()
        elif opcode in [Opcode.PRINT, Opcode.PRINT_INT]:
            self.latch_ip(sel_next=True)
            self.data_path.output(opcode)

            self.tick()
        elif opcode is Opcode.READ:
            self.latch_ip(sel_next=True)
            self.data_path.latch_acc(opcode)

            self.tick()
        elif opcode is Opcode.JMP:
            self.latch_ip(sel_next=False)

            self.tick()
        elif opcode in [Opcode.JE, Opcode.JNE]:
            expected_value = 1 if opcode is Opcode.JE else 0

            if self.data_path.flags['zero'] == expected_value:
                self.latch_ip(sel_next=False)
            else:
                self.latch_ip(sel_next=True)

            self.tick()
        elif opcode in [Opcode.JL, Opcode.JG]:
            expected_value = 1 if opcode is Opcode.JL else 0

            if self.data_path.flags['zero'] == 0 and self.data_path.flags['sign'] == expected_value:
                self.latch_ip(sel_next=False)
            else:
                self.latch_ip(sel_next=True)

            self.tick()
        elif opcode is Opcode.HLT:
            raise StopIteration()

    def __repr__(self):
        state = "{{TICK: {}, PC: {}, ADDR: {}, OUT: {}, ACC: {}}}".format(
            self._tick,
            self.ip,
            self.data_path.da,
            self.data_path.data_memory[self.data_path.da],
            self.data_path.acc,
        )

        instr = self.program[self.ip]
        instr_string = "{{OPCODE: {}, ARG: {}, POS: {}}}".format(
            instr['opcode'].value,
            instr['arg'],
            instr['term'].pos
        )

        return "{}, {}".format(state, instr_string)


def simulation(code, input_tokens, data_memory_size, limit, debug_level):
    data_path = DataPath(data_memory_size, input_tokens)
    control_unit = ControlUnit(code, data_path)
    instr_counter = 0

    logging.debug('%s', control_unit)
    try:
        while True:
            assert limit > instr_counter, "Too long execution, increase limit!"
            control_unit.decode_and_execute_instruction()
            instr_counter += 1

            if instr_counter < debug_level:
                logging.debug('%s', control_unit)
            elif instr_counter == debug_level:
                logging.debug('...')
    except EOFError:
        logging.warning('Input buffer is empty!')
    except StopIteration:
        pass
    out = ''.join(data_path.output_buffer)
    logging.info(f'output_buffer: {out}')
    return ''.join(data_path.output_buffer), instr_counter, control_unit.current_tick()


def main(args):
    assert len(args) == 2, "Wrong arguments: machine.py <code_file> <input_file>"
    code_file, input_file = args

    code = read_code(code_file)
    with open(input_file, encoding="utf-8") as file:
        input_text = file.read()
        input_token = []
        for char in input_text:
            input_token.append(char)

    input_token.append('\0')
    output, instr_counter, ticks = simulation(code,
                                              input_tokens=input_token,
                                              data_memory_size=1000,
                                              limit=10000000,
                                              debug_level=50)

    print(''.join(output))
    print("instr_counter: ", instr_counter, "ticks:", ticks)


if __name__ == '__main__':
    logging.getLogger().setLevel(logging.DEBUG)
    main(sys.argv[1:])
