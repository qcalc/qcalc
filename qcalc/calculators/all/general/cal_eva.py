# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

from qcore import QScreen, qcode
from calc import QCals, QPref
from calc.mod_qcals_security import validate_expression_security
from asteval import Interpreter
from qvars import qc_gpref as gs
from qutil import preprocess_expression, command_button, format_py_code


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
        }
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
        calout.append(args)

    out = QScreen()
    syms = QCals.qsymbol_dict.copy()
    syms.update({"show": show})
    # reserved_syms = set(syms)
    # strict_assign = QPref.getp1('strict_assign')

    aeval = Interpreter(
        symtable=syms,
        # strict_assign is commented out, so evaluator code can be used/shared freely.
        # readonly_symbols=reserved_syms if strict_assign else None,
        nested_symtable=True,
        # user_symbols=QCals.qsymbol_dict,
        writer=out.out,
        err_writer=out.out,
        # builtins_readonly=True,
    )

    expr = preprocess_expression(code)
    try:
        validate_expression_security(expr, syms)
    except Exception as e:
        return {'result': f'Error (EVR): {e}'}

    res = aeval(expr)
    # print(res)
    if res is not None:
        show(res)
    stdout = out.flush()
    toret = {}
    if calout:
        toret = {'': calout}
    if stdout:
        toret.update({'console': stdout})
    if not toret:
        toret = {'result': 'Output is empty'}
    return toret

