# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

import pandas as pd
import pulp
from qcore import as_qtable, qtable
from qutil.mod_runtime_validate import validate_schema_if_needed
from qutil import require_unique_pairs, require_unique_values, require_values_subset

from .cal_optima import (
    field_show_zero,
    table_prodinv_demand,
    table_prodinv_item_master,
    table_prodinv_production,
)
from .opt_core import safe_objective_value, solver, slack_table

def _period_sort_key(value):
    text = str(value).strip()
    try:
        return 0, float(text)
    except Exception:
        return 1, text


def optima_production_inventory(
    prodinv_item_master: qtable,
    prodinv_demand: qtable,
    prodinv_production: qtable,
    prodinv_qty_type,
    prodinv_allow_backlog,
    show_zero,
):
    validate_schema_if_needed('optima_production_inventory')
    prodinv_item_master = as_qtable(prodinv_item_master)
    prodinv_demand = as_qtable(prodinv_demand)
    prodinv_production = as_qtable(prodinv_production)
    require_values_subset(prodinv_demand, 'prodinv_demand', 'Item', prodinv_item_master, 'prodinv_item_master', 'Item')
    require_values_subset(
        prodinv_production,
        'prodinv_production',
        'Item',
        prodinv_item_master,
        'prodinv_item_master',
        'Item',
    )

    item_df = prodinv_item_master.copy()
    demand_df = prodinv_demand.copy()
    prod_df = prodinv_production.copy()

    if item_df.empty:
        raise Exception('prodinv_item_master must contain at least one row')
    if demand_df.empty:
        raise Exception('prodinv_demand must contain at least one row')
    if prod_df.empty:
        raise Exception('prodinv_production must contain at least one row')

    item_df['Item'] = item_df['Item'].astype(str).str.strip()
    demand_df['Item'] = demand_df['Item'].astype(str).str.strip()
    prod_df['Item'] = prod_df['Item'].astype(str).str.strip()
    demand_df['Period'] = demand_df['Period'].astype(str).str.strip()
    prod_df['Period'] = prod_df['Period'].astype(str).str.strip()

    items = require_unique_values(item_df, 'prodinv_item_master', 'Item')

    demand_df['Demand'] = pd.to_numeric(demand_df['Demand'])
    prod_df['Unit Cost'] = pd.to_numeric(prod_df['Unit Cost'])
    prod_df['Max Production'] = pd.to_numeric(prod_df['Max Production'])

    initial_inventory = dict(zip(item_df['Item'], pd.to_numeric(item_df['Initial Inventory'])))
    holding_cost = dict(zip(item_df['Item'], pd.to_numeric(item_df['Holding Cost'])))
    backlog_penalty = dict(zip(item_df['Item'], pd.to_numeric(item_df['Backlog Penalty'])))

    for item in items:
        if float(initial_inventory[item]) < 0:
            raise Exception(f'Initial Inventory must be non-negative for item: {item}')
        if float(holding_cost[item]) < 0:
            raise Exception(f'Holding Cost must be non-negative for item: {item}')
        if float(backlog_penalty[item]) < 0:
            raise Exception(f'Backlog Penalty must be non-negative for item: {item}')

    demand_df = demand_df.groupby(['Period', 'Item'], as_index=False)['Demand'].sum()

    require_unique_pairs(prod_df, 'prodinv_production', 'Period', 'Item')

    periods = sorted(set(demand_df['Period'].tolist()) | set(prod_df['Period'].tolist()), key=_period_sort_key)
    if not periods:
        raise Exception('No periods found in demand/production tables')

    demand = {(str(r['Period']), str(r['Item'])): float(r['Demand']) for _, r in demand_df.iterrows()}
    prod_cost = {(str(r['Period']), str(r['Item'])): float(r['Unit Cost']) for _, r in prod_df.iterrows()}
    max_prod = {(str(r['Period']), str(r['Item'])): float(r['Max Production']) for _, r in prod_df.iterrows()}

    setup_cost = {}
    has_setup = 'Setup Cost' in prod_df.columns
    if has_setup:
        prod_df['Setup Cost'] = pd.to_numeric(prod_df['Setup Cost'])
        setup_cost = {(str(r['Period']), str(r['Item'])): float(r['Setup Cost']) for _, r in prod_df.iterrows()}

    pairs = []
    for period in periods:
        for item in items:
            pair = (period, item)
            if pair not in prod_cost:
                raise Exception(
                    f'Missing production row for Period={period}, Item={item}. '
                    'Provide Unit Cost and Max Production for every period-item pair.'
                )
            if float(max_prod[pair]) < 0:
                raise Exception(f'Max Production must be non-negative for Period={period}, Item={item}')
            if float(prod_cost[pair]) < 0:
                raise Exception(f'Unit Cost must be non-negative for Period={period}, Item={item}')
            if has_setup and float(setup_cost[pair]) < 0:
                raise Exception(f'Setup Cost must be non-negative for Period={period}, Item={item}')
            pairs.append(pair)

    qty_cat = pulp.LpInteger if str(prodinv_qty_type).lower() == 'integer' else pulp.LpContinuous
    allow_backlog = bool(prodinv_allow_backlog)

    prob = pulp.LpProblem('optima_production_inventory', pulp.LpMinimize)

    prod_qty = pulp.LpVariable.dicts('Prod', pairs, lowBound=0, cat=qty_cat)
    inv = pulp.LpVariable.dicts('Inv', pairs, lowBound=0, cat=qty_cat)

    backlog = {}
    if allow_backlog:
        backlog = pulp.LpVariable.dicts('Backlog', pairs, lowBound=0, cat=qty_cat)

    setup_use = {}
    has_positive_setup = has_setup and any(float(setup_cost[p]) > 0 for p in pairs)
    if has_positive_setup:
        setup_use = pulp.LpVariable.dicts('Setup', pairs, lowBound=0, upBound=1, cat=pulp.LpBinary)

    production_cost_expr = pulp.lpSum(float(prod_cost[p]) * prod_qty[p] for p in pairs)
    holding_cost_expr = pulp.lpSum(float(holding_cost[p[1]]) * inv[p] for p in pairs)
    backlog_cost_expr = (
        pulp.lpSum(float(backlog_penalty[p[1]]) * backlog[p] for p in pairs)
        if allow_backlog else 0.0
    )
    setup_cost_expr = (
        pulp.lpSum(float(setup_cost[p]) * setup_use[p] for p in pairs)
        if has_positive_setup else 0.0
    )

    prob += production_cost_expr + holding_cost_expr + backlog_cost_expr + setup_cost_expr

    for p in pairs:
        prob += prod_qty[p] <= float(max_prod[p]), f'max_prod_{p[0]}_{p[1]}'
        if has_positive_setup:
            prob += prod_qty[p] <= float(max_prod[p]) * setup_use[p], f'setup_link_{p[0]}_{p[1]}'

    period_index = {period: idx for idx, period in enumerate(periods)}

    for item in items:
        for period in periods:
            pair = (period, item)
            dem = float(demand.get(pair, 0.0))

            if period_index[period] == 0:
                prev_inv = float(initial_inventory[item])
                prev_back = 0.0
            else:
                prev_period = periods[period_index[period] - 1]
                prev_pair = (prev_period, item)
                prev_inv = inv[prev_pair]
                prev_back = backlog[prev_pair] if allow_backlog else 0.0

            if allow_backlog:
                prob += (
                    prev_inv - prev_back + prod_qty[pair] == dem + inv[pair] - backlog[pair],
                    f'balance_{period}_{item}'
                )
            else:
                prob += (
                    prev_inv + prod_qty[pair] == dem + inv[pair],
                    f'balance_{period}_{item}'
                )

    prob.solve(solver())
    status = pulp.LpStatus[prob.status]

    plan_rows = []
    total_demand = 0.0
    total_prod = 0.0
    ending_inventory = 0.0
    ending_backlog = 0.0

    for item in items:
        for period in periods:
            pair = (period, item)
            dem = float(demand.get(pair, 0.0))
            qty = float(prod_qty[pair].value() or 0.0)
            inv_end = float(inv[pair].value() or 0.0)
            back_end = float(backlog[pair].value() or 0.0) if allow_backlog else 0.0
            util = (qty / float(max_prod[pair]) * 100.0) if float(max_prod[pair]) > 0 else 0.0

            total_demand += dem
            total_prod += qty
            if period == periods[-1]:
                ending_inventory += inv_end
                ending_backlog += back_end

            if show_zero or dem > 0 or qty > 0 or inv_end > 0 or back_end > 0:
                plan_rows.append({
                    'Period': period,
                    'Item': item,
                    'Demand': round(dem, 6),
                    'Production': round(qty, 6),
                    'Ending Inventory': round(inv_end, 6),
                    'Ending Backlog': round(back_end, 6),
                    'Unit Production Cost': round(float(prod_cost[pair]), 6),
                    'Max Production': round(float(max_prod[pair]), 6),
                    'Capacity Utilization %': round(util, 4),
                    'Setup Cost': round(float(setup_cost.get(pair, 0.0)), 6) if has_setup else 0.0,
                })

    total_production_cost = sum(float(prod_cost[p]) * float(prod_qty[p].value() or 0.0) for p in pairs)
    total_holding_cost = sum(float(holding_cost[p[1]]) * float(inv[p].value() or 0.0) for p in pairs)
    total_backlog_cost = (
        sum(float(backlog_penalty[p[1]]) * float(backlog[p].value() or 0.0) for p in pairs)
        if allow_backlog else 0.0
    )
    total_setup_cost = (
        sum(float(setup_cost[p]) * float(setup_use[p].value() or 0.0) for p in pairs)
        if has_positive_setup else 0.0
    )

    return {
        'Summary': pd.DataFrame([{
            'Model': 'Production and Inventory Planning',
            'Status': status,
            'Objective': safe_objective_value(prob),
            'Periods': len(periods),
            'Items': len(items),
            'Total Demand': round(total_demand, 6),
            'Total Production': round(total_prod, 6),
            'Ending Inventory': round(ending_inventory, 6),
            'Ending Backlog': round(ending_backlog, 6),
            'Production Cost': round(total_production_cost, 6),
            'Holding Cost': round(total_holding_cost, 6),
            'Backlog Cost': round(total_backlog_cost, 6),
            'Setup Cost': round(total_setup_cost, 6),
        }]),
        'Decision Table': pd.DataFrame(plan_rows),
        'Constraint Slack': slack_table(prob),
    }


def optima_production_inventory__info():
    return {
        'title': 'Optimization: Production and Inventory Planning',
        'desc': (
            'Minimize total production, holding, setup, and optional backlog cost across multiple periods.'
            ' Use this for finite-capacity production planning and inventory balance decisions.'
        ),
        'calculate': 'Solve',
        'schema': {
            'prodinv_item_master': table_prodinv_item_master('prodinv_item_master'),
            'prodinv_demand': table_prodinv_demand('prodinv_demand'),
            'prodinv_production': table_prodinv_production('prodinv_production'),
            'prodinv_qty_type': {
                'type': 'choice',
                'choices': {'continuous': 'Continuous', 'integer': 'Integer'},
                'initial': 'continuous',
                'help_text': 'Quantity type for production, inventory, and backlog variables. Use the same quantity unit basis as demand, inventory, and max production inputs.',
            },
            'prodinv_allow_backlog': {
                'type': 'choice',
                'choices': {False: 'No', True: 'Yes'},
                'initial': True,
                'help_text': 'Allow backlog carry-forward with penalty; disable to force demand-time fulfillment.',
            },
            'show_zero': field_show_zero(),
        },
        'layout': 'lr',
        'out1': ['Summary', 'Decision Table'],
        'tags': 'optimization, production planning, inventory, lot sizing, linear programming',
    }





