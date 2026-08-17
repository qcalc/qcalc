# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

import numpy as np
# from .mod_chart import line_chart
from qutil import css2floats
from qcore import QChart


def linter__info():
    return {
        'title': 'Linear Interpolation',
        'schema': {
            'x_values': {'type': 'textarea'},
            'y_values': {'type': 'textarea'}
        },
        'outcol': ['chart__r']
    }


def linter(x_values='1,2,3.2,4,5', y_values='2,3,5.8,12,20', x=2.5):
    xvf = css2floats(x_values)
    yvf = css2floats(y_values)
    y = np.interp(x, xvf, yvf)
    # ch = line(x_values, y_values)
    chart = QChart()  # patch=True
    fig, ax = chart.create_figure()
    ax.plot(xvf, yvf)
    ax.plot(x, y, 'ro')
    chart.render_done()
    # chart.close()
    return {
        'Result': y,
        'chart': chart,
    }


"""
20	17.7	8.5
25	18.4	10.5
30	19.3	12.7
35	21.5	13.7
40	22.2	15.3
45	22.9	16.4
50	25.2	18.9
55	26.3	20.9
"""
