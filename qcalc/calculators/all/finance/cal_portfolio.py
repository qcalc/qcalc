# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

import pandas as pd
import numpy as np
from qcore import qfunc, QScreen
from calculators.all.general.file.cal_file import csv_reader
from scipy.optimize import minimize
from qutil import demo_url


def portf__input(_kwargs):
    return {
        'csv_file--csv_url': demo_url('closing.csv'),
    }


def portf__info():
    return {
        'title': 'Portfolio Optimization',
    }


def portf(csv_file: qfunc = csv_reader, target_return=0.3, show_input=False):
    df: pd.DataFrame = csv_file['table']
    df_orig = df

    # https://medium.com/@ethan.duong1120/python-powered-portfolio-optimization-achieving-target-returns-through-weight-optimization-fc5163e5c9c6

    def get_port_return(weights):
        """
        Returns the Annualised Expected Return of a portfolio.
        Annualises the return using the 'crude' method.
        """
        exp_ret_portfolio = np.dot(np.transpose(weights), df_mean)
        return exp_ret_portfolio

    # print(df.columns)
    df.set_index(df.columns[0], inplace=True)
    # print(df.columns)
    stocks = df.columns  # determine after setting index
    df = df.pct_change(1).dropna()
    df_mean = df.mean() * 250
    num_stocks = len(stocks)
    init_weights = [1 / num_stocks] * num_stocks
    # get_port_return(init_weights)
    bounds = tuple((0, 1) for i in range(num_stocks))
    cons = (
        # Sum of weights must equate to 1
        {'type': 'eq', 'fun': lambda w: np.sum(w) - 1},
        # Difference between expected return and target must be equal to 0.
        # {'type': 'eq', 'fun': lambda x: x.dot(df_mean) - target_return}
        # {'type': 'eq', 'fun': lambda x: np.dot(np.transpose(x), df_mean) - target_return}
        {'type': 'eq', 'fun': lambda x: get_port_return(x) - target_return}
    )
    results = minimize(
        fun=get_port_return,  # being the objective function
        x0=init_weights,  # being the initial guess
        # bounds: the first constraint that the weight of any
        # asset i must be between 0 and 1 inclusive
        bounds=bounds,
        # being the other 2 constraints
        constraints=cons
    )
    weights = results['x']
    df_weights = pd.DataFrame(data={'Stock': stocks, 'Weight': weights, 'Avg Annual Return': df_mean * 250})
    port_return = get_port_return(weights)
    out = QScreen()
    out.write(results)
    log = out.flush()
    # optimised_weights.index = stocks
    return {
        'Success': results['success'],
        'Expected Return': port_return,
        'Optimized Portfolio': df_weights,
        'Log': log,
        'Input Data': df_orig if show_input else 'Not Shown'
    }
