# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

import re

import pandas as pd

from qcore import qcode, qtbl
from calc import QResults, scalar_results, show_choice, publish_shared_dataset, ResultCellsError, RESULT_CELLS_HELP
from qutil import QThread, parameter_values

SHARED_SCENARIO_TYPE = 'scenario_table'
SHARED_SCENARIO_KEY = 'compare_master'


def _df_to_qtbl(df: pd.DataFrame) -> dict:
    if df is None:
        return {'columns': [], 'data': []}
    # Keep plain scalar values for safe JSON-style transfer.
    clean_df = df.where(pd.notna(df), '')
    return {
        'columns': list(clean_df.columns),
        'data': clean_df.values.tolist(),
    }


# A relative value is a number followed by '%' or an operator in brackets: 5%, -5%, 5(%), 5(+), 2(x)
_RELATIVE_VALUE = re.compile(
    r'(?P<sign>[+-]?)(?P<number>(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?)'
    r'\s*(?:(?P<percent>%)|\(\s*(?P<op>[-+*/xX%])\s*\))'
)


def _relative_match(value):
    return _RELATIVE_VALUE.fullmatch(value.strip()) if isinstance(value, str) else None


def _apply_relative(match, base, variable, case_name):
    number = float(match.group('number'))
    if match.group('sign') == '-':
        number = -number
    op = '%' if match.group('percent') else match.group('op')
    if op == '%':
        # an explicit sign is a change (+10% -> x1.10), otherwise it is a share of the base (80% -> x0.80)
        result = base * (1 + number / 100) if match.group('sign') else base * number / 100
    elif op == '+':
        result = base + number
    elif op == '-':
        result = base - number
    elif op in ('*', 'x', 'X'):
        result = base * number
    else:
        if number == 0:
            raise Exception(f'{case_name}: cannot divide {variable} by zero')
        result = base / number
    return int(result) if result.is_integer() else result


def compare__info():
    return {
        'title': 'What-If Scenario Comparison',
        'desc': (
            'Evaluate an expression for multiple input scenarios, then compare '
            'the resulting values in a table and grouped bar chart. Values replace the '
            'current value; relative values are applied to the base (parameters: the value in the '
            'expression; variables: the first column): 5(+) 5(-) 2(*) 2(/) add/subtract/multiply/divide, '
            '+10% or -5% change, 80% or 80(%) share of the base'
        ),
        'schema': {
            'variation_target': {
                'label': 'Vary By',
                'type': 'choice',
                'choices': {'p': 'Parameters', 'v': 'Variables'},
                'help_text': 'Select what to vary: parameters of a function or variables of an expression',
            },
            'show': show_choice,
            'result_cells': {'help_text': RESULT_CELLS_HELP},
            'table_columns': {
                'help_text': 'Optional result columns to include, separated by comma',
            },
            'table_units': {
                'help_text': 'Optional result units to include, separated by comma',
            },
            'chart_columns': {
                'help_text': 'Optional result columns to chart, separated by comma',
            },
            'chart_units': {
                'help_text': 'Optional result units to chart, separated by comma',
            },
        },
        'provides_data': {
            'dataset_type': SHARED_SCENARIO_TYPE,
            'dataset_key': SHARED_SCENARIO_KEY,
        },
        'step2': [
            {
                'step': 'run',
                'func': 'scenario',
                'caption': 'Evaluate Scenarios',
                'spec': {'scenarios': 'table'},
            },
        ],
        'kins': 'redo, monte_carlo',
        'tags': 'comparison, discrete values, parameter sweep, sensitivity',
    }


def compare(
    variation_target='v',
    xpr: qcode = 'x + y',
    inputs: qtbl = {
        'columns': ['Variable', 'V1', 'V2', 'V3'],
        'data': [['x', 1, 2, 3], ['y', 2, 3, 4]],
    },
    result_cells: str = '',
    table_columns: str = '',
    table_units: str = '',
    chart_columns: str = '',
    chart_units: str = '',
    chart_title: str = 'Discrete Comparison',
    show='both',
):
    columns = inputs.get('columns', [])
    rows = inputs.get('data', [])

    variables = [str(row[0]).strip() for row in rows]
    if any(not re.fullmatch(r'[A-Za-z_]\w*', variable) for variable in variables):
        raise Exception('Each Variable must be a valid variable name')
    if len(set(variables)) != len(variables):
        raise Exception('Variable names must be unique')

    case_names = columns[1:]
    trial_values = []
    trial_inputs = []
    # relative values (5%, 5(+), ...) apply to a base: the current parameter values in the
    # expression, or for variables the first populated column
    base_values = {k.lower(): v for k, v in parameter_values(xpr).items()} if variation_target == 'p' else None
    for case_index, case_name in enumerate(case_names, start=1):
        values = [row[case_index] for row in rows]
        if all(value in ('', None) for value in values):
            continue
        if any(value in ('', None) for value in values):
            raise Exception(f'{case_name} must contain a value for every variable')

        if base_values is None:
            if any(_relative_match(value) for value in values):
                raise Exception(f'{case_name} is the base column; it must contain plain values, not relative ones')
            base_values = {}
            for variable, value in zip(variables, values):
                try:
                    base_values[variable.lower()] = float(value)
                except (TypeError, ValueError):
                    pass
        else:
            resolved = []
            for variable, value in zip(variables, values):
                match = _relative_match(value)
                if match:
                    base = base_values.get(variable.lower())
                    if base is None:
                        raise Exception(f'{case_name}: {variable} has no numeric base value for {value}')
                    value = _apply_relative(match, base, variable, case_name)
                resolved.append(value)
            values = resolved

        trial_values.append({variable: str(value) for variable, value in zip(variables, values)})
        trial_inputs.append((case_name, values))

    if not trial_values:
        raise Exception('Input table must contain at least one populated value column')

    successful_inputs = []
    results = []
    successful_cases = []
    last_error = None
    for trial_value, (case_name, values) in zip(trial_values, trial_inputs):
        try:
            row_results, _ = scalar_results(
                xpr=xpr,
                variable=','.join(columns),
                var_vals=[trial_value],
                variation_target=variation_target,
                cells=result_cells,
            )
        except ResultCellsError:
            raise
        except Exception as e:
            last_error = e
            continue
        successful_cases.append(case_name)
        successful_inputs.append(values)
        results.append(row_results[0])
    if not results:
        raise Exception(str(last_error or 'No numeric results were produced; check the expression'))
    case_labels = successful_cases

    qr = QResults(
        results,
        xvals=case_labels,
        variable='',
        table_columns=table_columns,
        table_units=table_units,
        show=show,
    )
    qr.setup_chart(
        chart_columns=chart_columns,
        chart_units=chart_units,
        chart_title=chart_title,
        chart_type='bars',
    )
    output = qr.objects()
    if 'table' in output:
        result_table = output['table'].drop(columns=['X'])
        output['table'] = pd.concat(
            [
                pd.DataFrame({
                    'Variation': successful_cases,
                    **{
                        variable: [values[index] for values in successful_inputs]
                        for index, variable in enumerate(variables)
                    },
                }).reset_index(drop=True),
                result_table.reset_index(drop=True),
            ],
            axis=1,
        )

    request = QThread.get_req()
    if request is not None and hasattr(request, 'session'):
        publish_shared_dataset(
            dataset_type=SHARED_SCENARIO_TYPE,
            dataset_key=SHARED_SCENARIO_KEY,
            payload=_df_to_qtbl(output.get('table')),
            producer_func='compare',
        )
    return output
