# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

import math
from statistics import fmean, pstdev
import pandas as pd
from qcore import qtable, as_qtable, QChart
import numpy as np


def volatility__info():
    return {
        'title': 'Volatility and Drift from Historical Values',
        'kins': 'forecast_fv',
        'tags': 'forecasting',
        'step2': [
            {
                'step': 'run',
                'func': 'forecast_fv',
                'caption': 'Predict Future Values',
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
    historical_values = as_qtable(historical_values)
    # https://quant.stackexchange.com/questions/35194/estimating-the-historical-drift-and-volatility
    values = historical_values['Values'].astype(float)
    changes = [math.log(values[i] / values[i - 1]) for i in range(1, len(values))]
    volatility = pstdev(changes)  # population stdev
    mean = fmean(changes)  # mean
    variance = volatility ** 2
    drift = mean + 0.5 * variance

    chart = QChart()
    xvals = list(range(1, len(values) + 1))
    chart.render_lines(
        xvals=xvals,
        yvalsm=[values.tolist()],
        xlabel='Period Index',
        ylabels=['Historical Value'],
        ylabel='Value',
        title='Historical Values',
    )

    return {
        'Volatility': volatility,
        'Drift': drift,
        'Last Value': values[len(values) - 1],
        'Historical chart': chart,
    }


def forecast_fv__info():
    return {
        'title': 'Forecast Future Values of an Asset based on Volatility and Drift',
        'kins': 'volatility',
        'tags': 'forecasting',
    }


def forecast_fv(starting_price: float = 100, periods: int = 10, volatility: float = 0.05, drift: float = 0.0):
    periodic_returns = np.exp(drift + volatility * np.random.randn(periods))
    price_series = [starting_price]
    for i in range(1, periods):
        price_series.append(price_series[i - 1] * periodic_returns[i])

    chart = QChart()
    xvals = list(range(1, len(price_series) + 1))
    chart.render_lines(
        xvals=xvals,
        yvalsm=[price_series],
        xlabel='Forecast Step',
        ylabels=['Forecast Value'],
        ylabel='Value',
        title='Forecast Value Path',
    )

    return {
        'Forecast Values': price_series,
        'Forecast chart': chart,
    }
