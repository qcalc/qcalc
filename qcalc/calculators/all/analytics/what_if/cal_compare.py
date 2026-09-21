# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

import re

import pandas as pd

from qcore import qcode, qtbl
from calc import QResults, scalar_results, show_choice, publish_shared_dataset
from qutil import QThread

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


def compare__info():
    return {
        'title': 'What-If Scenario Comparison',
        'desc': (
            'Evaluate an expression for multiple input scenarios, then compare '
            'the resulting values in a table and grouped bar chart'
        ),
        'schema': {
            'variation_target': {
                'label': 'Vary By',
                'type': 'choice',
                'choices': {'p': 'Parameters', 'v': 'Variables'},
                'help_text': 'Select what to vary: parameters of a function or variables of an expression',
            },
            'show': show_choice,
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
    for case_index, case_name in enumerate(case_names, start=1):
        values = [row[case_index] for row in rows]
        if all(value in ('', None) for value in values):
            continue
        if any(value in ('', None) for value in values):
            raise Exception(f'{case_name} must contain a value for every variable')
        trial_values.append({variable: str(value) for variable, value in zip(variables, values)})
        trial_inputs.append((case_name, values))

    if not trial_values:
        raise Exception('Input table must contain at least one populated value column')

    successful_inputs = []
    results = []
    successful_cases = []
    for trial_value, (case_name, values) in zip(trial_values, trial_inputs):
        try:
            row_results, _ = scalar_results(
                xpr=xpr,
                variable=','.join(columns),
                var_vals=[trial_value],
                variation_target=variation_target,
            )
        except Exception:
            continue
        successful_cases.append(case_name)
        successful_inputs.append(values)
        results.append(row_results[0])
    if not results:
        raise Exception('No numeric results were produced; check the expression')
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
