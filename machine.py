import logging
from isa import Opcode, read_code

"""
    CPU model
"""


class ArithmeticLogicUnit:
    def __init__(self):
        self.left = 0
        self.right = 0
        self.result = 0

    def get_left(self):
        self.result = self.left

    def get_right(self):
        self.result = self.right

    def add(self):
        self.result = self.left + self.right

    def sub(self):
        self.result = self.left - self.right

    
class DataPath:
    def __init__(self, data_memory_size: int, input_buffer: list, alu: ArithmeticLogicUnit):
        assert data_memory_size > 0, "Data_memory size should be non-zero"
        self.data_memory_size = data_memory_size
        self.data_memory = [0] * data_memory_size
        self.data_address = 0
        self.acc = 0
        self.dr = 0
        self.input_buffer = input_buffer
        self.output_buffer = []
        self.alu = alu

    def latch_data_addr(self, sel):
        self.data_address = sel

        assert 0 <= self.data_address < self.data_memory_size, \
            "out of memory: {}".format(self.data_address)

    def latch_dr(self, sel):
        self.dr = sel

    def latch_dr_from_memory(self):
        self.dr = self.data_memory[self.data_address]

    def latch_alu_registers(self):
        self.alu.left = self.acc
        self.alu.right = self.dr

    def latch_acc_from_alu(self):
        self.acc = self.alu.result

    def latch_data_address_from_alu(self):
        self.data_address = self.alu.result

    def latch_acc_from_memory(self):  # load
        self.acc = self.data_memory[self.data_address]

    def input(self):
        if len(self.input_buffer) == 0:
            raise EOFError()
        symbol = self.input_buffer.pop(0)
        symbol_code = ord(symbol)
        self.acc = symbol_code
        logging.debug('input: %s', repr(symbol))

    def output(self):
        symbol = chr(self.acc)
        logging.debug('output: %s << %s', repr(
            ''.join(self.output_buffer)), repr(symbol))
        self.output_buffer.append(symbol)

    def output_int(self):
        symbol = str(self.acc)
        logging.debug('output: %s << %s', repr(
            ''.join(self.output_buffer)), repr(symbol))
        self.output_buffer.append(symbol)

    def wr(self):
        self.data_memory[self.data_address] = self.acc  # todo

    def zero(self):
        return self.acc == 0


class ControlUnit:
    def __init__(self, program: list, data_path: DataPath):
        self.program = program
        self.program_counter = 0
        self.data_path = data_path
        self._tick = 0

    def tick(self):
        self._tick += 1

    def current_tick(self):
        return self._tick

    def latch_program_counter(self, sel_next):
        if sel_next:
            self.program_counter += 1
        else:
            instr = self.program[self.program_counter]
            assert 'arg' in instr, "internal error"
            self.program_counter = instr["arg"]

    def decode_and_execute_instruction(self):
        instr = self.program[self.program_counter]
        opcode = instr["opcode"]
        arg = instr["arg"]

        self.tick()

        if opcode is Opcode.LOAD:
            self.data_path.latch_dr(arg)
            self.data_path.latch_alu_registers()
            self.data_path.alu.get_right()
            self.data_path.latch_data_address_from_alu()
            self.data_path.latch_acc_from_memory()

            self.program_counter += 1
        elif opcode is Opcode.LOAD_CONST:
            if arg == -1:
                pass
            self.data_path.latch_dr(arg)
            self.data_path.latch_alu_registers()
            self.data_path.alu.get_right()
            self.data_path.latch_acc_from_alu()

            self.program_counter += 1
        elif opcode is Opcode.LOAD_MEM:
            self.data_path.latch_dr(arg)
            self.data_path.latch_alu_registers()
            self.data_path.alu.get_right()
            self.data_path.latch_data_address_from_alu()
            self.data_path.latch_acc_from_memory()

            self.data_path.latch_alu_registers()
            self.data_path.alu.get_left()
            self.data_path.latch_data_address_from_alu()
            self.data_path.latch_acc_from_memory()

            self.program_counter += 1
        elif opcode is Opcode.STORE:
            self.data_path.latch_dr(arg)
            self.data_path.latch_alu_registers()
            self.data_path.alu.get_right()
            self.data_path.latch_data_address_from_alu()
            self.data_path.wr()

            self.program_counter += 1
        elif opcode is Opcode.STORE_MEM:
            self.data_path.latch_dr(arg)
            self.data_path.latch_alu_registers()
            self.data_path.alu.get_right()
            self.data_path.latch_data_address_from_alu()
            self.data_path.latch_dr_from_memory()

            self.data_path.latch_alu_registers()
            self.data_path.alu.get_right()
            self.data_path.latch_data_address_from_alu()
            self.data_path.wr()

            self.program_counter += 1
        elif opcode is Opcode.ADD:
            self.data_path.latch_dr(arg)
            self.data_path.latch_alu_registers()
            self.data_path.alu.get_right()
            self.data_path.latch_data_address_from_alu()
            self.data_path.latch_dr_from_memory()
            self.data_path.alu.add()
            self.data_path.latch_acc_from_alu()

            self.program_counter += 1
        elif opcode is Opcode.ADD_CONST:
            self.data_path.latch_dr(arg)
            self.data_path.latch_alu_registers()
            self.data_path.alu.add()
            self.data_path.latch_acc_from_alu()

            self.program_counter += 1
        elif opcode is Opcode.SUB:
            self.data_path.latch_dr(arg)
            self.data_path.latch_alu_registers()
            self.data_path.alu.get_right()
            self.data_path.latch_data_address_from_alu()
            self.data_path.latch_dr_from_memory()
            self.data_path.alu.sub()
            self.data_path.latch_acc_from_alu()

            self.program_counter += 1
        elif opcode is Opcode.PRINT:
            self.data_path.output()

            self.program_counter += 1
        elif opcode is Opcode.PRINT_INT:
            self.data_path.output_int()

            self.program_counter += 1
        elif opcode is Opcode.READ:
            self.data_path.input()

            self.program_counter += 1
        elif opcode is Opcode.JMP:
            self.program_counter = arg - 1

            self.program_counter += 1
        elif opcode is Opcode.JE:
            if self.data_path.acc == 0:
                self.program_counter = arg - 1

            self.program_counter += 1
        elif opcode is Opcode.JNE:
            if self.data_path.acc != 0:
                self.program_counter = arg - 1

            self.program_counter += 1
        elif opcode is Opcode.JG:
            if self.data_path.acc > 0:
                self.program_counter = arg - 1

            self.program_counter += 1
        elif opcode is Opcode.JL:
            if self.data_path.acc < 0:
                self.program_counter = arg - 1

            self.program_counter += 1
        elif opcode is Opcode.HLT:
            raise StopIteration()

    def __repr__(self):
        state = "{{TICK: {}, PC: {}, ADDR: {}, OUT: {}, ACC: {}}}".format(
            self._tick,
            self.program_counter,
            self.data_path.data_address,
            self.data_path.data_memory[self.data_path.data_address],
            self.data_path.acc,
        )

        return "{}".format(state)


def simulation(code, input_tokens, data_memory_size, limit):
    alu = ArithmeticLogicUnit()
    data_path = DataPath(data_memory_size, input_tokens, alu)
    control_unit = ControlUnit(code, data_path)
    instr_counter = 0

    logging.debug('%s', control_unit)
    try:
        while True:
            assert limit > instr_counter, "too long execution, increase limit!"
            control_unit.decode_and_execute_instruction()
            instr_counter += 1
            logging.debug('%s', control_unit)
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
                                              limit=1000)

    print(''.join(output))
    print("instr_counter: ", instr_counter, "ticks:", ticks)


if __name__ == '__main__':
    logging.getLogger().setLevel(logging.DEBUG)
    main(['machine_code/basic.json', 'io/input.txt'])
