# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

import re

import numpy as np
import pandas as pd

from qcore import qchar, qcode, qtbl, QChart
from calc import require_columns, scalar_results, QResults, show_choice, RESULT_CELLS_HELP, result_values, ResultCellsError
from qutil import css2strs
from qvars import qc_gpref as gs

MC_DEFAULT_XPR = '(price - unit_cost) * demand - fixed_cost'
MC_DEFAULT_INPUTS = {
    'columns': ['Variable', 'Distribution', 'Param 1', 'Param 2', 'Param 3'],
    'data': [
        ['price', 'normal', 120, 8, ''],
        ['unit_cost', 'normal', 70, 6, ''],
        ['demand', 'triangular', 700, 1300, 1000],
        ['fixed_cost', 'normal', 25000, 3000, ''],
    ],
}


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


def _mc2_sample(distribution, param1, param2, param3, trials, rng=None):
    random = rng if rng is not None else np.random
    if distribution == 'normal':
        if param2 < 0:
            raise Exception('Stdev cannot be negative for a normal distribution')
        return random.normal(param1, param2, trials)
    if distribution == 'uniform':
        if param1 > param2:
            raise Exception('Low cannot exceed High for a uniform distribution')
        return random.uniform(param1, param2, trials)
    if distribution == 'triangular':
        if param1 > param2:
            raise Exception('Low cannot exceed High for a triangular distribution')
        mode = (param1 + param2) / 2 if param3 is None else param3
        if not (param1 <= mode <= param2):
            raise Exception('Mode must be between Low and High')
        return random.triangular(param1, mode, param2, trials)
    if distribution == 'lognormal':
        if param2 < 0:
            raise Exception('Sigma cannot be negative for a lognormal distribution')
        return random.lognormal(param1, param2, trials)
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
    xpr: qcode = MC_DEFAULT_XPR,
    inputs: qtbl = MC_DEFAULT_INPUTS,
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


def _normalize_name(value: str) -> str:
    return re.sub(r'[^a-z0-9]+', '', str(value).lower())


def _numeric_result_map(result):
    source = dict(result) if isinstance(result, dict) else result
    values, _ = result_values(source)
    numeric = {}
    for key, value in values.items():
        if isinstance(value, bool):
            continue
        if isinstance(value, (int, float, np.integer, np.floating)):
            number = float(value)
            if np.isfinite(number):
                numeric[key] = number
    return numeric


def _resolve_target_key(target_column, keys):
    key_list = list(keys)
    if not key_list:
        raise Exception('No numeric target output column was produced')
    if target_column:
        target_norm = _normalize_name(target_column)
        for key in key_list:
            if _normalize_name(key) == target_norm:
                return key
        available = ', '.join(key_list)
        raise Exception(f"target_column '{target_column}' was not found. Available: {available}")
    if len(key_list) == 1:
        return key_list[0]
    available = ', '.join(key_list)
    raise Exception(
        "Multiple numeric output columns were produced; specify target_column. "
        f"Available: {available}"
    )


def _safe_corrcoef(x, y):
    if len(x) == 0 or len(y) == 0:
        return 0.0
    sx = float(np.std(x, ddof=1)) if len(x) > 1 else 0.0
    sy = float(np.std(y, ddof=1)) if len(y) > 1 else 0.0
    if sx == 0.0 or sy == 0.0:
        return 0.0
    return float(np.corrcoef(x, y)[0, 1])


def _residuals(y, x):
    if x.size == 0:
        return y - np.mean(y)
    design = np.column_stack([np.ones(len(y)), x])
    beta = np.linalg.lstsq(design, y, rcond=None)[0]
    return y - design @ beta


def _src_scores(x, y):
    if len(y) < 2:
        raise Exception('At least two successful trials are required for sensitivity analysis')
    y_std = float(np.std(y, ddof=1))
    if y_std == 0:
        raise Exception('Target output has zero variance; sensitivity cannot be computed')
    x_mean = np.mean(x, axis=0)
    x_std = np.std(x, axis=0, ddof=1)
    xz = np.zeros_like(x, dtype=float)
    nonzero = x_std > 0
    xz[:, nonzero] = (x[:, nonzero] - x_mean[nonzero]) / x_std[nonzero]
    yz = (y - float(np.mean(y))) / y_std
    beta = np.linalg.lstsq(xz, yz, rcond=None)[0]
    yhat = xz @ beta
    sst = float(np.sum((yz - np.mean(yz)) ** 2))
    ssr = float(np.sum((yz - yhat) ** 2))
    r2 = 1.0 - (ssr / sst) if sst > 0 else 0.0
    return beta, max(0.0, min(1.0, r2))


def _prcc_scores(x, y):
    x_rank = np.column_stack([pd.Series(x[:, i]).rank(method='average').to_numpy(dtype=float)
                              for i in range(x.shape[1])])
    y_rank = pd.Series(y).rank(method='average').to_numpy(dtype=float)
    scores = []
    for index in range(x.shape[1]):
        others = [i for i in range(x.shape[1]) if i != index]
        z = x_rank[:, others] if others else np.empty((len(y_rank), 0))
        rx = _residuals(x_rank[:, index], z)
        ry = _residuals(y_rank, z)
        scores.append(_safe_corrcoef(rx, ry))
    return np.array(scores, dtype=float)


def sensitivity__info():
    return {
        'title': 'Sensitivity Analysis',
        'desc': 'Estimate input importance using standardized regression coefficients (SRC) '
                'and/or partial rank correlation coefficients (PRCC) from Monte Carlo samples',
        'schema': {
            'variation_target': {
                'type': 'choice',
                'choices': {'p': 'Parameters', 'v': 'Variables'},
                'help_text': 'Select what to vary: parameters of a function or variables of an expression',
            },
            'method': {'type': 'choice', 'choices': {'src': 'SRC', 'prcc': 'PRCC', 'both': 'Both'}},
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
            'target_column': {'help_text': 'Output column to analyze when expression returns multiple numeric columns'},
            'correlated_variables': {
                'help_text': 'Optional pair, for example inflation, interest, separated by comma', },
            'correlation': {'help_text': 'Correlation for the optional pair, from -1 to 1'},
        },
        'layout': 'tb',
        'inp1': '1-5',
        'out1': '~chart',
        'kins': 'monte_carlo2, scenario',
        'tags': 'sensitivity, src, prcc, monte carlo, uncertainty',
    }


def sensitivity(
    variation_target='v',
    xpr: qcode = MC_DEFAULT_XPR,
    inputs: qtbl = MC_DEFAULT_INPUTS,
    trials: int = 500,
    method='both',
    target_column: str = '',
    correlated_variables: str = '',
    correlation=0.0,
    top_n: int = 0,
    random_seed=None,
    result_cells: str = '',
    show_values=True,
    show='both',
    chart_title='Sensitivity Analysis',
):
    inputs = inputs or {'columns': [], 'data': []}
    require_columns(
        inputs,
        'inputs',
        ['Variable', 'Distribution', 'Param 1', 'Param 2', 'Param 3'],
        columns_can_grow=False,
    )
    if method not in ('src', 'prcc', 'both'):
        raise Exception("method must be one of: src, prcc, both")

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

    seed = None if random_seed in ('', None) else int(random_seed)
    rng = np.random.default_rng(seed) if seed is not None else None
    samples = {}
    for index, name in enumerate(names):
        if index not in pair_indexes:
            samples[name] = _mc2_sample(
                distributions[index], param1_values[index], param2_values[index], param3_values[index], trials, rng=rng
            )
    if pair_indexes:
        first, second = pair_indexes
        random = rng if rng is not None else np.random
        z1 = random.normal(0.0, 1.0, trials)
        z2 = random.normal(0.0, 1.0, trials)
        correlated_z2 = correlation * z1 + np.sqrt(1.0 - correlation ** 2) * z2
        samples[names[first]] = param1_values[first] + param2_values[first] * z1
        samples[names[second]] = param1_values[second] + param2_values[second] * correlated_z2

    successful_inputs = []
    target_values = []
    used_target_key = None
    failed = 0
    variable_expr = ', '.join(names)
    for trial in range(trials):
        trial_value = {name: str(float(samples[name][trial])) for name in names}
        try:
            row_results, _ = scalar_results(
                xpr=xpr, variable=variable_expr, var_vals=[trial_value], variation_target=variation_target, cells=result_cells
            )
        except ResultCellsError:
            raise
        except Exception:
            failed += 1
            continue
        if not row_results:
            failed += 1
            continue

        numeric_map = _numeric_result_map(row_results[0])
        if not numeric_map:
            failed += 1
            continue
        if used_target_key is None:
            used_target_key = _resolve_target_key(target_column, numeric_map.keys())
        if used_target_key not in numeric_map:
            failed += 1
            continue
        successful_inputs.append([float(samples[name][trial]) for name in names])
        target_values.append(float(numeric_map[used_target_key]))

    if not target_values:
        raise Exception('No successful numeric target results were produced; check expression and target_column')
    x = np.array(successful_inputs, dtype=float)
    y = np.array(target_values, dtype=float)

    src_values = None
    prcc_values = None
    src_r2 = None
    if method in ('src', 'both'):
        src_values, src_r2 = _src_scores(x, y)
    if method in ('prcc', 'both'):
        prcc_values = _prcc_scores(x, y)

    rows = []
    for index, name in enumerate(names):
        src = float(src_values[index]) if src_values is not None else None
        prcc = float(prcc_values[index]) if prcc_values is not None else None
        if method == 'src':
            primary = src
        elif method == 'prcc':
            primary = prcc
        else:
            primary = prcc if prcc is not None else src
        rows.append({
            'Variable': name,
            'SRC': src,
            'SRC Abs': abs(src) if src is not None else None,
            'PRCC': prcc,
            'PRCC Abs': abs(prcc) if prcc is not None else None,
            'Primary Score': primary,
            'Primary Abs': abs(primary) if primary is not None else 0.0,
            'Direction': 'positive' if (primary or 0) > 0 else ('negative' if (primary or 0) < 0 else 'neutral'),
        })
    table = pd.DataFrame(rows)
    table = table.sort_values(by='Primary Abs', ascending=False).reset_index(drop=True)
    table['Rank'] = table.index + 1
    if src_values is not None:
        table['SRC Rank'] = table['SRC Abs'].rank(method='min', ascending=False).astype(int)
    if prcc_values is not None:
        table['PRCC Rank'] = table['PRCC Abs'].rank(method='min', ascending=False).astype(int)
    if top_n and top_n > 0:
        table = table.head(int(top_n)).reset_index(drop=True)

    chart = None
    if show in ('both', 'chart'):
        display_scores = table['Primary Score'].fillna(0.0).to_numpy(dtype=float)
        low_vals = np.minimum(display_scores, 0.0)
        high_vals = np.maximum(display_scores, 0.0)
        chart = QChart(xtype=str)
        chart.render_tornado_chart(
            labels=table['Variable'].tolist(),
            low_vals=low_vals.tolist(),
            high_vals=high_vals.tolist(),
            xlabel='Sensitivity score',
            ylabel='Variable',
            title=chart_title,
            show_values=bool(show_values),
        )

    summary_rows = [
        ['Method', method.upper()],
        ['Target', used_target_key],
        ['Trials requested', trials],
        ['Trials used', len(target_values)],
        ['Trials failed', failed],
    ]
    if src_r2 is not None:
        summary_rows.append(['SRC R2', float(src_r2)])
    summary = {'columns': ['Metric', 'Value'], 'data': summary_rows}

    output = {'Summary': summary}
    if show in ('both', 'table'):
        output['table'] = table
    if show in ('both', 'chart'):
        output['chart'] = chart
    return output
