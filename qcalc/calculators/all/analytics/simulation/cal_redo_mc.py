# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

import re

import numpy as np

from qcore import qchar, qcode, qtbl
from calc import require_columns, scalar_results, QResults, show_choice, RESULT_CELLS_HELP
from qutil import css2strs
from qvars import qc_gpref as gs


def monte_carlo__info():
    return {
        'title': 'Monte Carlo Simulation',
        'desc': 'Repeat a calculation many times while sampling a variable from a probability '
                'distribution, then chart the resulting distribution of outcomes',
        'schema': {
            'variation_target': {
                'type': 'choice',
                'choices': {'p': 'Parameters', 'v': 'Variables'},
                'help_text': 'Select what to vary: parameters of a function or variables of an expression',
            },
            'show': show_choice,
            'result_cells': {'help_text': RESULT_CELLS_HELP},
            'distribution': {'type': 'choice', 'choices': ['normal', 'uniform', 'triangular', 'lognormal']},
            'param1': {'help_text': 'normal: mean; uniform/triangular: low; lognormal: mu (of underlying normal)'},
            'param2': {'help_text': 'normal: stdev; uniform/triangular: high; lognormal: sigma (of underlying normal)'},
            'param3': {'help_text': 'triangular only: mode (most likely value); ignored otherwise, '
                                    'defaults to midpoint of param1/param2 if left blank'},
            # 'histo_column': {'required': True},
        },
        'layout': 'tb',
        'inp1': ['1-6'], #, '7-14'
        'out1': ['~chart'],
        'kins': 'redo',
        'tags': 'monte carlo, simulation',
    }


def monte_carlo(variation_target='v', xpr: qcode = "sine('x deg')", variable: qchar = 'x',
                distribution='normal', param1=0.0, param2=1.0, param3=None,
                trials: int = 100, bin_count=20, round_off=4,
                result_cells: str = '',
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
    results, xvals = scalar_results(
        xpr=xpr, variable=variable, var_vals=var_vals, variation_target=variation_target, cells=result_cells
    )

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
                ['Mean', float(np.mean(numeric_values))],
                ['Stdev', float(np.std(numeric_values, ddof=1)) if len(numeric_values) > 1 else 0.0],
                ['Min', float(np.min(numeric_values))],
                ['Max', float(np.max(numeric_values))],
                ['P5', float(np.percentile(numeric_values, 5))],
                ['P50', float(np.percentile(numeric_values, 50))],
                ['P95', float(np.percentile(numeric_values, 95))],
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
                'with an optional correlated pair, using an editable input table',
        'schema': {
            'variation_target': {
                'type': 'choice',
                'choices': {'p': 'Parameters', 'v': 'Variables'},
                'help_text': 'Select what to vary: parameters of a function or variables of an expression',
            },
            'show': show_choice,
            'result_cells': {'help_text': RESULT_CELLS_HELP},
            'inputs': {
                'help_text': (
                    'Use Distribution to choose the sampling shape.<br>'
                    '<b>normal:</b> Param 1 = <b>mean</b>, Param 2 = <b>stdev</b>, Param 3 = blank<br>'
                    '<b>uniform:</b> Param 1 = <b>low</b>, Param 2 = <b>high</b>, Param 3 = blank<br>'
                    '<b>triangular:</b> Param 1 = <b>low</b>, Param 2 = <b>high</b>, Param 3 = <b>mode</b><br>'
                    '<b>lognormal:</b> Param 1 = <b>mu</b>, Param 2 = <b>sigma</b>, Param 3 = blank<br>'
                ),
            },
            'correlated_variables': {
                'help_text': 'Optional pair, for example inflation, interest, separated by comma', },
            'correlation': {'help_text': 'Correlation for the optional pair, from -1 to 1'},
            # 'histo_column': {'required': True},
        },
        'layout': 'tb',
        'inp1': '1-5',
        'out1': '~chart',
        'kins': 'redo, monte_carlo',
        'tags': 'monte carlo, simulation, uncertainty, correlation',
    }


def monte_carlo2(
    variation_target='v',
    xpr: qcode = 'x + y',
    inputs: qtbl = {
        'columns': ['Variable', 'Distribution', 'Param 1', 'Param 2', 'Param 3'],
        'data': [['x', 'normal', 0, 1, ''], ['y', 'normal', 0, 1, '']],
    },
    trials: int = 100,
    bin_count=20,
    correlated_variables: str = '',
    correlation=0.0,
    result_cells: str = '',
    table_columns: str = '',
    table_units: str = '',
    histo_column: str = '',
    show='both',
    chart_title='Monte Carlo Simulation v2',
):
    inputs = inputs or {'columns': [], 'data': []}
    require_columns(
        inputs,
        'inputs',
        ['Variable', 'Distribution', 'Param 1', 'Param 2', 'Param 3'],
        columns_can_grow=False,
    )

    columns = list(inputs.get('columns', []))
    rows = list(inputs.get('data', []))
    col_index = {name: columns.index(name) for name in ['Variable', 'Distribution', 'Param 1', 'Param 2', 'Param 3']}

    names = []
    distributions = []
    param1_values = []
    param2_values = []
    param3_values = []
    for row in rows:
        values = list(row) if row is not None else []
        variable = values[col_index['Variable']] if len(values) > col_index['Variable'] else ''
        distribution = values[col_index['Distribution']] if len(values) > col_index['Distribution'] else ''
        param1 = values[col_index['Param 1']] if len(values) > col_index['Param 1'] else ''
        param2 = values[col_index['Param 2']] if len(values) > col_index['Param 2'] else ''
        param3 = values[col_index['Param 3']] if len(values) > col_index['Param 3'] else ''

        variable = str(variable).strip()
        distribution = str(distribution).strip().lower()

        if all(value in ('', None) for value in (variable, distribution, param1, param2, param3)):
            continue
        if not variable or not distribution or param1 in ('', None) or param2 in ('', None):
            raise Exception('Each populated input row must include Variable, Distribution, Param 1, and Param 2')
        if not re.fullmatch(r'[A-Za-z_]\w*', variable):
            raise Exception(f"'{variable}' is not a valid variable name")
        if variable in names:
            raise Exception('Variable names must be unique')
        if distribution not in ('normal', 'uniform', 'triangular', 'lognormal'):
            raise Exception('Unknown distribution; use normal, uniform, triangular, or lognormal')

        names.append(variable)
        distributions.append(distribution)
        param1_values.append(float(param1))
        param2_values.append(float(param2))
        param3_values.append(None if param3 in ('', None) else float(param3))

    if not names:
        raise Exception('Inputs table must contain at least one populated variable row')
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
        {name: str(float(samples[name][trial])) for name in names}
        for trial in range(trials)
    ]
    results, xvals = scalar_results(
        xpr=xpr, variable=', '.join(names), var_vals=trial_values, variation_target=variation_target,
        cells=result_cells
    )
    qr = QResults(results, xvals=xvals, variable=', '.join(names), table_columns=table_columns, table_units=table_units,
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
                ['Mean', float(np.mean(numeric_values))],
                ['Stdev', float(np.std(numeric_values, ddof=1)) if len(numeric_values) > 1 else 0.0],
                ['Min', float(np.min(numeric_values))],
                ['Max', float(np.max(numeric_values))],
                ['P5', float(np.percentile(numeric_values, 5))],
                ['P50', float(np.percentile(numeric_values, 50))],
                ['P95', float(np.percentile(numeric_values, 95))],
            ],
        },
        **histo
    }
