# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

import numpy as np
import pandas as pd

from qcore import Qty, quomx, qtexta
from qvars import qc_gpref as gs
from calc import QCals, df2chart
from qutil import vals2css


def valid_range(variation_start, variation_stop, variation_step):
    if int((variation_stop + variation_step - variation_start) / variation_step) > gs['range_limit']:
        raise Exception(f"Error (VR): Range limit of {gs['range_limit']} exceeded")
    else:
        return np.arange(variation_start, variation_stop + variation_step, variation_step)


def fx__info():
    return {
        'title': 'Calculate y=f(x)',
        'schema': {
            'output_format': {'type': 'checkboxselectmultiple', 'choices': ['CSV', 'Table', 'Chart']}
        }
    }


def fx(y: qtexta = 'x**2+2*x-5', variable='x', variation_start=1.0, variation_stop=10.0, variation_step=1.0,
       round_off=2,
       output_format=['CSV']):
    v_range = valid_range(variation_start, variation_stop, variation_step)
    df = pd.DataFrame({"X": [round(x, round_off) for x in v_range],
                       "Y": [round(QCals.safe_eval(y, ldict={variable: x}), round_off) for x in v_range]})

    toret = {}
    if 'CSV' in output_format or output_format == []:
        toret['X'] = vals2css(df['X'])
        toret['Y'] = vals2css(df['Y'])
    if 'Table' in output_format:
        df2 = df.copy()
        df2['X'] = df2['X'].apply(lambda x: str(x))
        df2['Y'] = df2['Y'].apply(lambda y: str(y))
        toret['Table'] = df2
    if 'Chart' in output_format:
        chart=df2chart(df,'X')
        toret['Chart'] = chart
    return toret


def vrange__info():
    return {
        'title': 'Values within a Given Range and Step',
        'schema': {
            'output_format': {'type': 'checkboxselectmultiple', 'choices': ['CSV', 'Table', 'Chart']}
        }
    }


def vrange(variation_start=100.0, variation_stop=200.0, variation_step=10.0, step_round_off=2,
           output_format=['CSV']):
    v_range = valid_range(variation_start, variation_stop, variation_step)
    df = pd.DataFrame({"Result": [round(x, step_round_off) for x in v_range]})

    toret = {}
    if 'CSV' in output_format or output_format == []:
        toret['CSV'] = vals2css(df['Result'])
    if 'Table' in output_format:
        toret['Table'] = df
    if 'Chart' in output_format:
        chart = df2chart(df)
        toret['Chart'] = chart
    return toret


def qrange__info(): return {'title': 'Quantities within a Given Range and Increment'}


def qrange(variation_start=100.0, variation_stop=200.0, variation_unit: quomx = 'ft', variation_step=10.0,
           step_unit: quomx = 'ft',
           step_round_off=2):
    qvariation_start = Qty(variation_start, variation_unit)
    qvariation_stop = Qty(variation_stop, variation_unit)
    qvariation_step = Qty(variation_step, step_unit, variation_unit)
    v_range = valid_range(qvariation_start.val, qvariation_stop.val, qvariation_step.val)
    dfq = pd.DataFrame({"Result": [Qty(x, variation_unit).roundoff(step_round_off) for x in v_range]})
    df = pd.DataFrame({"Result": [round(x, step_round_off) for x in v_range]})
    chart=df2chart(df)
    return {'table': dfq, 'chart': chart}
