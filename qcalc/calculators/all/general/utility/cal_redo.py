# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

from calc import show_choice
from qutil import replace_words
from qcore import qchar
from calculators.all.general.utility.cal_range import valid_range
from calc import results2chart, scalar_values
from calculators.all.general.cal_eva import eva
from qcore import qtexta


def redo__info():
    return {
        'title': 'Redo Calculation',
        'desc': 'Repeat calculation by changing value of a variable',
        'schema': {
            'show': show_choice,
            'chart_type': {'type': 'choice', 'choices': ['lines', 'bars', 'stack']},
        },
        # 'newcol': ['xpr', 'result_columns'],
        # 'endcol': ['step_round_off', 'show'],
        'col': ['1-6', '7-13'],
        'outcol': ['chart__r']
    }


def redo(xpr: qtexta = "sine('x deg')", variable: qchar = 'x',
         variation_start=0.0, variation_stop=360.0, variation_step=10.0, step_round_off=2,
         result_columns: str = '', result_units: str = '', chart_columns: str = '', chart_units: str = '', show='both',
         chart_title: str = '', chart_type='lines'):
    # xvals = xrange(variation_start, variation_stop, variation_step, step_round_off)["Result"]
    v_range = valid_range(variation_start, variation_stop, variation_step)
    xvals = [round(x, step_round_off) for x in v_range]
    # xrange will call valid_range
    results = []
    for var in xvals:
        code = replace_words(xpr, [variable], str(var))
        result = eva(code=code)
        sc_values = scalar_values(result)
        print('|', sc_values)
        results.append(sc_values)
    return results2chart(
        results=results,
        xvals=xvals,
        result_columns=result_columns,
        result_units=result_units,
        chart_x_axis=variable,
        chart_columns=chart_columns,
        chart_units=chart_units,
        show=show,
        title=chart_title,
        chart_type=chart_type)
