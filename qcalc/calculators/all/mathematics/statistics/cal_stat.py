# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

from statistics import fmean, median, mode, stdev, pstdev, \
    geometric_mean, harmonic_mean, median_low, median_high, variance, pvariance, quantiles
import pandas as pd
import scipy.stats as ss
from qutil import css2floats
from qcore import qchar
from calculators.all.general.chart import pareq


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
    }


# https://docs.python.org/3/library/statistics.html
def stat(numbers='1,2,3,4,5', weights=''):
    nums = css2floats(numbers)
    avg = fmean(nums)
    havg = harmonic_mean(nums)
    if weights != '':
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
    xnums = css2floats(x_numbers)
    x = pd.Series(xnums)

    ynums = css2floats(y_numbers)
    y = pd.Series(ynums)

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
