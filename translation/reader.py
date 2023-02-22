import re
from isa import *
from translation.common import *


def is_num(word):
    """Проверка на то, что поданный аргумент число"""
    return word.isnumeric()


def remove_comments(text):
    return re.sub(r';[^\n]*', '', text)


def add_spaces(text):
    clear_text = re.sub('\(', ' ( ', text)
    return re.sub('\)', ' ) ', clear_text)


def validate_brackets(text):
    assert len(re.findall(r'\(', text)) - len(re.findall(r'\)', text)) == 0, "Unbalanced brackets"


def get_list_and_rest(terms):
    assert terms[0] == '(', 'Incorrect function usage'
    rest = terms.copy()
    depth = 0
    lisp_list = []

    for term in terms:
        lisp_list.append(term)
        rest.pop(0)

        if term == '(':
            depth += 1
        elif term == ')':
            depth -= 1
            if depth == 0:
                break

    return [lisp_list, rest]


def split_terms_into_lists(terms):
    lisp_terms = terms
    lisp_lists = []

    while len(lisp_terms) != 0:
        assert lisp_terms[0] == '(', 'Incorrect Lisp code'
        lisp_list, lisp_terms = get_list_and_rest(lisp_terms)
        lisp_lists.append(lisp_list)

    return lisp_lists


def convert_list_to_s_expression(lisp_list):
    prev_s_expressions = []
    args = lisp_list
    assert args[0] == '(' and args[-1] == ')', f"Incorrect function usage with arg = {lisp_list}"
    args.pop(0)
    args.pop()
    assert args[0] in functions, f'{args[0]} is not lisp operator or function in this translator'
    s_expression = SymbolicExpression(args.pop(0))
    if s_expression.operator == 'loop':
        if args[0] == 'for':
            args.pop(0) #for
            iter_var = args.pop(0) #i
            assert args.pop(0) == 'from', 'Incorrect for loop'
            assert args.pop(1) == 'to', 'Incorrect for loop'
            iter_span = [int(args.pop(0)), int(args.pop(0))]
            assert args.pop(0) == 'do', 'Incorrect for loop'
            prev_s_expressions.append(SymbolicExpression('setq', iter_var, iter_span[0]))
            args += split_code_into_terms(
                add_spaces(f'(setq {iter_var} (+ {iter_var} 1))'
                           f'(if (> {iter_var} {iter_span[1]}) (return))'
                           )
            )

        inner_lists = split_terms_into_lists(args)
        inner_s_expressions = []
        for inner_lisp_list in inner_lists:
            inner_s_expressions += convert_list_to_s_expression(inner_lisp_list)
        s_expression.args = inner_s_expressions
    else:
        while len(args) > 0:
            # убрать скобки у например (t)
            if len(args) >= 3 and args[0] == '(' and (not args[1] in functions) and args[2] == ')':
                args.pop(0)
                args.pop(1)

            # lisp atom
            if args[0] != '(':
                cur_term = args.pop(0)

                if is_num(cur_term):
                    cur_term = int(cur_term)
                elif cur_term == 't' or cur_term == 'T':
                    cur_term = True
                elif cur_term == 'NIL':
                    cur_term = False

                s_expression.args.append(cur_term)
            # lisp list
            else:
                inner_lisp_list, args = get_list_and_rest(args)
                s_expression.args += convert_list_to_s_expression(inner_lisp_list)

    return prev_s_expressions + [s_expression]


def split_code_into_terms(code):
    terms = []
    is_inside_string = False

    for line in code.split('\n'):
        for word in line.split():
            quotes = re.findall(r'\"', word)
            pos = word.find('"')

            if is_inside_string:
                terms[-1] += ' ' + word
            else:
                terms.append(word)

            if len(quotes) == 1 and pos == 0:
                is_inside_string = True
            elif len(quotes) == 1 and pos > 0:
                is_inside_string = False

    return terms


def read(code):
    clean_code = remove_comments(code)
    clean_code = add_spaces(clean_code)
    validate_brackets(clean_code)

    terms = split_code_into_terms(clean_code)
    lisp_lists = split_terms_into_lists(terms)
    s_expressions = []

    for lisp_list in lisp_lists:
        s_expressions_from_lisp_list = convert_list_to_s_expression(lisp_list)
        s_expressions += s_expressions_from_lisp_list
        for exp in s_expressions_from_lisp_list:
            print(exp)

    return s_expressions
