# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

import pandas as pd

from qcore import qtbl
from calc import show_choice, get_shared_dataset
from calc.mod_result_post import postprocess_scenarios
from qutil import addcal_button, nzv
from calculators.all.analytics.what_if import SHARED_SCENARIO_TYPE, SHARED_SCENARIO_KEY


def scenario__modify(arg_name, arg_value, action):
    if arg_name != 'scenarios':
        return arg_value

    dataset_type = action.get('dataset_type')
    dataset_key = action.get('dataset_key')
    shared_record = get_shared_dataset(dataset_type=dataset_type, dataset_key=dataset_key)

    payload = shared_record.get('payload') if isinstance(shared_record, dict) else None
    if payload is None:
        raise Exception('No shared compare scenarios loaded. Open [compare], run it, then apply again.')

    if isinstance(payload, pd.DataFrame):
        payload = {
            'columns': list(payload.columns),
            'data': payload.where(pd.notna(payload), '').values.tolist(),
        }
    return payload


def scenario__info():
    return {
        'title': 'Scenario Analysis (Result Postprocessor)',
        'desc': (
            'Postprocess scenario results using delta, rank, filter, or '
            'weighted score analysis modes'
        ),
        'consumes_data': {
            'dataset_type': SHARED_SCENARIO_TYPE,
            'dataset_key': SHARED_SCENARIO_KEY,
        },
        'inserts': {
            'form_bottom': addcal_button('compare', 'What-If Scenario Comparison') +
                           '<button type="button" class="btn btn-info btncmd ml-2 cmd-compare" '
                           'name="apply_compare">Apply Compare</button>'
        },
        'showhide': {
            'mode': {
                'fields': [
                    'baseline_variation',
                    'delta_type',
                    'rank_by',
                    'rank_order',
                    'top_n',
                    'filter_by',
                    'filter_operator',
                    'filter_value',
                    'filter_value2',
                    'score_weights',
                    'score_directions',
                    'score_column',
                    'score_normalization',
                ],
                'callback': 'scenario_mode_showhide',
            }
        },
        'script': '''
        $(document).ready(function() {
            $(".cmd-compare").on("click", function() {
                updateAllData($(this));
                cid = getCidOf($(this));
                updateExtra(cid, {
                    "cmd":"__modify",
                    "args":["@scenarios"],
                    "kwargs":{"@scenarios":{
                        "dataset_type":"scenario_table",
                        "dataset_key":"compare_master"
                    }}
                });
                qcalc_FullFormSubmit(cid);
            });
        });

        function scenario_mode_showhide(mode){
            var vis = {
                delta: [1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                rank: [0, 0, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0],
                filter: [0, 0, 0, 0, 1, 1, 1, 1, 1, 0, 0, 0, 0],
                score: [0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 1, 1, 1],
            }
            return vis[mode] || [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
        }
        ''',
        'schema': {
            'mode': {
                'type': 'choice',
                'choices': {
                    'delta': 'Delta',
                    'rank': 'Rank',
                    'filter': 'Filter',
                    'score': 'Score',
                },
                'help_text': 'Postprocessing mode to apply on selected metrics',
            },
            'delta_type': {
                'type': 'choice',
                'choices': ['absolute', 'percent', 'index'],
            },
            'rank_order': {
                'type': 'choice',
                'choices': {'desc': 'High to Low', 'asc': 'Low to High'},
            },
            'filter_operator': {
                'type': 'choice',
                'choices': ['>=', '>', '<=', '<', '==', '!=', 'between', 'contains'],
            },
            'score_normalization': {
                'type': 'choice',
                'choices': ['minmax'],
            },
            'show': show_choice,
            'chart_type': {
                'type': 'choice',
                'choices': ['bars', 'hbars', 'lines', 'stack'],
            },
            'metric_columns': {
                'help_text': 'Optional metric columns to process, separated by comma',
            },
            'metric_units': {
                'help_text': 'Optional metric units to process, separated by comma',
            },
            'variable_columns': {
                'help_text': 'Optional non-metric input columns to keep unchanged (for example x,y,z)',
            },
            'baseline_variation': {
                'help_text': 'Baseline variation label used by delta mode (for example V1)',
            },
            'rank_by': {
                'help_text': 'Metric used for rank mode (defaults to first selected metric)',
            },
            'top_n': {
                'help_text': 'Optional maximum output rows after ranking/filtering/scoring',
            },
            'filter_by': {
                'help_text': 'Metric used for filter mode (defaults to first selected metric)',
            },
            'filter_value': {
                'help_text': 'Filter threshold value (used by filter mode)',
            },
            'filter_value2': {
                'help_text': 'Second threshold for between operator (filter mode)',
            },
            'score_weights': {
                'help_text': "Optional metric weights, e.g. 'Revenue:0.6, Risk:0.4'",
            },
            'score_directions': {
                'help_text': "Optional metric directions, e.g. 'Revenue:high, Risk:low'",
            },
            'score_column': {
                'help_text': 'Name of the computed score column for score mode',
            },
        },
        'tags': 'scenario, delta, rank, filter, score, decision support',
        'kins': 'compare, redo, monte_carlo, monte_carlo2',
        'layout': 'tb',
        'inp1': '1-5',
        'out1': '~chart',
    }


def scenario(
    scenarios: qtbl = {
        'columns': ['Variation', 'x', 'y', 'Result 1'],
        'data': [['V1', 1, 2, 3], ['V2', 2, 3, 4], ['V3', 3, 4, 5]],
    },
    mode='delta',
    metric_columns: str = '',
    metric_units: str = '',
    variable_columns: str = 'x, y',
    baseline_variation='V1',
    delta_type='absolute',
    rank_by: str = '',
    rank_order='desc',
    top_n: int = 0,
    filter_by: str = '',
    filter_operator='>=',
    filter_value='0',
    filter_value2='',
    score_weights: str = '',
    score_directions: str = '',
    score_column='Score',
    score_normalization='minmax',
    show='both',
    chart_title='Scenario Analysis',
    chart_type='bars',
):
    return postprocess_scenarios(
        scenario_table=scenarios,
        mode=mode,
        metric_columns=metric_columns,
        metric_units=metric_units,
        variable_columns=variable_columns,
        baseline_variation=baseline_variation,
        delta_type=delta_type,
        rank_by=rank_by,
        rank_order=rank_order,
        top_n=nzv(top_n),
        filter_by=filter_by,
        filter_operator=filter_operator,
        filter_value=filter_value,
        filter_value2=filter_value2,
        score_weights=score_weights,
        score_directions=score_directions,
        score_column=score_column,
        score_normalization=score_normalization,
        show=show,
        chart_title=chart_title,
        chart_type=chart_type,
    )
