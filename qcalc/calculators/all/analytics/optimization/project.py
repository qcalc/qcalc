# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

import pandas as pd
import pulp
from qcore import as_qtable, qtable
from qutil.mod_runtime_validate import validate_schema_if_needed
from qutil import parse_optional_number, require_unique_values, require_values_subset

from .cal_optima import (
    field_show_zero,
    table_project_rules,
    table_projects,
)
from .opt_core import safe_objective_value, solver, slack_table


_ALLOWED_RULE_TYPES = {'depends_on', 'excludes'}


def optima_project(
    projects: qtable,
    project_rules: qtable,
    project_budget_limit,
    project_resource_limit,
    project_max_selected,
    project_min_selected,
    show_zero,
):
    validate_schema_if_needed('optima_project')
    projects = as_qtable(projects)
    project_rules = as_qtable(project_rules)

    prj = projects.copy()
    prj['Project'] = prj['Project'].astype(str).str.strip()
    project_list = require_unique_values(prj, 'projects', 'Project')
    if not project_list:
        raise Exception('projects must contain at least one row')

    value = dict(zip(prj['Project'], pd.to_numeric(prj['Value'])))
    cost = dict(zip(prj['Project'], pd.to_numeric(prj['Cost'])))

    has_resource = 'Resource' in prj.columns
    resource = dict(zip(prj['Project'], pd.to_numeric(prj['Resource']))) if has_resource else {p: 0.0 for p in project_list}

    has_must_do = 'Must Do' in prj.columns
    must_do = (
        dict(zip(prj['Project'], pd.to_numeric(prj['Must Do'], errors='coerce').fillna(0)))
        if has_must_do else {p: 0 for p in project_list}
    )

    budget_limit = parse_optional_number(project_budget_limit, 'project_budget_limit', float)
    resource_limit = parse_optional_number(project_resource_limit, 'project_resource_limit', float)
    max_selected = parse_optional_number(project_max_selected, 'project_max_selected', int)
    min_selected = parse_optional_number(project_min_selected, 'project_min_selected', int)
    max_selected = 0 if max_selected is None else max_selected
    min_selected = 0 if min_selected is None else min_selected

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
        require_values_subset(rules, 'project_rules', 'From', prj, 'projects', 'Project')
        require_values_subset(rules, 'project_rules', 'To', prj, 'projects', 'Project')
        for _, row in rules.iterrows():
            from_p = str(row['From'])
            to_p = str(row['To'])
            rtype = str(row['Type']).strip().lower()
            if rtype not in _ALLOWED_RULE_TYPES:
                raise Exception(
                    f"project_rules Type must be one of {sorted(_ALLOWED_RULE_TYPES)}. Found: {row['Type']}"
                )

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


def optima_project__info():
    return {
        'title': 'Optimization: Project Portfolio',
        'desc': (
            'Select projects to maximize portfolio value under optional budget, resource, and relation constraints.'
            ' Use this for project intake, capex planning, and constrained portfolio selection problems.'
        ),
        'calculate': 'Solve',
        'schema': {
            'projects': table_projects('projects'),
            'project_rules': table_project_rules('project_rules'),
            'project_budget_limit': {'initial': 220, 'help_text': 'Set empty for no budget cap on selected projects.'},
            'project_resource_limit': {
                'initial': None,
                'help_text': "Optional total resource cap; requires 'Resource' column in projects.",
            },
            'project_max_selected': {'initial': 0, 'help_text': 'Set 0 for no upper limit on number of selected projects.'},
            'project_min_selected': {'initial': 0, 'help_text': 'Set 0 for no lower limit on number of selected projects.'},
            'show_zero': field_show_zero(),
        },
        'layout': 'lr',
        'out1': ['Summary', 'Decision Table'],
        'tags': 'optimization, project portfolio, knapsack, mixed integer programming',
    }





