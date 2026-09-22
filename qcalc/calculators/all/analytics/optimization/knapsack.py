# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

import pandas as pd
import pulp
from qcore import as_qtable, qtable
from qutil.mod_runtime_validate import validate_schema_if_needed

from .cal_optima import field_show_zero, table_items
from .opt_core import safe_objective_value, solver, slack_table


def optima_knapsack(
    items: qtable,
    capacity_limit,
    decision_type,
    show_zero,
):
    validate_schema_if_needed('optima_knapsack')
    items = as_qtable(items)

    item_list = items['Item'].astype(str).tolist()
    value = dict(zip(items['Item'].astype(str), pd.to_numeric(items['Value'])))
    weight = dict(zip(items['Item'].astype(str), pd.to_numeric(items['Weight'])))
    max_qty = (
        dict(zip(items['Item'].astype(str), pd.to_numeric(items['Max Qty'])))
        if 'Max Qty' in items.columns else {item: 1 for item in item_list}
    )
    capacity = float(capacity_limit)

    prob = pulp.LpProblem('optima_knapsack', pulp.LpMaximize)
    cat = pulp.LpBinary if decision_type == 'binary' else pulp.LpInteger
    x = {}
    for item in item_list:
        upper = 1 if decision_type == 'binary' else int(max(0, round(float(max_qty[item]))))
        x[item] = pulp.LpVariable(f'Select_{item}', lowBound=0, upBound=upper, cat=cat)

    prob += pulp.lpSum(float(value[item]) * x[item] for item in item_list)
    prob += pulp.lpSum(float(weight[item]) * x[item] for item in item_list) <= capacity, 'capacity'

    prob.solve(solver())
    status = pulp.LpStatus[prob.status]

    decision_rows = []
    total_weight = 0.0
    total_value = 0.0
    for item in item_list:
        qty = float(x[item].value() or 0)
        w = float(weight[item])
        v = float(value[item])
        total_weight += w * qty
        total_value += v * qty
        if show_zero or qty > 0:
            decision_rows.append({
                'Item': item,
                'Selected Qty': round(qty, 6),
                'Unit Value': round(v, 6),
                'Unit Weight': round(w, 6),
                'Value Contribution': round(v * qty, 6),
                'Weight Contribution': round(w * qty, 6),
            })

    return {
        'Summary': pd.DataFrame([{
            'Model': 'Knapsack',
            'Status': status,
            'Objective': safe_objective_value(prob),
            'Total Value': round(total_value, 6),
            'Total Weight': round(total_weight, 6),
            'Capacity Limit': round(capacity, 6),
        }]),
        'Decision Table': pd.DataFrame(decision_rows),
        'Constraint Slack': slack_table(prob),
    }


def optima_knapsack__info():
    return {
        'title': 'Optimization: Knapsack',
        'desc': (
            'Maximize value under a capacity limit with binary or integer item decisions.'
            ' Use this for budget selection, portfolio picking, and constrained mix-selection problems.'
        ),
        'calculate': 'Solve',
        'schema': {
            'items': table_items('items'),
            'capacity_limit': {
                'initial': 5,
                'help_text': 'Total capacity limit; use the same unit basis as Weight (for example kg, volume, hours, or budget units).',
            },
            'decision_type': {
                'type': 'choice',
                'choices': {'binary': 'Binary (0/1)', 'integer': 'Integer (0..Max Qty)'},
                'initial': 'binary',
                'help_text': 'Choose binary (0/1) or integer quantities up to Max Qty.',
            },
            'show_zero': field_show_zero(),
        },
        'layout': 'lr',
        'out1': ['Summary', 'Decision Table'],
        'tags': 'optimization, knapsack, integer programming',
    }





