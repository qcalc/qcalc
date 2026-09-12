# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

import re

import numpy as np

from qcore import qchar, qcode, qtexta
from calc import scalar_results, QResults, show_choice
from qutil import css2floats, css2strs
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
            # 'histo_column': {'required': True},
        },
        'inp1': ['1-6'], #, '7-14'
        'out1': ['~chart'],
        'layout': 't2b2',
        'kins': 'redo',
        'tags': 'monte carlo, simulation',
    }


def monte_carlo(xpr: qcode = "sine('x deg')", variable: qchar = 'x',
                distribution='normal', param1=0.0, param2=1.0, param3=None,
                trials: int = 100, bin_count=20, round_off=4,
                table_columns: str = '', table_units: str = '', histo_column: str = '',
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
    qr.setup_histo(histo_column=histo_column, bin_count=bin_count, chart_title=chart_title)

    # 'values' is always populated regardless of 'show', so the expensive
    # chart render is skipped whenever it isn't actually requested
    histo = qr.objects()
    numeric_values = histo.pop('values', [])
    failed = len(var_vals) - len(xvals)

    return {
        'Statistics': {
            'columns': ['Metric', 'Value'],
            'data': [
                ['Trials used', len(numeric_values)],
                ['Trials failed', failed],
                ['Mean', round(float(np.mean(numeric_values)), round_off)],
                ['Stdev', round(float(np.std(numeric_values, ddof=1)), round_off)
                 if len(numeric_values) > 1 else 0.0],
                ['Min', round(float(np.min(numeric_values)), round_off)],
                ['Max', round(float(np.max(numeric_values)), round_off)],
                ['P5', round(float(np.percentile(numeric_values, 5)), round_off)],
                ['P50', round(float(np.percentile(numeric_values, 50)), round_off)],
                ['P95', round(float(np.percentile(numeric_values, 95)), round_off)],
            ],
        },
        **histo
    }


def _mc2_sample(distribution, param1, param2, param3, trials):
    if distribution == 'normal':
        if param2 < 0:
            raise Exception('Stdev cannot be negative for a normal distribution')
        return np.random.normal(param1, param2, trials)
    if distribution == 'uniform':
        if param1 > param2:
            raise Exception('Low cannot exceed High for a uniform distribution')
        return np.random.uniform(param1, param2, trials)
    if distribution == 'triangular':
        if param1 > param2:
            raise Exception('Low cannot exceed High for a triangular distribution')
        mode = (param1 + param2) / 2 if param3 is None else param3
        if not (param1 <= mode <= param2):
            raise Exception('Mode must be between Low and High')
        return np.random.triangular(param1, mode, param2, trials)
    if distribution == 'lognormal':
        if param2 < 0:
            raise Exception('Sigma cannot be negative for a lognormal distribution')
        return np.random.lognormal(param1, param2, trials)
    raise Exception(f"Unknown distribution '{distribution}'")


def monte_carlo2__info():
    return {
        'title': 'Monte Carlo Simulation 2',
        'desc': 'Repeat a calculation while sampling multiple variables independently, '
                'with an optional correlated pair',
        'schema': {
            'show': show_choice,
            'distributions': {
                'help_text': 'One distribution per variable, separated by comma\n options: normal, uniform, triangular, lognormal', },
            'param1s': {'help_text': 'One mean/low/mu value per variable, separated by comma', },
            'param2s': {'help_text': 'One stdev/high/sigma value per variable, separated by comma', },
            'param3s': {'help_text': 'Optional triangular mode values, separated by comma', },
            'correlated_variables': {
                'help_text': 'Optional pair, for example inflation, interest, separated by comma', },
            'correlation': {'help_text': 'Correlation for the optional pair, from -1 to 1'},
            # 'histo_column': {'required': True},
        },
        'col': ['1-6', '7-16'],
        'outcol': ['chart__r', 'table__r'],
        'kins': 'redo, monte_carlo',
        'tags': 'monte carlo, simulation, uncertainty, correlation',
    }


def monte_carlo2(
    xpr: qcode = 'x + y',
    variables: qtexta = 'x, y',
    distributions: str = 'normal, normal',
    param1s: str = '0, 0',
    param2s: str = '1, 1',
    param3s: str = '',
    trials: int = 100,
    bin_count=20,
    round_off=4,
    correlated_variables: str = '',
    correlation=0.0,
    table_columns: str = '',
    table_units: str = '',
    histo_column: str = '',
    show='both',
    chart_title='Monte Carlo Simulation v2',
):
    names = css2strs(variables)
    distributions = css2strs(distributions.lower())
    param1_values = css2floats(param1s)
    param2_values = css2floats(param2s)
    param3_strings = css2strs(param3s)

    if not names or len(set(names)) != len(names):
        raise Exception('Variables must contain one or more unique variable names')
    if any(not re.fullmatch(r'[A-Za-z_]\w*', name) for name in names):
        raise Exception('Each variable must be a valid variable name')
    count = len(names)
    if not all(len(values) == count for values in
               (distributions, param1_values, param2_values)):
        raise Exception('Variables, distributions, param1s, and param2s must have the same length')
    if param3_strings and len(param3_strings) not in (1, count):
        raise Exception('param3s must be blank, one value, or one value per variable')
    if param3_strings and len(param3_strings) == 1 and count > 1:
        param3_strings *= count
    param3_values = [None if value == '' else float(value) for value in param3_strings]
    param3_values.extend([None] * (count - len(param3_values)))
    if any(distribution not in ('normal', 'uniform', 'triangular', 'lognormal')
           for distribution in distributions):
        raise Exception('Unknown distribution; use normal, uniform, triangular, or lognormal')
    if trials <= 0:
        raise Exception('Trials must be a positive integer')
    if trials > gs['range_limit']:
        raise Exception(f"Range limit of {gs['range_limit']} exceeded")
    correlation = 0.0 if correlation in ('', None) else float(correlation)
    if not -1.0 <= correlation <= 1.0:
        raise Exception('Correlation must be between -1 and 1')

    correlated_names = css2strs(correlated_variables)
    if correlated_names and len(correlated_names) != 2:
        raise Exception('correlated_variables must contain exactly two variable names')
    if any(name not in names for name in correlated_names):
        raise Exception('Correlated variables must be included in variables')
    pair_indexes = [names.index(name) for name in correlated_names]
    if any(distributions[index] != 'normal' for index in pair_indexes):
        raise Exception('The correlated pair must use the normal distribution')

    samples = {}
    for index, name in enumerate(names):
        if index not in pair_indexes:
            samples[name] = _mc2_sample(
                distributions[index], param1_values[index], param2_values[index],
                param3_values[index], trials
            )
    if pair_indexes:
        first, second = pair_indexes
        z1 = np.random.normal(0.0, 1.0, trials)
        z2 = np.random.normal(0.0, 1.0, trials)
        correlated_z2 = correlation * z1 + np.sqrt(1.0 - correlation ** 2) * z2
        samples[names[first]] = param1_values[first] + param2_values[first] * z1
        samples[names[second]] = param1_values[second] + param2_values[second] * correlated_z2

    trial_values = [
        {name: str(round(float(samples[name][trial]), round_off)) for name in names}
        for trial in range(trials)
    ]
    results, xvals = scalar_results(xpr=xpr, variable=variables, var_vals=trial_values)
    qr = QResults(results, xvals=xvals, variable=variables, table_columns=table_columns, table_units=table_units,
                  show=show)
    qr.setup_histo(histo_column=histo_column, bin_count=bin_count, chart_title=chart_title)
    histo = qr.objects()
    numeric_values = histo.pop('values', [])
    failed = trials - len(numeric_values)

    return {
        'Statistics': {
            'columns': ['Metric', 'Value'],
            'data': [
                ['Trials used', len(numeric_values)],
                ['Trials failed', failed],
                ['Mean', round(float(np.mean(numeric_values)), round_off)],
                ['Stdev', round(float(np.std(numeric_values, ddof=1)), round_off)
                 if len(numeric_values) > 1 else 0.0],
                ['Min', round(float(np.min(numeric_values)), round_off)],
                ['Max', round(float(np.max(numeric_values)), round_off)],
                ['P5', round(float(np.percentile(numeric_values, 5)), round_off)],
                ['P50', round(float(np.percentile(numeric_values, 50)), round_off)],
                ['P95', round(float(np.percentile(numeric_values, 95)), round_off)],
            ],
        },
        **histo
    }
