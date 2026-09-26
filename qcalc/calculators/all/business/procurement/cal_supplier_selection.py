# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

import pandas as pd
import pulp
from qcore import as_qtable, qtable
from qutil.mod_runtime_validate import validate_schema_if_needed
from qutil import parse_optional_number, require_unique_values, require_values_subset

from calc import (
    field_show_zero,
    table_material_demand,
    table_supplier_item_cost,
    table_supplier_master,
)
from calc import safe_objective_value, solver, slack_table


def optima_supplier_selection(
    material_demand: qtable,
    supplier_master: qtable,
    supplier_item_cost: qtable,
    max_suppliers,
    material_qty_type,
    budget_limit,
    min_avg_quality,
    max_avg_risk,
    show_zero,
):
    validate_schema_if_needed('optima_supplier_selection')
    material_demand = as_qtable(material_demand)
    supplier_master = as_qtable(supplier_master)
    supplier_item_cost = as_qtable(supplier_item_cost)
    require_values_subset(
        supplier_item_cost,
        'supplier_item_cost',
        'Supplier',
        supplier_master,
        'supplier_master',
        'Supplier',
    )
    require_values_subset(
        supplier_item_cost,
        'supplier_item_cost',
        'Item',
        material_demand,
        'material_demand',
        'Item',
    )
    require_unique_values(material_demand, 'material_demand', 'Item')
    require_unique_values(supplier_master, 'supplier_master', 'Supplier')

    items = material_demand['Item'].astype(str).tolist()
    suppliers = supplier_master['Supplier'].astype(str).tolist()
    demand = dict(zip(material_demand['Item'].astype(str), pd.to_numeric(material_demand['Demand'])))
    capacity = dict(zip(supplier_master['Supplier'].astype(str), pd.to_numeric(supplier_master['Capacity'])))
    fixed_cost = dict(zip(supplier_master['Supplier'].astype(str), pd.to_numeric(supplier_master['Fixed Cost'])))

    pair_cost = {}
    pair_max_qty = {}
    for _, row in supplier_item_cost.iterrows():
        supplier = str(row['Supplier'])
        item = str(row['Item'])
        pair = (supplier, item)
        pair_cost[pair] = float(row['Unit Cost'])
        if 'Max Qty' in supplier_item_cost.columns and str(row.get('Max Qty', '')).strip() != '':
            pair_max_qty[pair] = float(row['Max Qty'])

    pairs = list(pair_cost.keys())
    if not pairs:
        raise Exception('supplier_item_cost must contain at least one supplier-item row')

    for item in items:
        if not any(pair_item == item for _, pair_item in pairs):
            raise Exception(f'No supplier-item cost row found for item: {item}')

    qty_cat = pulp.LpInteger if str(material_qty_type).lower() == 'integer' else pulp.LpContinuous
    prob = pulp.LpProblem('optima_supplier_selection', pulp.LpMinimize)

    x = pulp.LpVariable.dicts('Buy', pairs, lowBound=0, cat=qty_cat)
    y = pulp.LpVariable.dicts('UseSupplier', suppliers, lowBound=0, upBound=1, cat=pulp.LpBinary)

    variable_cost_expr = pulp.lpSum(pair_cost[pair] * x[pair] for pair in pairs)
    fixed_cost_expr = pulp.lpSum(float(fixed_cost[supplier]) * y[supplier] for supplier in suppliers)
    prob += variable_cost_expr + fixed_cost_expr

    for item in items:
        item_pairs = [pair for pair in pairs if pair[1] == item]
        prob += pulp.lpSum(x[pair] for pair in item_pairs) == float(demand[item]), f'demand_{item}'

    for supplier in suppliers:
        supplier_pairs = [pair for pair in pairs if pair[0] == supplier]
        prob += (
            pulp.lpSum(x[pair] for pair in supplier_pairs) <= float(capacity[supplier]),
            f'capacity_{supplier}'
        )

    for supplier, item in pairs:
        fallback_max = min(float(demand[item]), float(capacity[supplier]))
        pair_max = float(pair_max_qty.get((supplier, item), fallback_max))
        pair_max = max(0.0, pair_max)
        prob += x[(supplier, item)] <= pair_max * y[supplier], f'link_{supplier}_{item}'

    if 'Min Order' in supplier_master.columns:
        min_order = dict(zip(supplier_master['Supplier'].astype(str), pd.to_numeric(supplier_master['Min Order'])))
        for supplier in suppliers:
            supplier_pairs = [pair for pair in pairs if pair[0] == supplier]
            prob += (
                pulp.lpSum(x[pair] for pair in supplier_pairs) >= float(min_order[supplier]) * y[supplier],
                f'min_order_{supplier}'
            )

    max_suppliers_val = parse_optional_number(max_suppliers, 'max_suppliers', int)
    max_suppliers_val = 0 if max_suppliers_val is None else max_suppliers_val
    if max_suppliers_val > 0:
        prob += pulp.lpSum(y[supplier] for supplier in suppliers) <= max_suppliers_val, 'max_suppliers'

    budget_limit_val = parse_optional_number(budget_limit, 'budget_limit', float)
    if budget_limit_val is not None:
        prob += variable_cost_expr + fixed_cost_expr <= budget_limit_val, 'budget_limit'

    total_demand = float(sum(float(demand[item]) for item in items))
    if total_demand <= 0:
        raise Exception('Total demand must be greater than zero')

    min_avg_quality_val = parse_optional_number(min_avg_quality, 'min_avg_quality', float)
    if min_avg_quality_val is not None:
        if 'Quality' not in supplier_master.columns:
            raise Exception("supplier_master must include 'Quality' when min_avg_quality is used")
        quality = dict(zip(supplier_master['Supplier'].astype(str), pd.to_numeric(supplier_master['Quality'])))
        prob += (
            pulp.lpSum(
                float(quality[supplier]) * pulp.lpSum(x[pair] for pair in pairs if pair[0] == supplier)
                for supplier in suppliers
            ) >= min_avg_quality_val * total_demand,
            'min_avg_quality'
        )

    max_avg_risk_val = parse_optional_number(max_avg_risk, 'max_avg_risk', float)
    if max_avg_risk_val is not None:
        if 'Risk' not in supplier_master.columns:
            raise Exception("supplier_master must include 'Risk' when max_avg_risk is used")
        risk = dict(zip(supplier_master['Supplier'].astype(str), pd.to_numeric(supplier_master['Risk'])))
        prob += (
            pulp.lpSum(
                float(risk[supplier]) * pulp.lpSum(x[pair] for pair in pairs if pair[0] == supplier)
                for supplier in suppliers
            ) <= max_avg_risk_val * total_demand,
            'max_avg_risk'
        )

    prob.solve(solver())
    status = pulp.LpStatus[prob.status]

    decision_rows = []
    for supplier in suppliers:
        for item in items:
            pair = (supplier, item)
            if pair not in pair_cost:
                continue
            qty = float(x[pair].value() or 0)
            if show_zero or qty > 0:
                unit_cost = float(pair_cost[pair])
                decision_rows.append({
                    'Supplier': supplier,
                    'Item': item,
                    'Qty': round(qty, 6),
                    'Unit Cost': round(unit_cost, 6),
                    'Line Cost': round(unit_cost * qty, 6),
                })

    selected_rows = []
    for supplier in suppliers:
        supplier_pairs = [pair for pair in pairs if pair[0] == supplier]
        purchased = float(sum(float(x[pair].value() or 0) for pair in supplier_pairs))
        cap = float(capacity[supplier])
        selected = int(round(float(y[supplier].value() or 0)))
        row = {
            'Supplier': supplier,
            'Selected': selected,
            'Purchased': round(purchased, 6),
            'Capacity': round(cap, 6),
            'Utilization %': round((purchased / cap * 100) if cap else 0, 4),
            'Fixed Cost': round(float(fixed_cost[supplier]), 6),
        }
        if 'Risk' in supplier_master.columns:
            row['Risk'] = round(float(supplier_master.loc[supplier_master['Supplier'].astype(str) == supplier, 'Risk'].iloc[0]), 6)
        if 'Quality' in supplier_master.columns:
            row['Quality'] = round(float(supplier_master.loc[supplier_master['Supplier'].astype(str) == supplier, 'Quality'].iloc[0]), 6)
        selected_rows.append(row)

    total_purchased = sum(float(x[pair].value() or 0) for pair in pairs)
    selected_count = sum(int(round(float(y[supplier].value() or 0))) for supplier in suppliers)

    return {
        'Summary': pd.DataFrame([{
            'Model': 'Supplier Selection',
            'Status': status,
            'Objective': safe_objective_value(prob),
            'Selected Suppliers': int(selected_count),
            'Total Purchased': round(float(total_purchased), 6),
            'Total Demand': round(float(total_demand), 6),
        }]),
        'Decision Table': pd.DataFrame(decision_rows),
        'Supplier Utilization': pd.DataFrame(selected_rows),
        'Constraint Slack': slack_table(prob),
    }


def optima_supplier_selection__info():
    return {
        'title': 'Optimization: Supplier Selection',
        'desc': (
            'Minimize procurement cost with supplier capacities, optional budget, and risk/quality controls.'
            ' Use this for sourcing decisions, vendor mix planning, and cost-risk-quality trade-off problems.'
        ),
        'calculate': 'Solve',
        'schema': {
            'material_demand': table_material_demand('material_demand'),
            'supplier_master': table_supplier_master('supplier_master'),
            'supplier_item_cost': table_supplier_item_cost('supplier_item_cost'),
            'max_suppliers': {'initial': 0, 'help_text': 'Set 0 for no limit on number of suppliers.'},
            'material_qty_type': {
                'type': 'choice',
                'choices': {'continuous': 'Continuous', 'integer': 'Integer'},
                'initial': 'continuous',
                'help_text': 'Quantity type for material purchase variables. Use the same quantity unit basis as Demand, Capacity, and Max Qty.',
            },
            'budget_limit': {'initial': None, 'help_text': 'Optional total spend cap including variable and fixed costs.'},
            'min_avg_quality': {
                'initial': None,
                'help_text': "Optional lower bound on demand-weighted average quality; requires 'Quality' in supplier_master and uses the same quality scale as that column.",
            },
            'max_avg_risk': {
                'initial': None,
                'help_text': "Optional upper bound on demand-weighted average risk; requires 'Risk' in supplier_master and uses the same risk scale as that column.",
            },
            'show_zero': field_show_zero(),
        },
        'layout': 'lr',
        'out1': ['Summary', 'Decision Table'],
        'tags': 'optimization, supplier selection, mixed integer programming',
    }





