# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

import pandas as pd
import pulp
from qcore import to_cast, qtable, QTable
from qcore import validate_schema_if_needed

from calc import (
    PROJECT_RULES_SCHEMA,
    PROJECTS_SCHEMA,
    field_show_zero,
    table_project_rules,
    table_projects,
)
from calc import safe_objective_value, solver, slack_table



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
    prj = QTable(projects, name='projects', schema=PROJECTS_SCHEMA)
    project_list = prj.assert_unique('Project')
    if not project_list:
        raise Exception('projects must contain at least one row')

    value = prj.to_map('Project', 'Value')
    cost = prj.to_map('Project', 'Cost')
    has_resource = 'Resource' in prj.columns
    resource = prj.to_map('Project', 'Resource') if has_resource else {p: 0.0 for p in project_list}
    has_must_do = 'Must Do' in prj.columns
    must_do = prj.to_map('Project', 'Must Do') if has_must_do else {p: 0 for p in project_list}

    budget_limit = to_cast(project_budget_limit, 'project_budget_limit', float)
    resource_limit = to_cast(project_resource_limit, 'project_resource_limit', float)
    max_selected = to_cast(project_max_selected, 'project_max_selected', int)
    min_selected = to_cast(project_min_selected, 'project_min_selected', int)
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

    rules = QTable.optional(project_rules, name='project_rules', schema=PROJECT_RULES_SCHEMA)
    if rules is not None:
        rules.assert_foreign_key(prj, 'From', 'Project')
        rules.assert_foreign_key(prj, 'To', 'Project')
        for row in rules.select():
            from_p = row['From']
            to_p = row['To']
            if row['Type'] == 'depends_on':
                prob += x[from_p] <= x[to_p], f'depends_{from_p}_on_{to_p}'
            else:
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
                'type': 'float',
                'initial': None,
                'help_text': "Optional total resource cap; requires 'Resource' column in projects.",
            },
            'project_max_selected': {'initial': 0, 'help_text': 'Set 0 for no upper limit on number of selected projects.'},
            'project_min_selected': {'initial': 0, 'help_text': 'Set 0 for no lower limit on number of selected projects.'},
            'show_zero': field_show_zero(),
        },
        'layout': 'lr',
        # 'out1': ['Summary', 'Decision Table'],
        'tags': 'optimization, project portfolio, knapsack, mixed integer programming',
    }



