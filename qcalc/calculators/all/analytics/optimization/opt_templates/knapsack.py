# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

import pandas as pd
import pulp

from ..opt_core import require_columns, safe_objective_value, solver, slack_table


def solve_knapsack(items, capacity_limit, decision_type, show_zero):
    require_columns(items, 'items', ['Item', 'Value', 'Weight'])

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
