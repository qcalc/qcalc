# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

import re

from calc import show_choice
from qcore import qchar, QTable
from calculators.all.general.utility.cal_range import valid_range
from calc import QResults, scalar_results
from qcore import qcode


def redo__info():
    return {
        'title': 'Redo Calculation',
        'desc': 'Repeat calculation by changing value of a variable',
        'schema': {
            'show': show_choice,
            'chart_type': {'type': 'choice', 'choices': ['lines', 'bars', 'stack']},
        },
        'col': ['1-6', '7-13'],
        'outcol': ['chart__r'],
        'kins': 'monte_carlo',
        'tags': 'sensitivity, parameter sweep, simulation',
    }


def redo(xpr: qcode = "sine('x deg')", variable: qchar = 'x',
         variation_start=0.0, variation_stop=360.0, variation_step=10.0, step_round_off=2,
         table_columns: str = '', table_units: str = '', chart_columns: str = '', chart_units: str = '', show='both',
         chart_title: str = '', chart_type='lines'):
    variable = (variable or '').strip()
    if not re.fullmatch(r'[A-Za-z_]\w*', variable):
        raise Exception(f"'{variable}' is not a valid variable name")
    if variation_step == 0:
        raise Exception("Variation step cannot be 0")
    if (variation_stop - variation_start) * variation_step < 0:
        raise Exception("Variation step direction does not match variation start/variation stop range")

    v_range = valid_range(variation_start, variation_stop, variation_step)
    var_vals = [round(x, step_round_off) for x in v_range]
    results, xvals = scalar_results(xpr=xpr, variable=variable, var_vals=var_vals)

    qr = QResults(results, xvals=xvals, variable=variable,
                  table_columns=table_columns, table_units=table_units, show=show)
    qr.setup_chart(chart_columns=chart_columns, chart_units=chart_units,
                   chart_title=chart_title, chart_type=chart_type)
    return qr.objects()
