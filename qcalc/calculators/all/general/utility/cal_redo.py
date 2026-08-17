# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

from calc import show_choice
from qutil import replace_words
from qcore import qchar
from calculators.all.general.utility.cal_range import valid_range
from calc import fchart
from calculators.all.general.cal_eva import eva


def redo__info():
    return {
        'title': 'Redo Calculation',
        'desc': 'Repeat calculation by changing value of a variable',
        'schema': {
            'xpr': {'type': 'textarea'},
            'show': show_choice
        },
        'newcol': ['xpr', 'result_columns'],
        'endcol': ['step_round_off', 'show'],
        'outcol': ['chart__r']
    }


def redo(xpr="sine('x deg')", variable: qchar = 'x',
         variation_start=0.0, variation_stop=360.0, variation_step=10.0, step_round_off=2,
         result_columns='', result_units='', chart_columns='', chart_units='', show='both'):
    # xvals = xrange(variation_start, variation_stop, variation_step, step_round_off)["Result"]
    v_range = valid_range(variation_start, variation_stop, variation_step)
    xvals = [round(x, step_round_off) for x in v_range]
    # xrange will call valid_range
    results = []
    for var in xvals:
        result = eva(code=replace_words(xpr, [variable], str(var)))
        # print(var, result)
        results.append(result)
    return fchart(results, xvals, result_columns, result_units, variable, chart_columns, chart_units, show)
