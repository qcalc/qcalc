# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

from calc.mod_mfunc import func_meta
from calc import QCals
from qcore import qhtml, QScreen, qpretty_json
from calc import get_code, func_guide


# https://docs.python.org/2/howto/doanddont.html#from-module-import

def code__info():
    return {
        'title': 'Show Code',
        'calculate': 'Show',
        'kins': 'meta',
    }


def code(func_id: str = 'gold', show_meta=True):
    return {'code': qhtml(get_code(func_id, show_meta))}


def meta__info():
    return {
        'title': 'Function Meta',
        'kins': 'code',
    }


def meta(func_id: str = 'gold'):
    # func_id = func_name
    func_addr = QCals.addr(func_id, 'qop')

    if func_addr:
        fargs, fanns, finfs = func_meta(func_addr, func_id, None)
        resp = qpretty_json({'fargs': fargs, 'fanns': fanns, 'finfs': finfs})
    else:
        resp = f"Function {func_id} not found"

    out = QScreen()
    out.write(resp)
    return out.flush()


def explain__info():
    return {
        'title': 'Explain the Calculator function',
        'calculate': 'Explain',
        'kins': 'code, meta'
    }


def explain(qc_name: str = 'gold'):
    result = {}
    user_guide = func_guide(qc_name)
    result.update({'End User Guide': qhtml(user_guide)})
    return result
