# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

import pandas as pd
import pulp
from qcore import as_qtable, qtable
from qutil.mod_runtime_validate import validate_schema_if_needed
from qutil import require_complete_pair_grid, require_values_subset

from calc import field_show_zero, table_demand, table_ship_cost, table_supply
from calc import safe_objective_value, solver, slack_table


def optima_transport(
    supply: qtable,
    demand: qtable,
    ship_cost: qtable,
    flow_type,
    show_zero,
):
    validate_schema_if_needed('optima_transport')
    supply = as_qtable(supply)
    demand = as_qtable(demand)
    ship_cost = as_qtable(ship_cost)
    require_values_subset(ship_cost, 'ship_cost', 'Source', supply, 'supply', 'Source')
    require_values_subset(ship_cost, 'ship_cost', 'Destination', demand, 'demand', 'Destination')

    sources = supply['Source'].astype(str).tolist()
    destinations = demand['Destination'].astype(str).tolist()
    capacity = dict(zip(supply['Source'].astype(str), pd.to_numeric(supply['Capacity'])))
    req = dict(zip(demand['Destination'].astype(str), pd.to_numeric(demand['Demand'])))
    cost = {(str(r['Source']), str(r['Destination'])): float(r['Cost']) for _, r in ship_cost.iterrows()}
    require_complete_pair_grid(
        pair_table=ship_cost,
        pair_table_name='ship_cost',
        left_col='Source',
        right_col='Destination',
        left_values=sources,
        right_values=destinations,
        left_label='Source',
        right_label='Destination',
    )

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


def optima_transport__info():
    return {
        'title': 'Optimization: Transportation',
        'desc': (
            'Minimize total shipping cost from sources to destinations under supply and demand constraints.'
            ' Use this for distribution, replenishment, and source-to-demand allocation problems.'
        ),
        'calculate': 'Solve',
        'schema': {
            'supply': table_supply('supply'),
            'demand': table_demand('demand'),
            'ship_cost': table_ship_cost('ship_cost'),
            'flow_type': {
                'type': 'choice',
                'choices': {'continuous': 'Continuous', 'integer': 'Integer'},
                'initial': 'integer',
                'help_text': 'Quantity type for shipment flow variables. Use the same quantity unit basis as supply Capacity and demand Demand.',
            },
            'show_zero': field_show_zero(),
        },
        'layout': 'lr',
        'out1': ['Summary', 'Decision Table'],
        'tags': 'optimization, transportation, linear programming',
    }





