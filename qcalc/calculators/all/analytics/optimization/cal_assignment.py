# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

import pandas as pd
import pulp
from qcore import qtable
from qcore import validate_schema_if_needed
from qcore import QTable
from calc import AGENTS_SCHEMA, ASSIGN_COST_SCHEMA, TASKS_SCHEMA
from calc import field_show_zero, table_agents, table_assign_cost, table_tasks
from calc import safe_objective_value, solver, slack_table


def optima_assignment(
    agents: qtable,
    tasks: qtable,
    assign_cost: qtable,
    show_zero,
):
    validate_schema_if_needed('optima_assignment')
    agents = QTable(agents, name='agents', schema=AGENTS_SCHEMA)
    tasks = QTable(tasks, name='tasks', schema=TASKS_SCHEMA)
    assign_cost = QTable(assign_cost, name='assign_cost', schema=ASSIGN_COST_SCHEMA)
    agent_list = agents.column('Agent')
    task_list = tasks.column('Task')
    assign_cost.assert_foreign_key(agents, 'Agent', 'Agent')
    assign_cost.assert_foreign_key(tasks, 'Task', 'Task')
    assign_cost.assert_complete_cross_join('Agent', 'Task', agent_list, task_list)

    capacity = agents.to_map('Agent', 'Capacity')
    cost = assign_cost.to_map(['Agent', 'Task'], 'Cost')

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
        # 'out1': ['Summary', 'Decision Table'],
        'tags': 'optimization, assignment, mixed integer programming',
    }
