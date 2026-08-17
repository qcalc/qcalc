# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

import math
from statistics import mean, fmean, median, mode, stdev, pstdev, \
    geometric_mean, harmonic_mean, median_low, median_high, variance, pvariance, quantiles
import pandas as pd
import scipy.stats as ss
from qutil import css2floats
from qcore import qchar, qtable
from calculators.all.general.chart.cal_chart import pareq
import numpy as np


# correlation, covariance (part of statistics in python 3.10+)


def stat__info():
    return {
        'title': 'Basic Statistics',
        'desc': 'Calculate mathematical statistics of numeric data. '
                'Enter values and optionally weights separated by comma (,). '
                'Weights, if entered, must be of same length. At least two values are required.',
        'schema': {
            'numbers': {'type': 'textarea'},
            'weights': {'type': 'textarea', 'label': 'Weights (optional)'}
        },
        'outcol': ['result']
    }


# https://docs.python.org/3/library/statistics.html
def stat(numbers='1,2,3,4,5', weights=''):
    # arr = numbers.split(',')
    # print(arr)
    # nums = [float(x) for x in arr]
    nums = css2floats(numbers)
    # print(nums)
    avg = fmean(nums)
    havg = harmonic_mean(nums)
    if weights != '':
        # warr = weights.split(',')
        # wnums = [float(x) for x in warr]
        wnums = css2floats(weights)
        if len(nums) != len(wnums):
            raise Exception(
                f"Error (STAT): {len(nums)} Values and {len(wnums)} Weights found. Please enter in equal numbers.")
        else:
            wavg = sum(list(map(lambda x, y: x * y, nums, wnums))) / sum(wnums)
            if 0 in nums:
                whavg = 0
            else:
                whavg = sum(wnums) / sum(list(map(lambda x, y: 1 / x * y, nums, wnums)))
    else:
        wavg = avg
        whavg = havg

    qnt = [q for q in quantiles(nums, n=4)]

    return {
        "Count": len(nums),
        "Sum": sum(nums),
        "Mean": avg,
        "Weighted Mean": wavg,
        "Harmonic Mean": havg,
        "Weighted Harmonic Mean": whavg,
        "Geometric Mean": geometric_mean(nums),
        "Median": median(nums),
        "Median Low": median_low(nums),
        "Median High": median_high(nums),
        "Mode": mode(nums),
        "Standard Deviation": stdev(nums),
        "Population StDev": pstdev(nums),
        "Variance": variance(nums, avg),
        "Population Variance": pvariance(nums, avg),
        "25th Percentile": qnt[0],
        "50th Percentile": qnt[1],
        "75th Percentile": qnt[2]
    }


# print(mean(array(1,2,3,4,5)))
# print(mean([1,2,3,4,5]))

def corr__info():
    return {
        'title': 'Correlation and Covariance',
        'desc': 'Correlation measures the length and direction of linear relationship. '
                'Covariance measures the joint variability of two data points.',
        'schema': {
            'x_numbers': {'type': 'textarea'},
            'y_numbers': {'type': 'textarea'}
        },
    }


# https://realpython.com/numpy-scipy-pandas-correlation-python/
def corr(x_numbers='10, 11, 12, 13, 14, 15, 16, 17, 18, 19',
         y_numbers='2, 1, 4, 5, 8, 12, 18, 25, 96, 48'):
    # arr = x_numbers.split(',')
    # xnums = [float(x) for x in arr]
    xnums = css2floats(x_numbers)
    x = pd.Series(xnums)

    # arr = y_numbers.split(',')
    # ynums = [float(x) for x in arr]
    ynums = css2floats(y_numbers)
    y = pd.Series(ynums)

    # pear_r = x.corr(y, method='pearson')
    # kend_tau = x.corr(y, method='kendall')
    # spear_roh = x.corr(y, method='spearman')
    # cov = x.cov(y)

    pear_r, pear_p = ss.pearsonr(x, y)
    kend_tau, kend_p = ss.kendalltau(x, y)
    spear_roh, spear_p = ss.spearmanr(x, y)

    slope, intercept, r, p, stderr = ss.linregress(x, y)
    reg_line = f'y = {intercept:.3f} + {slope:.3f}x, r={r:.3f}'

    return {
        'Pearson r': pear_r,
        'Pearson p': pear_p,
        'Kendall tau': kend_tau,
        'Kendall p': kend_p,
        'Spearman roh': spear_roh,
        'Spearman p': spear_p,
        'Regression Slope': slope,
        'Intercept': intercept,
        'Regression line': reg_line
    }


def normal__info():
    return {

        'title': 'Normal Distribution Curve',
        'desc': 'Plot the normal distribution equation: '
                'y=(1 / (sqrt(2 * pi) * sigma)) * exp(-0.5 * (1 / sigma * (x - mu)) ** 2)',
        'outcol': ['chart__r']
    }


def normal(
    mean: qchar = '50.0',
    standard_devn: qchar = '10.0',
    start=0,
    stop=100,
    variations=100
):
    chart = pareq(
        x='x',
        y='(1 / (sqrt(2 * pi) * sigma)) * exp(-0.5 * (1 / sigma * (x - mu)) ** 2)',
        variable='x',
        variable_start=start,
        variable_stop=stop,
        variations=variations,
        x_label='x',
        y_label='y',
        title='Normal Distribution Curve',
        const_1='mu',
        const_1_part=mean,
        const_2='sigma',
        const_2_part=standard_devn,
        aspect=0
    )
    return {'chart': chart}


def volatility__info():
    return {
        'title': 'Volatility and Drift from Historical Values',
        'step2': [
            {
                'step': 'run',
                'func': 'monte_carlo', 'caption': 'Predict Future Values',
                'spec': {
                    'starting_price': 'Last Value',
                    'volatility': 'Volatility',
                    'drift': 'Drift'
                }
            },
        ]
    }


def volatility(historical_values: qtable = pd.DataFrame(
    {'Values': [100.8, 97.8, 102.0, 101.3, 98, 101.1, 103.5, 104.2, 101, 99, 99.5]})
):
    # https://quant.stackexchange.com/questions/35194/estimating-the-historical-drift-and-volatility
    values = historical_values['Values'].astype(float)
    changes = [math.log(values[i] / values[i - 1]) for i in range(1, len(values))]
    volatility = pstdev(changes)  # population stdev
    mean = fmean(changes)  # mean
    variance = volatility ** 2
    drift = mean + 0.5 * variance
    return {
        'Volatility': volatility,
        'Drift': drift,
        'Last Value': values[len(values) - 1]
    }


def monte_carlo__info():
    return {
        'title': 'Forecast Future Values of an Asset based on Monte Cralo Simulation'
    }


def monte_carlo(starting_price: float = 100, periods: int = 10, volatility: float = 0.05, drift: float = 0.0):
    periodic_returns = np.exp(drift + volatility * np.random.randn(periods))
    price_series = [starting_price]
    for i in range(1, periods):
        price_series.append(price_series[i - 1] * periodic_returns[i])
    return {'Forecast Values': price_series}
