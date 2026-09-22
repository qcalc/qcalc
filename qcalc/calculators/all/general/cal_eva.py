# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

from qcore import QScreen, qcode
from calc import QCals
from asteval import Interpreter
from qvars import qc_gpref as gs
from qutil import preprocess_expression, command_button, format_py_code, validate_expression_security


def eva__modify(arg_name, arg_value, action):
    if arg_name == 'code' and action == 'format':
        user_code = format_py_code(arg_value)
        return user_code
    return arg_value


def eva__info():
    return {
        'title': 'Simple Expression Evaluator',
        'desc': 'Evaluate arbitrary expressions and functions',
        'inserts': {
            'form_top': command_button('eva', 'Format Code', '__modify', kwargs={'code': 'format'})
        },
        'kins': 'mycal',
    }


def eva(code: qcode = '''print('Example Calculation')
x = q('5 ft') + q('3 m')
x = x.to('inch')
show(x)

price = q('75 usd/inch')
cost = x*price
show(cost)

y = 1*ft + 3*m
show(y)
'''):
    calout = []

    rlimit = gs['range_limit']

    def show(*args):
        if len(calout) > rlimit:
            raise Exception(f'Error (EVR): Range limit [{rlimit}] for show() exceeded')
        n = len(args)
        calout.append(args if n>1 else args[0])

    out = QScreen()
    syms = QCals.qsymbol_dict.copy()
    syms.update({"show": show})
    # reserved_syms = set(syms)
    # strict_assign = QPref.getp1('strict_assign')

    aeval = Interpreter(
        # nested_symtable requires an asteval Group-based symtable (built via
        # user_symbols=), not a plain dict, or calls to user-defined functions
        # break name lookup (AttributeError: 'dict' object has no attribute
        # '__getattr__').
        user_symbols=syms,
        # strict_assign is commented out, so evaluator code can be used/shared freely.
        # readonly_symbols=reserved_syms if strict_assign else None,
        nested_symtable=True,
        writer=out.out,
        # err_writer=out.out,
        # builtins_readonly=True,
    )

    expr = preprocess_expression(code)
    try:
        validate_expression_security(expr, syms)
    except Exception as e:
        return {'result': f'{e}'}

    res = aeval(expr, show_errors=False)
    if aeval.error:
        return {'result': format_eval_error(aeval.error[0])}

    if res is not None:
        show(res)
    stdout = out.flush()
    toret = {}
    if calout:
        n = len(calout)
        toret = {'': calout} if n > 1 else calout[0]

    if stdout:
        toret = {'':toret, 'console': stdout}

    # | Don't return this message, as output can be 0 or None too
    # if not toret:
    #     toret = {'result': 'Output is empty'}
    return toret

def format_eval_error(error):
    exc_info = getattr(error, 'exc_info', None)

    if exc_info and len(exc_info) >= 2 and exc_info[1] is not None:
        exc = exc_info[1]
        message = f'{type(exc).__name__}: {exc}'
    else:
        message = error.msg

    line_no = getattr(error.node, 'lineno', None)

    result = (
        f'Error at line {line_no}: {message}'
        if line_no
        else f'Error: {message}'
    )

    expr = getattr(error, 'expr', '')

    if expr and line_no:
        lines = expr.splitlines()

        if 0 < line_no <= len(lines):
            source_line = lines[line_no - 1].strip()

            if len(source_line) > 120:
                if '(' in source_line:
                    source_line = source_line[:source_line.index('(') + 1] + '...)'
                else:
                    source_line = source_line[:117] + '...'

            result += f'\n\n>> {source_line}'

    return result
