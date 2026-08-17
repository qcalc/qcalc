# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

from calculators.all.general.chart.cal_chart import pareq
from qcore import qchar
import numpy as np
from calc import QChart


def lissa__info():
    return {
        'title': 'Lissajous Curve',
        'desc': 'Plot the parametric equations: x=a cos(3t) and y=b sin(2t)',
        'outcol': ['chart__r']
    }


def lissa(
    const_a: qchar = '25',
    const_b: qchar = '30'
):
    chart = pareq(
        x='a*cos(3*t)',
        y='b*sin(2*t)',
        variable='t',
        variable_start=0,
        variable_stop=6.28,
        variations=200,
        x_label='x',
        y_label='y',
        title='Lissajous Curve',
        const_1='a', const_1_part=const_a,
        const_2='b', const_2_part=const_b,
        aspect=1
    )
    return {'chart': chart}


def hypo1__info():
    return {
        'title': 'Hypotrochoid Curve 1',
        'desc': 'Plot the parametric equations: x=(R-r)*cos(t)+d*cos((R-r)*t/r) and '
                'y=(R-r)*sin(t)-d*sin((R-r)*t/r) for R=6, r=4 and d=1',
        'outcol': ['chart__r']
    }


def hypo1(
    Fixed_r: qchar = '6',
    Inner_r: qchar = '4',
    Distance_d: qchar = '1'
):
    chart = pareq(
        x='(R-r)*cos(t)+d*cos((R-r)*t/r)',
        y='(R-r)*sin(t)-d*sin((R-r)*t/r)',
        variable='t',
        variable_start=0,
        variable_stop=90,
        variations=1000,
        x_label='x',
        y_label='y',
        title='Hypotrochoid Curve',
        const_1='R', const_1_part=Fixed_r,
        const_2='r', const_2_part=Inner_r,
        const_3='d', const_3_part=Distance_d,
        aspect=1
    )
    return {'chart': chart}


def hypo2__info():
    return {
        'title': 'Hypotrochoid Curve 2',
        'desc': 'Plot the parametric equations: x=(R-r)*cos(t)+d*cos((R-r)*t/r) and '
                'y=(R-r)*sin(t)-d*sin((R-r)*t/r) for R=7, r=4 and d=1',
        'outcol': ['chart__r']
    }


def hypo2(
    Fixed_r: qchar = '7',
    Inner_r: qchar = '4',
    Distance_d: qchar = '1'
):
    return hypo1(
        Fixed_r=Fixed_r,
        Inner_r=Inner_r,
        Distance_d=Distance_d
    )


def hypo3__info():
    return {
        'title': 'Hypotrochoid Curve 3',
        'desc': 'Plot the parametric equations: x=(R-r)*cos(t)+d*cos((R-r)*t/r) and '
                'y=(R-r)*sin(t)-d*sin((R-r)*t/r) for R=8, r=3 and d=2',
        'outcol': ['chart__r']
    }


def hypo3(
    Fixed_r: qchar = '8',
    Inner_r: qchar = '3',
    Distance_d: qchar = '2'
):
    return hypo1(
        Fixed_r=Fixed_r,
        Inner_r=Inner_r,
        Distance_d=Distance_d
    )


def hypo4__info():
    return {
        'title': 'Hypotrochoid Curve 4',
        'desc': 'Plot the parametric equations: x=(R-r)*cos(t)+d*cos((R-r)*t/r) and '
                'y=(R-r)*sin(t)-d*sin((R-r)*t/r) for R=7, r=4 and d=2',
        'outcol': ['chart__r']
    }


def hypo4(
    Fixed_r: qchar = '7',
    Inner_r: qchar = '4',
    Distance_d: qchar = '2'
):
    return hypo1(
        Fixed_r=Fixed_r,
        Inner_r=Inner_r,
        Distance_d=Distance_d
    )


def hypo5__info():
    return {
        'title': 'Hypotrochoid Curve 5',
        'desc': 'Plot the parametric equations: x=(R-r)*cos(t)+d*cos((R-r)*t/r) and '
                'y=(R-r)*sin(t)-d*sin((R-r)*t/r) for R=15, r=14 and d=1',
        'outcol': ['chart__r']
    }


def hypo5(
    Fixed_r: qchar = '15',
    Inner_r: qchar = '14',
    Distance_d: qchar = '1'
):
    return hypo1(
        Fixed_r=Fixed_r,
        Inner_r=Inner_r,
        Distance_d=Distance_d
    )


def butterfly__info():
    return {
        'title': 'Butterfly Curve',
        'desc': 'Plot the parametric equations: x=sin(t)*(exp(cos(t))-2*cos(4*t)-(sin(t/12))**5) and '
                'y=cos(t)*(exp(cos(t))-2*cos(4*t)-(sin(t/12))**5) for 0<=t<=12*pi',
        'outcol': ['chart__r']
    }


def butterfly(
    variations=1000
):
    chart = pareq(
        x='sin(t)*(exp(cos(t))-2*cos(4*t)-(sin(t/12))**5)',
        y='cos(t)*(exp(cos(t))-2*cos(4*t)-(sin(t/12))**5)',
        variable='t',
        variable_start=0,
        variable_stop=37.7,
        variations=variations,
        x_label='x',
        y_label='y',
        title='Butterfly Curve',
        aspect=1
    )
    return {'chart': chart}


def spiral__info():
    return {
        'title': 'Spiral Curve'
    }


def spiral(n=4, a=1.0, b=0.2):
    # | https://matplotlib.org/stable/gallery/misc/fill_spiral.html
    theta = np.arange(0, n * 2 * np.pi, 0.1)
    chart = QChart()
    fig, ax = chart.create_figure()
    for dt in np.arange(0, 2 * np.pi, np.pi / 2.0):
        x = a * np.cos(theta + dt) * np.exp(b * theta)
        y = a * np.sin(theta + dt) * np.exp(b * theta)

        dt = dt + np.pi / 4.0

        x2 = a * np.cos(theta + dt) * np.exp(b * theta)
        y2 = a * np.sin(theta + dt) * np.exp(b * theta)

        xf = np.concatenate((x, x2[::-1]))
        yf = np.concatenate((y, y2[::-1]))

        p1 = ax.fill(xf, yf)

    chart.render_done()
    return {'chart': chart}
