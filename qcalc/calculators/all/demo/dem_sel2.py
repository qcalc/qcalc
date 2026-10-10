# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

from qcore import Qty
from calc import QList, activity_choice


def demo_sel2__info():
    return {
        'title': 'Select2 Testing',
        'schema': {
            'activity': activity_choice,
            'country1': QList.getx("country", type='qsel2', sel2id='cntry'),
            'country2': {'type': 'qsel2', 'sel2id': 'cntry', 'initial': 'JP'},
        },
    }


def demo_sel2(
    activity=1.2,
    country1='IN',
    country2='BD',
    weight='25.0 kg',
    length='5.0 ft',
    pressure='75 bar',
):
    uwt = Qty(weight) / Qty(length)
    pr = Qty(pressure, 'mmh2O')
    return (
        country1,
        country2,
        uwt,
        pr
    )
