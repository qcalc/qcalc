# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

from datetime import date
from qutil import QDateTime
from qcore import Qty


def age__info():
    return {
        'title': 'Calculate Age from Date of Birth',
        'step2': [
            {
                'step': 'run',
                'func': 'moonphase',
                'caption': 'Calculate Moonphase',
                'spec': {'on_date': 'date_of_birth'},
            }
        ],
    }


def age(date_of_birth='1999-12-31'):
    tody = date.today()
    dob = QDateTime(date_of_birth)
    delta = tody - dob.val  # normalize
    # Build the next birthday date for the current year; fallback for Feb 29 in non-leap years.
    try:
        next_bday = date(tody.year, dob.val.month, dob.val.day)
    except ValueError:
        next_bday = date(tody.year, 2, 28)

    if next_bday < tody:
        try:
            next_bday = date(tody.year + 1, dob.val.month, dob.val.day)
        except ValueError:
            next_bday = date(tody.year + 1, 2, 28)

    next_bday_in_days = (next_bday - tody).days
    return {
        'Age': Qty(delta.days, 'd').as_units('yr, mo, d'),
        'Day of Birth': dob.day_name(),
        'Next Birthday In': Qty(next_bday_in_days, 'day'),
    }
