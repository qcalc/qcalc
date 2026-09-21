# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

import pandas as pd
import pulp

from ..opt_core import require_columns, safe_objective_value, solver, slack_table


_ALLOWED_RULE_TYPES = {'depends_on', 'excludes'}


def _to_float_or_none(value):
    if value in ('', None):
        return None
    return float(value)


def _to_int_or_default(value, default=0):
    if value in ('', None):
        return int(default)
    return int(value)


def solve_project(
    projects,
    project_rules,
    project_budget_limit,
    project_resource_limit,
    project_max_selected,
    project_min_selected,
    show_zero,
):
    require_columns(projects, 'projects', ['Project', 'Value', 'Cost'])

    prj = projects.copy()
    prj['Project'] = prj['Project'].astype(str)
    project_list = prj['Project'].tolist()
    if not project_list:
        raise Exception('projects must contain at least one row')
    if prj['Project'].duplicated().any():
        raise Exception('projects contains duplicate Project values')

    value = dict(zip(prj['Project'], pd.to_numeric(prj['Value'])))
    cost = dict(zip(prj['Project'], pd.to_numeric(prj['Cost'])))

    has_resource = 'Resource' in prj.columns
    resource = dict(zip(prj['Project'], pd.to_numeric(prj['Resource']))) if has_resource else {p: 0.0 for p in project_list}

    has_must_do = 'Must Do' in prj.columns
    must_do = (
        dict(zip(prj['Project'], pd.to_numeric(prj['Must Do'], errors='coerce').fillna(0)))
        if has_must_do else {p: 0 for p in project_list}
    )

    budget_limit = _to_float_or_none(project_budget_limit)
    resource_limit = _to_float_or_none(project_resource_limit)
    max_selected = _to_int_or_default(project_max_selected, 0)
    min_selected = _to_int_or_default(project_min_selected, 0)

    prob = pulp.LpProblem('optima_project', pulp.LpMaximize)
    x = pulp.LpVariable.dicts('Select', project_list, lowBound=0, upBound=1, cat=pulp.LpBinary)

    prob += pulp.lpSum(float(value[p]) * x[p] for p in project_list)

    if budget_limit is not None:
        prob += pulp.lpSum(float(cost[p]) * x[p] for p in project_list) <= budget_limit, 'budget_limit'

    if resource_limit is not None:
        if not has_resource:
            raise Exception("projects must include 'Resource' when project_resource_limit is used")
        prob += pulp.lpSum(float(resource[p]) * x[p] for p in project_list) <= resource_limit, 'resource_limit'

    if max_selected > 0:
        prob += pulp.lpSum(x[p] for p in project_list) <= max_selected, 'max_selected'

    if min_selected > 0:
        prob += pulp.lpSum(x[p] for p in project_list) >= min_selected, 'min_selected'

    for p in project_list:
        if float(must_do[p]) > 0:
            prob += x[p] == 1, f'must_do_{p}'

    rules = project_rules if project_rules is not None else pd.DataFrame(columns=['From', 'To', 'Type'])
    if len(rules) > 0:
        require_columns(rules, 'project_rules', ['From', 'To', 'Type'])
        for _, row in rules.iterrows():
            from_p = str(row['From'])
            to_p = str(row['To'])
            rtype = str(row['Type']).strip().lower()
            if rtype not in _ALLOWED_RULE_TYPES:
                raise Exception(
                    f"project_rules Type must be one of {sorted(_ALLOWED_RULE_TYPES)}. Found: {row['Type']}"
                )
            if from_p not in project_list:
                raise Exception(f'project_rules has unknown From project: {from_p}')
            if to_p not in project_list:
                raise Exception(f'project_rules has unknown To project: {to_p}')

            if rtype == 'depends_on':
                prob += x[from_p] <= x[to_p], f'depends_{from_p}_on_{to_p}'
            elif rtype == 'excludes':
                cname = '_'.join(sorted([from_p, to_p]))
                prob += x[from_p] + x[to_p] <= 1, f'excludes_{cname}'

    prob.solve(solver())
    status = pulp.LpStatus[prob.status]

    total_value = 0.0
    total_cost = 0.0
    total_resource = 0.0
    selected_count = 0
    decision_rows = []

    for p in project_list:
        pick = int(round(float(x[p].value() or 0)))
        v = float(value[p])
        c = float(cost[p])
        r = float(resource[p]) if has_resource else 0.0
        total_value += v * pick
        total_cost += c * pick
        total_resource += r * pick
        selected_count += pick

        if show_zero or pick > 0:
            row = {
                'Project': p,
                'Selected': pick,
                'Value': round(v, 6),
                'Cost': round(c, 6),
                'Value Contribution': round(v * pick, 6),
                'Cost Contribution': round(c * pick, 6),
            }
            if has_resource:
                row['Resource'] = round(r, 6)
                row['Resource Contribution'] = round(r * pick, 6)
            if has_must_do:
                row['Must Do'] = int(float(must_do[p]) > 0)
            decision_rows.append(row)

    summary_row = {
        'Model': 'Project Portfolio',
        'Status': status,
        'Objective': safe_objective_value(prob),
        'Selected Projects': int(selected_count),
        'Total Value': round(total_value, 6),
        'Total Cost': round(total_cost, 6),
        'Budget Limit': budget_limit,
    }
    if has_resource:
        summary_row['Total Resource'] = round(total_resource, 6)
        summary_row['Resource Limit'] = resource_limit

    return {
        'Summary': pd.DataFrame([summary_row]),
        'Decision Table': pd.DataFrame(decision_rows),
        'Constraint Slack': slack_table(prob),
    }
