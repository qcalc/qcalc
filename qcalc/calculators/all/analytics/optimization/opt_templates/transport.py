# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

import pandas as pd
import pulp

from ..opt_core import require_columns, safe_objective_value, solver, slack_table


def solve_transport(supply, demand, ship_cost, flow_type, show_zero):
    require_columns(supply, 'supply', ['Source', 'Capacity'])
    require_columns(demand, 'demand', ['Destination', 'Demand'])
    require_columns(ship_cost, 'ship_cost', ['Source', 'Destination', 'Cost'])

    sources = supply['Source'].astype(str).tolist()
    destinations = demand['Destination'].astype(str).tolist()
    capacity = dict(zip(supply['Source'].astype(str), pd.to_numeric(supply['Capacity'])))
    req = dict(zip(demand['Destination'].astype(str), pd.to_numeric(demand['Demand'])))
    cost = {(str(r['Source']), str(r['Destination'])): float(r['Cost']) for _, r in ship_cost.iterrows()}

    missing_pairs = [
        f'{s}-{d}' for s in sources for d in destinations if (s, d) not in cost
    ]
    if missing_pairs:
        preview = ', '.join(missing_pairs[:10])
        raise Exception(f'ship_cost missing pair(s): {preview}')

    prob = pulp.LpProblem('optima_transport', pulp.LpMinimize)
    var_type = pulp.LpInteger if flow_type == 'integer' else pulp.LpContinuous
    x = pulp.LpVariable.dicts(
        'Flow', ((s, d) for s in sources for d in destinations), lowBound=0, cat=var_type
    )

    prob += pulp.lpSum(cost[(s, d)] * x[(s, d)] for s in sources for d in destinations)

    for s in sources:
        prob += pulp.lpSum(x[(s, d)] for d in destinations) <= float(capacity[s]), f'supply_{s}'
    for d in destinations:
        prob += pulp.lpSum(x[(s, d)] for s in sources) == float(req[d]), f'demand_{d}'

    prob.solve(solver())
    status = pulp.LpStatus[prob.status]

    decision_rows = []
    for s in sources:
        for d in destinations:
            val = float(x[(s, d)].value() or 0)
            if show_zero or val > 0:
                decision_rows.append({'Source': s, 'Destination': d, 'Flow': round(val, 6), 'Unit Cost': cost[(s, d)]})

    util_rows = []
    for s in sources:
        used = sum(float(x[(s, d)].value() or 0) for d in destinations)
        cap = float(capacity[s])
        util_rows.append({
            'Source': s,
            'Used': round(used, 6),
            'Capacity': round(cap, 6),
            'Utilization %': round((used / cap * 100) if cap else 0, 4),
        })

    return {
        'Summary': pd.DataFrame([{
            'Model': 'Transportation',
            'Status': status,
            'Objective': safe_objective_value(prob),
            'Decision Count': len(decision_rows),
        }]),
        'Decision Table': pd.DataFrame(decision_rows),
        'Capacity Utilization': pd.DataFrame(util_rows),
        'Constraint Slack': slack_table(prob),
    }
