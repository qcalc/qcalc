# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

# from qcore import qtime, qdatetime
from qutil import QDateTime
from qcore import Qty


def demo_dt__info():
    return {
        'title': 'Test Auto Date Time Field Creation'
    }


def demo_dt(
    a='2024-09-23',
    b='18:06',
    c='18:06:30',
    d='2024-09-23 18:06:30+06:00',
    e='2024-09-23 18:06:30.123456+06:00',
    f='5 ft',
    g=QDateTime('2024-09-15')
):
    # print('t', type(a), type(b), type(e), type(f))
    return {
        'a val': a,
        'b val': b,
        'c val': c,
        'd val': d,
        'e val': e,
        'a val2': QDateTime(a),
        'b val2': QDateTime(b),
        'c val2': QDateTime(c),
        'd val2': QDateTime(d),
        'e val2': QDateTime(e),
        'f-val2': f,
        'g-val2': g,
    }
