# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

import pandas as pd
import pulp
from qcore import as_qtable, qtable
from qutil.mod_runtime_validate import validate_schema_if_needed
from qutil import require_complete_pair_grid, require_values_subset

from calc import field_show_zero, table_agents, table_assign_cost, table_tasks
from calc import safe_objective_value, solver, slack_table


def optima_assignment(
    agents: qtable,
    tasks: qtable,
    assign_cost: qtable,
    show_zero,
):
    validate_schema_if_needed('optima_assignment')
    agents = as_qtable(agents)
    tasks = as_qtable(tasks)
    assign_cost = as_qtable(assign_cost)
    require_values_subset(assign_cost, 'assign_cost', 'Agent', agents, 'agents', 'Agent')
    require_values_subset(assign_cost, 'assign_cost', 'Task', tasks, 'tasks', 'Task')

    agent_list = agents['Agent'].astype(str).tolist()
    task_list = tasks['Task'].astype(str).tolist()
    capacity = dict(zip(agents['Agent'].astype(str), pd.to_numeric(agents['Capacity'])))
    cost = {(str(r['Agent']), str(r['Task'])): float(r['Cost']) for _, r in assign_cost.iterrows()}
    require_complete_pair_grid(
        pair_table=assign_cost,
        pair_table_name='assign_cost',
        left_col='Agent',
        right_col='Task',
        left_values=agent_list,
        right_values=task_list,
        left_label='Agent',
        right_label='Task',
    )

    prob = pulp.LpProblem('optima_assignment', pulp.LpMinimize)
    x = pulp.LpVariable.dicts(
        'Assign', ((a, t) for a in agent_list for t in task_list), lowBound=0, upBound=1, cat=pulp.LpBinary
    )

    prob += pulp.lpSum(cost[(a, t)] * x[(a, t)] for a in agent_list for t in task_list)

    for t in task_list:
        prob += pulp.lpSum(x[(a, t)] for a in agent_list) == 1, f'task_{t}'
    for a in agent_list:
        prob += pulp.lpSum(x[(a, t)] for t in task_list) <= float(capacity[a]), f'agent_{a}'

    prob.solve(solver())
    status = pulp.LpStatus[prob.status]

    decision_rows = []
    for a in agent_list:
        for t in task_list:
            val = float(x[(a, t)].value() or 0)
            if show_zero or val > 0.5:
                decision_rows.append({'Agent': a, 'Task': t, 'Assigned': int(round(val)), 'Cost': cost[(a, t)]})

    util_rows = []
    for a in agent_list:
        used = sum(float(x[(a, t)].value() or 0) for t in task_list)
        cap = float(capacity[a])
        util_rows.append({
            'Agent': a,
            'Assigned Tasks': round(used, 6),
            'Capacity': round(cap, 6),
            'Utilization %': round((used / cap * 100) if cap else 0, 4),
        })

    return {
        'Summary': pd.DataFrame([{
            'Model': 'Assignment',
            'Status': status,
            'Objective': safe_objective_value(prob),
            'Decision Count': len(decision_rows),
        }]),
        'Decision Table': pd.DataFrame(decision_rows),
        'Resource Utilization': pd.DataFrame(util_rows),
        'Constraint Slack': slack_table(prob),
    }


def optima_assignment__info():
    return {
        'title': 'Optimization: Assignment',
        'desc': (
            'Assign tasks to agents at minimum total cost under capacity constraints.'
            ' Use this for worker-task assignment, machine-job assignment, and ticket routing problems.'
        ),
        'calculate': 'Solve',
        'schema': {
            'agents': table_agents('agents'),
            'tasks': table_tasks('tasks'),
            'assign_cost': table_assign_cost('assign_cost'),
            'show_zero': field_show_zero(),
        },
        'layout': 'lr',
        'out1': ['Summary', 'Decision Table'],
        'tags': 'optimization, assignment, mixed integer programming',
    }




