# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

import pandas as pd
import pulp

from ..opt_core import require_columns, safe_objective_value, solver, slack_table


def solve_assignment(agents, tasks, assign_cost, show_zero):
    require_columns(agents, 'agents', ['Agent', 'Capacity'])
    require_columns(tasks, 'tasks', ['Task'])
    require_columns(assign_cost, 'assign_cost', ['Agent', 'Task', 'Cost'])

    agent_list = agents['Agent'].astype(str).tolist()
    task_list = tasks['Task'].astype(str).tolist()
    capacity = dict(zip(agents['Agent'].astype(str), pd.to_numeric(agents['Capacity'])))
    cost = {(str(r['Agent']), str(r['Task'])): float(r['Cost']) for _, r in assign_cost.iterrows()}

    missing_pairs = [
        f'{a}-{t}' for a in agent_list for t in task_list if (a, t) not in cost
    ]
    if missing_pairs:
        preview = ', '.join(missing_pairs[:10])
        raise Exception(f'assign_cost missing pair(s): {preview}')

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
