class SymbolicExpression:
    def __str__(self) -> str:
        args = []
        for arg in self.args:
            args.append(str(arg))

        return '{' + f'operator: {self.operator}, args:{args}' + '}'

    def __init__(self, operator, *args):
        self.operator = operator
        self.args = list(args)
