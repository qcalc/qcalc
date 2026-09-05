# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

from datetime import date
from qutil import QDateTime
from qcore import Qty


def age__info(): return {'title': 'Calculate Age from Date of Birth'}


def age(date_of_birth='1999-12-31'):
    tody = date.today()
    delta = tody - QDateTime(date_of_birth).val # normalize
    # return Qty(delta.days, 'd').in_units_of('yr', 'mo', 'd')
    return Qty(delta.days, 'd').as_units('yr, mo, d')
