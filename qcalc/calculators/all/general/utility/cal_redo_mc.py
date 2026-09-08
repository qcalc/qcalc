# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

import re

import numpy as np

from qcore import qchar, qcode
from calc import scalar_results, QResults, show_choice
from qvars import qc_gpref as gs


def monte_carlo__info():
    return {
        'title': 'Monte Carlo Simulation',
        'desc': 'Repeat a calculation many times while sampling a variable from a probability '
                'distribution, then chart the resulting distribution of outcomes',
        'schema': {
            'show': show_choice,
            'distribution': {'type': 'choice', 'choices': ['normal', 'uniform', 'triangular', 'lognormal']},
            'param1': {'help_text': 'normal: mean; uniform/triangular: low; lognormal: mu (of underlying normal)'},
            'param2': {'help_text': 'normal: stdev; uniform/triangular: high; lognormal: sigma (of underlying normal)'},
            'param3': {'help_text': 'triangular only: mode (most likely value); ignored otherwise, '
                                    'defaults to midpoint of param1/param2 if left blank'},
        },
        'col': ['1-6', '7-14'],
        'outcol': ['chart__r'],
        'kins': 'redo',
        'tags': 'monte carlo, simulation',
    }


def monte_carlo(xpr: qcode = "sine('x deg')", variable: qchar = 'x',
                distribution='normal', param1=0.0, param2=1.0, param3=None,
                trials: int = 100, bin_count=20, round_off=4,
                table_columns: str = '', table_units: str = '', chart_column: str = '',
                show='both', chart_title='Monte Carlo Simulation'):
    # normal: param1=mean, param2=stdev
    # uniform: param1=low, param2=high
    # triangular: param1=low, param2=high, param3=mode (defaults to midpoint if not given)
    # lognormal: param1=mu, param2=sigma (of the underlying normal distribution)
    variable = (variable or '').strip()
    if not re.fullmatch(r'[A-Za-z_]\w*', variable):
        raise Exception(f"'{variable}' is not a valid variable name")
    if trials <= 0:
        raise Exception("Trials must be a positive integer")
    if trials > gs['range_limit']:
        raise Exception(f"Range limit of {gs['range_limit']} exceeded")

    if distribution == 'normal':
        if param2 < 0:
            raise Exception("Stdev (param2) cannot be negative for a normal distribution")
        samples = np.random.normal(param1, param2, trials)
    elif distribution == 'uniform':
        if param1 > param2:
            raise Exception("Low (param1) cannot exceed High (param2) for a uniform distribution")
        samples = np.random.uniform(param1, param2, trials)
    elif distribution == 'triangular':
        if param1 > param2:
            raise Exception("Low (param1) cannot exceed High (param2) for a triangular distribution")
        mode = (param1 + param2) / 2 if param3 is None else param3
        if not (param1 <= mode <= param2):
            raise Exception("Mode (param3) must be between Low (param1) and High (param2)")
        samples = np.random.triangular(param1, mode, param2, trials)
    elif distribution == 'lognormal':
        if param2 < 0:
            raise Exception("Sigma (param2) cannot be negative for a lognormal distribution")
        samples = np.random.lognormal(param1, param2, trials)
    else:
        raise Exception(f"Unknown distribution '{distribution}'")

    var_vals = [round(float(s), round_off) for s in samples]
    results, xvals = scalar_results(xpr=xpr, variable=variable, var_vals=var_vals)

    qr = QResults(results, xvals=xvals, variable=variable,
                  table_columns=table_columns, table_units=table_units, show=show)
    qr.setup_histo(chart_column=chart_column, bin_count=bin_count, chart_title=chart_title)

    # 'values' is always populated regardless of 'show', so the expensive
    # chart render is skipped whenever it isn't actually requested
    histo = qr.objects()
    numeric_values = histo.pop('values', [])
    failed = len(var_vals) - len(xvals)

    return {
        'trials_used': len(numeric_values),
        'trials_failed': failed,
        'mean': round(float(np.mean(numeric_values)), round_off),
        'stdev': round(float(np.std(numeric_values, ddof=1)), round_off) if len(numeric_values) > 1 else 0.0,
        'min': round(float(np.min(numeric_values)), round_off),
        'max': round(float(np.max(numeric_values)), round_off),
        'p5': round(float(np.percentile(numeric_values, 5)), round_off),
        'p50': round(float(np.percentile(numeric_values, 50)), round_off),
        'p95': round(float(np.percentile(numeric_values, 95)), round_off),
        **histo
    }
