# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

import pandas as pd
import pulp

from calc import QResults
from qcore import as_qtable, qhtml, qtable
from qutil import require_unique_pairs, require_unique_values, require_values_subset
from qutil.mod_runtime_validate import validate_schema_if_needed

from calc import (
    field_show_zero,
    optimization_status_description,
    safe_objective_value,
    slack_table,
    solver,
    table_sop_capacity,
    table_sop_demand,
    table_sop_material_requirements,
    table_sop_overtime,
    table_sop_product_master,
    table_sop_previous_plan,
    table_sop_scenarios,
    table_supplier_item_cost,
    table_supplier_master,
)


def _period_sort_key(value):
    text = str(value).strip()
    try:
        return 0, float(text)
    except Exception:
        return 1, text


def _product_sort_key(value):
    return str(value).strip()


def _as_bool(value):
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    if isinstance(value, (int, float)):
        return value != 0
    text = str(value).strip().lower()
    if text in ('1', 'true', 'yes', 'y', 'on'):
        return True
    if text in ('0', 'false', 'no', 'n', 'off', ''):
        return False
    return bool(value)


def _extract_previous_plan(previous_plan_df: pd.DataFrame | None, products, periods):
    if previous_plan_df is None or previous_plan_df.empty:
        return {}, False

    required_cols = {'Period', 'Product', 'Previous Production'}
    missing_cols = required_cols - set(previous_plan_df.columns)
    if missing_cols:
        raise Exception(
            'sop_previous_plan is missing required columns: ' + ', '.join(sorted(missing_cols))
        )

    previous_plan_df = previous_plan_df.copy()
    previous_plan_df['Product'] = previous_plan_df['Product'].astype(str).str.strip()
    previous_plan_df['Period'] = previous_plan_df['Period'].astype(str).str.strip()
    previous_plan_df['Previous Production'] = pd.to_numeric(previous_plan_df['Previous Production'])

    require_unique_pairs(previous_plan_df, 'sop_previous_plan', 'Period', 'Product')

    lookup = {
        (str(r['Product']), str(r['Period'])): float(r['Previous Production'])
        for _, r in previous_plan_df.iterrows()
    }
    expected = {(product, period) for product in products for period in periods}
    missing_pairs = expected - set(lookup)
    for product, period in missing_pairs:
        lookup[(product, period)] = 0.0
    return lookup, True


def _apply_scenario_multipliers(product_df, demand_df, capacity_df, scenario_row):
    scen_product_df = product_df.copy()
    scen_demand_df = demand_df.copy()
    scen_capacity_df = capacity_df.copy()

    demand_multiplier = float(scenario_row.get('Demand Multiplier', 1.0) or 1.0)
    capacity_multiplier = float(scenario_row.get('Capacity Multiplier', 1.0) or 1.0)
    production_cost_multiplier = float(scenario_row.get('Production Cost Multiplier', 1.0) or 1.0)
    holding_cost_multiplier = float(scenario_row.get('Holding Cost Multiplier', 1.0) or 1.0)
    backlog_penalty_multiplier = float(scenario_row.get('Backlog Penalty Multiplier', 1.0) or 1.0)
    setup_cost_multiplier = float(scenario_row.get('Setup Cost Multiplier', 1.0) or 1.0)
    opening_inventory_multiplier = float(scenario_row.get('Opening Inventory Multiplier', 1.0) or 1.0)
    safety_stock_multiplier = float(scenario_row.get('Safety Stock Multiplier', 1.0) or 1.0)

    scen_demand_df['Demand'] = scen_demand_df['Demand'].astype(float) * demand_multiplier
    scen_capacity_df['Capacity'] = scen_capacity_df['Capacity'].astype(float) * capacity_multiplier

    scen_product_df['Opening Inventory'] = scen_product_df['Opening Inventory'].astype(float) * opening_inventory_multiplier
    scen_product_df['Safety Stock'] = scen_product_df['Safety Stock'].astype(float) * safety_stock_multiplier
    scen_product_df['Production Cost'] = scen_product_df['Production Cost'].astype(float) * production_cost_multiplier
    scen_product_df['Holding Cost'] = scen_product_df['Holding Cost'].astype(float) * holding_cost_multiplier
    scen_product_df['Backlog Penalty'] = scen_product_df['Backlog Penalty'].astype(float) * backlog_penalty_multiplier
    if 'Setup Cost' in scen_product_df.columns:
        scen_product_df['Setup Cost'] = scen_product_df['Setup Cost'].astype(float) * setup_cost_multiplier

    return scen_product_df, scen_demand_df, scen_capacity_df


def _chart_metric_for_objective(objective):
    objective = str(objective).strip().lower()
    if objective == 'service_level':
        return 'Service Level %'
    if objective == 'inventory_minimize':
        return 'Ending Inventory'
    return 'Total Cost'


def _optional_table_schema(table_builder, field_name):
    schema = dict(table_builder(field_name))
    schema.pop('validators', None)
    return schema


def _build_material_requirements(product_df, product_rows, sop_material_requirements):
    bom_df = as_qtable(sop_material_requirements if sop_material_requirements is not None else pd.DataFrame())
    if bom_df.empty:
        return pd.DataFrame(), pd.DataFrame()

    required_cols = {'Product', 'Material', 'Qty per Unit'}
    missing_cols = required_cols - set(bom_df.columns)
    if missing_cols:
        raise Exception(
            'sop_material_requirements is missing required columns: ' + ', '.join(sorted(missing_cols))
        )

    bom_df = bom_df.copy()
    bom_df['Product'] = bom_df['Product'].astype(str).str.strip()
    bom_df['Material'] = bom_df['Material'].astype(str).str.strip()
    bom_df['Qty per Unit'] = pd.to_numeric(bom_df['Qty per Unit'])

    require_values_subset(bom_df, 'sop_material_requirements', 'Product', product_df, 'sop_product_master', 'Product')
    require_unique_pairs(bom_df, 'sop_material_requirements', 'Product', 'Material')

    product_totals = {}
    for row in product_rows:
        product_name = str(row.get('Product', '')).strip()
        if product_name:
            product_totals[product_name] = float(row.get('Total Production', 0.0) or 0.0)

    known_products = set(str(product).strip() for product in product_df['Product'].tolist())
    bom_products = set(bom_df['Product'].tolist())
    missing_products = sorted(known_products - bom_products)
    if missing_products:
        raise Exception(
            'sop_material_requirements must include at least one row for every product when procurement is enabled. Missing: '
            + ', '.join(missing_products)
        )

    detail_rows = []
    demand_map = {}
    for _, row in bom_df.iterrows():
        product = str(row['Product'])
        material = str(row['Material'])
        qty_per_unit = float(row['Qty per Unit'])
        if qty_per_unit < 0:
            raise Exception(f'Qty per Unit must be non-negative for Product={product}, Material={material}')
        produced_qty = float(product_totals.get(product, 0.0))
        required_qty = produced_qty * qty_per_unit
        detail_rows.append({
            'Product': product,
            'Material': material,
            'Total Production': round(produced_qty, 6),
            'Qty per Unit': round(qty_per_unit, 6),
            'Required Qty': round(required_qty, 6),
        })
        demand_map[material] = demand_map.get(material, 0.0) + required_qty

    material_demand_df = pd.DataFrame([
        {'Item': material, 'Demand': round(demand, 6)}
        for material, demand in sorted(demand_map.items())
        if demand > 0
    ])

    return pd.DataFrame(detail_rows), material_demand_df


def _attach_procurement_model(
    prob,
    production,
    local_products,
    local_periods,
    bom_df,
    supplier_master_df,
    supplier_item_cost_df,
    qty_cat,
    max_suppliers,
    material_qty_type,
    budget_limit,
    min_avg_quality,
    max_avg_risk,
):
    bom_df = as_qtable(bom_df if bom_df is not None else pd.DataFrame())
    supplier_master_df = as_qtable(supplier_master_df if supplier_master_df is not None else pd.DataFrame())
    supplier_item_cost_df = as_qtable(supplier_item_cost_df if supplier_item_cost_df is not None else pd.DataFrame())

    if bom_df.empty:
        raise Exception('sop_material_requirements must contain at least one row when procurement is enabled')
    if supplier_master_df.empty:
        raise Exception('supplier_master must contain at least one row when procurement is enabled')
    if supplier_item_cost_df.empty:
        raise Exception('supplier_item_cost must contain at least one row when procurement is enabled')

    required_bom_cols = {'Product', 'Material', 'Qty per Unit'}
    missing_bom_cols = required_bom_cols - set(bom_df.columns)
    if missing_bom_cols:
        raise Exception('sop_material_requirements is missing required columns: ' + ', '.join(sorted(missing_bom_cols)))

    required_supplier_cols = {'Supplier', 'Capacity', 'Fixed Cost'}
    missing_supplier_cols = required_supplier_cols - set(supplier_master_df.columns)
    if missing_supplier_cols:
        raise Exception('supplier_master is missing required columns: ' + ', '.join(sorted(missing_supplier_cols)))

    required_cost_cols = {'Supplier', 'Item', 'Unit Cost'}
    missing_cost_cols = required_cost_cols - set(supplier_item_cost_df.columns)
    if missing_cost_cols:
        raise Exception('supplier_item_cost is missing required columns: ' + ', '.join(sorted(missing_cost_cols)))

    bom_df = bom_df.copy()
    supplier_master_df = supplier_master_df.copy()
    supplier_item_cost_df = supplier_item_cost_df.copy()

    bom_df['Product'] = bom_df['Product'].astype(str).str.strip()
    bom_df['Material'] = bom_df['Material'].astype(str).str.strip()
    bom_df['Qty per Unit'] = pd.to_numeric(bom_df['Qty per Unit'])
    supplier_master_df['Supplier'] = supplier_master_df['Supplier'].astype(str).str.strip()
    supplier_master_df['Capacity'] = pd.to_numeric(supplier_master_df['Capacity'])
    supplier_master_df['Fixed Cost'] = pd.to_numeric(supplier_master_df['Fixed Cost'])
    supplier_item_cost_df['Supplier'] = supplier_item_cost_df['Supplier'].astype(str).str.strip()
    supplier_item_cost_df['Item'] = supplier_item_cost_df['Item'].astype(str).str.strip()
    supplier_item_cost_df['Unit Cost'] = pd.to_numeric(supplier_item_cost_df['Unit Cost'])

    require_unique_pairs(bom_df, 'sop_material_requirements', 'Product', 'Material')
    require_unique_values(supplier_master_df, 'supplier_master', 'Supplier')
    require_values_subset(
        supplier_item_cost_df,
        'supplier_item_cost',
        'Supplier',
        supplier_master_df,
        'supplier_master',
        'Supplier',
    )

    bom_map = {(str(r['Product']), str(r['Material'])): float(r['Qty per Unit']) for _, r in bom_df.iterrows()}
    materials = sorted({material for _, material in bom_map.keys()}, key=_product_sort_key)
    supplier_rows = supplier_master_df['Supplier'].astype(str).tolist()
    supplier_capacity = dict(zip(supplier_master_df['Supplier'], supplier_master_df['Capacity']))
    supplier_fixed_cost = dict(zip(supplier_master_df['Supplier'], supplier_master_df['Fixed Cost']))

    pair_cost = {}
    pair_max_qty = {}
    for _, row in supplier_item_cost_df.iterrows():
        supplier = str(row['Supplier'])
        material = str(row['Item'])
        pair = (supplier, material)
        pair_cost[pair] = float(row['Unit Cost'])
        if 'Max Qty' in supplier_item_cost_df.columns and str(row.get('Max Qty', '')).strip() != '':
            pair_max_qty[pair] = float(row['Max Qty'])

    for material in materials:
        if not any(pair_material == material for _, pair_material in pair_cost.keys()):
            raise Exception(f'No supplier-item cost row found for material: {material}')

    purchase = pulp.LpVariable.dicts('Buy', list(pair_cost.keys()), lowBound=0, cat=qty_cat)
    supplier_use = pulp.LpVariable.dicts('UseSupplier', supplier_rows, lowBound=0, upBound=1, cat=pulp.LpBinary)

    material_requirement_expr = {}
    for material in materials:
        material_requirement_expr[material] = pulp.lpSum(
            production[(product, period)] * float(qty_per_unit)
            for (product, bom_material), qty_per_unit in bom_map.items()
            if bom_material == material
            for period in local_periods
        )
        prob += (
            pulp.lpSum(purchase[(supplier, material)] for supplier in supplier_rows if (supplier, material) in purchase)
            == material_requirement_expr[material],
            f'material_balance_{material}'
        )

    variable_cost_expr = pulp.lpSum(pair_cost[pair] * purchase[pair] for pair in pair_cost)
    fixed_cost_expr = pulp.lpSum(float(supplier_fixed_cost[supplier]) * supplier_use[supplier] for supplier in supplier_rows)

    for supplier in supplier_rows:
        supplier_pairs = [pair for pair in pair_cost if pair[0] == supplier]
        prob += (
            pulp.lpSum(purchase[pair] for pair in supplier_pairs) <= float(supplier_capacity[supplier]),
            f'procurement_capacity_{supplier}'
        )

    for supplier, material in pair_cost:
        fallback_max = float(supplier_capacity[supplier])
        pair_max = float(pair_max_qty.get((supplier, material), fallback_max))
        prob += purchase[(supplier, material)] <= pair_max * supplier_use[supplier], f'procurement_link_{supplier}_{material}'

    max_suppliers_val = int(max_suppliers or 0)
    if max_suppliers_val > 0:
        prob += pulp.lpSum(supplier_use[supplier] for supplier in supplier_rows) <= max_suppliers_val, 'max_suppliers'

    budget_limit_val = None if budget_limit in (None, '') else float(budget_limit)
    if budget_limit_val is not None:
        prob += variable_cost_expr + fixed_cost_expr <= budget_limit_val, 'budget_limit'

    total_material_requirement = pulp.lpSum(material_requirement_expr[material] for material in materials)
    min_avg_quality_val = None if min_avg_quality in (None, '') else float(min_avg_quality)
    if min_avg_quality_val is not None:
        if 'Quality' not in supplier_master_df.columns:
            raise Exception("supplier_master must include 'Quality' when procurement_min_avg_quality is used")
        quality = dict(zip(supplier_master_df['Supplier'], pd.to_numeric(supplier_master_df['Quality'])))
        prob += (
            pulp.lpSum(
                float(quality[supplier]) * pulp.lpSum(purchase[pair] for pair in pair_cost if pair[0] == supplier)
                for supplier in supplier_rows
            ) >= min_avg_quality_val * total_material_requirement,
            'min_avg_quality'
        )

    max_avg_risk_val = None if max_avg_risk in (None, '') else float(max_avg_risk)
    if max_avg_risk_val is not None:
        if 'Risk' not in supplier_master_df.columns:
            raise Exception("supplier_master must include 'Risk' when procurement_max_avg_risk is used")
        risk = dict(zip(supplier_master_df['Supplier'], pd.to_numeric(supplier_master_df['Risk'])))
        prob += (
            pulp.lpSum(
                float(risk[supplier]) * pulp.lpSum(purchase[pair] for pair in pair_cost if pair[0] == supplier)
                for supplier in supplier_rows
            ) <= max_avg_risk_val * total_material_requirement,
            'max_avg_risk'
        )

    return {
        'bom_map': bom_map,
        'materials': materials,
        'supplier_rows': supplier_rows,
        'supplier_capacity': supplier_capacity,
        'supplier_fixed_cost': supplier_fixed_cost,
        'pair_cost': pair_cost,
        'purchase': purchase,
        'supplier_use': supplier_use,
        'variable_cost_expr': variable_cost_expr,
        'fixed_cost_expr': fixed_cost_expr,
        'material_requirement_expr': material_requirement_expr,
        'material_requirement_total_expr': total_material_requirement,
        'bom_df': bom_df,
        'supplier_master_df': supplier_master_df,
        'supplier_item_cost_df': supplier_item_cost_df,
    }


def _build_sop_output(base_result, use_stability, overtime_enabled, scenario_enabled, scenarios_enabled_df, product_df, demand_df, capacity_df, previous_lookup, objective, solve_plan):
    summary_row = dict(base_result['summary'])
    summary_row['Status Description'] = optimization_status_description(str(summary_row.get('Status', 'Unknown')))
    output = {
        'Summary': pd.DataFrame([summary_row]),
        'Period Plan': pd.DataFrame(base_result['period_rows']),
        'Capacity Utilization': pd.DataFrame(base_result['capacity_rows']),
        'Product Summary': pd.DataFrame(base_result['product_rows']),
        'Constraint Slack': base_result['constraint_slack'],
        'Constraint Slack Note': qhtml(
            '<div style="margin-top: 0.5rem;">'
            'Positive slack means the constraint has headroom, '
            'zero means it is binding, and negative slack means the constraint is violated or the solve is infeasible/tight.'
            '</div>'
        ),
    }

    if use_stability:
        output['Stability Summary'] = pd.DataFrame(base_result.get('stability_rows') or [])

    if overtime_enabled:
        overtime_rows = []
        for row in base_result['capacity_rows']:
            overtime_rows.append({
                'Period': row['Period'],
                'Overtime Capacity': row.get('Overtime Capacity', 0.0),
                'Overtime Used': row.get('Overtime Used', 0.0),
                'Overtime Cost': row.get('Overtime Cost', 0.0),
            })
        output['Overtime Summary'] = pd.DataFrame(overtime_rows)

    if scenario_enabled:
        scenario_rows = []
        for _, row in scenarios_enabled_df.iterrows():
            scenario_name = str(row['Scenario']).strip() or 'Scenario'
            scen_product_df, scen_demand_df, scen_capacity_df = _apply_scenario_multipliers(product_df, demand_df, capacity_df, row)
            scen_result = solve_plan(
                scen_product_df,
                scen_demand_df,
                scen_capacity_df,
                previous_lookup_map=previous_lookup if use_stability else None,
                build_details=False,
            )
            scen_summary = dict(scen_result['summary'])
            scen_summary['Scenario'] = scenario_name
            scen_summary['Demand Multiplier'] = float(row.get('Demand Multiplier', 1.0) or 1.0)
            scen_summary['Capacity Multiplier'] = float(row.get('Capacity Multiplier', 1.0) or 1.0)
            scen_summary['Production Cost Multiplier'] = float(row.get('Production Cost Multiplier', 1.0) or 1.0)
            scen_summary['Holding Cost Multiplier'] = float(row.get('Holding Cost Multiplier', 1.0) or 1.0)
            scen_summary['Backlog Penalty Multiplier'] = float(row.get('Backlog Penalty Multiplier', 1.0) or 1.0)
            scenario_rows.append(scen_summary)

        scenario_df = pd.DataFrame(scenario_rows)
        scenario_metric = _chart_metric_for_objective(objective)
        if scenario_metric not in scenario_df.columns:
            scenario_metric = 'Objective'
        output['Scenario Summary'] = scenario_df
        output['Scenario Chart'] = QResults.df2chart(
            scenario_df,
            x_column='Scenario',
            y_columns=[scenario_metric],
            ylabel=scenario_metric,
            chart_title=f'Scenario Comparison - {scenario_metric}',
            chart_type='bars',
        )

    return output


def _prepare_sop_inputs(
    sop_product_master,
    sop_demand,
    sop_capacity,
    overtime_enabled,
    sop_overtime,
    bom_enabled,
    sop_material_requirements,
    objective,
    qty_type,
    backlog_policy,
    max_backlog_pct,
    service_level_floor_pct,
    stability_enabled,
    stability_penalty,
    max_change_pct,
    sop_previous_plan,
    enable_scenarios,
    scenarios_enabled,
    sop_scenarios,
):
    validate_schema_if_needed('optima_sop')

    product_df = as_qtable(sop_product_master)
    demand_df = as_qtable(sop_demand)
    capacity_df = as_qtable(sop_capacity)
    overtime_df = as_qtable(sop_overtime if sop_overtime is not None else pd.DataFrame())
    bom_df = as_qtable(sop_material_requirements if sop_material_requirements is not None else pd.DataFrame())
    previous_plan_df = as_qtable(sop_previous_plan if sop_previous_plan is not None else pd.DataFrame())
    scenarios_df = as_qtable(sop_scenarios if sop_scenarios is not None else pd.DataFrame())

    if product_df.empty:
        raise Exception('sop_product_master must contain at least one row')
    if demand_df.empty:
        raise Exception('sop_demand must contain at least one row')
    if capacity_df.empty:
        raise Exception('sop_capacity must contain at least one row')
    if _as_bool(overtime_enabled) and overtime_df.empty:
        raise Exception('sop_overtime must contain at least one row when overtime is enabled')
    if _as_bool(bom_enabled) and bom_df.empty:
        raise Exception('sop_material_requirements must contain at least one row when BOM is enabled')

    product_df = product_df.copy()
    demand_df = demand_df.copy()
    capacity_df = capacity_df.copy()

    required_product_cols = [
        'Product',
        'Opening Inventory',
        'Safety Stock',
        'Production Cost',
        'Holding Cost',
        'Max Production',
        'Backlog Penalty',
    ]
    for col in required_product_cols:
        if col not in product_df.columns:
            raise Exception(f'Missing required column in sop_product_master: {col}')

    if _as_bool(overtime_enabled) and not overtime_df.empty:
        overtime_df = overtime_df.copy()
        overtime_df['Period'] = overtime_df['Period'].astype(str).str.strip()
        overtime_df['Overtime Capacity'] = pd.to_numeric(overtime_df['Overtime Capacity'])
        overtime_df['Overtime Cost'] = pd.to_numeric(overtime_df['Overtime Cost'])
        require_unique_values(overtime_df, 'sop_overtime', 'Period')

    product_df['Product'] = product_df['Product'].astype(str).str.strip()
    demand_df['Product'] = demand_df['Product'].astype(str).str.strip()
    demand_df['Period'] = demand_df['Period'].astype(str).str.strip()
    capacity_df['Period'] = capacity_df['Period'].astype(str).str.strip()

    products = require_unique_values(product_df, 'sop_product_master', 'Product')
    demand_df['Demand'] = pd.to_numeric(demand_df['Demand'])
    capacity_df['Capacity'] = pd.to_numeric(capacity_df['Capacity'])

    require_values_subset(demand_df, 'sop_demand', 'Product', product_df, 'sop_product_master', 'Product')
    require_unique_values(capacity_df, 'sop_capacity', 'Period')

    opening_inventory = dict(zip(product_df['Product'], pd.to_numeric(product_df['Opening Inventory'])))
    safety_stock = dict(zip(product_df['Product'], pd.to_numeric(product_df['Safety Stock'])))
    production_cost = dict(zip(product_df['Product'], pd.to_numeric(product_df['Production Cost'])))
    holding_cost = dict(zip(product_df['Product'], pd.to_numeric(product_df['Holding Cost'])))
    max_production = dict(zip(product_df['Product'], pd.to_numeric(product_df['Max Production'])))
    backlog_penalty = dict(zip(product_df['Product'], pd.to_numeric(product_df['Backlog Penalty'])))

    setup_cost = {}
    has_setup = 'Setup Cost' in product_df.columns
    if has_setup:
        product_df['Setup Cost'] = pd.to_numeric(product_df['Setup Cost'])
        setup_cost = dict(zip(product_df['Product'], product_df['Setup Cost']))

    for product in products:
        if float(opening_inventory[product]) < 0:
            raise Exception(f'Opening Inventory must be non-negative for product: {product}')
        if float(safety_stock[product]) < 0:
            raise Exception(f'Safety Stock must be non-negative for product: {product}')
        if float(production_cost[product]) < 0:
            raise Exception(f'Production Cost must be non-negative for product: {product}')
        if float(holding_cost[product]) < 0:
            raise Exception(f'Holding Cost must be non-negative for product: {product}')
        if float(max_production[product]) < 0:
            raise Exception(f'Max Production must be non-negative for product: {product}')
        if float(backlog_penalty[product]) < 0:
            raise Exception(f'Backlog Penalty must be non-negative for product: {product}')
        if has_setup and float(setup_cost[product]) < 0:
            raise Exception(f'Setup Cost must be non-negative for product: {product}')

    demand_df = demand_df.groupby(['Period', 'Product'], as_index=False)['Demand'].sum()
    periods = sorted(set(demand_df['Period'].tolist()) | set(capacity_df['Period'].tolist()), key=_period_sort_key)
    if not periods:
        raise Exception('No periods found in sop_demand or sop_capacity')

    demand = {(str(r['Period']), str(r['Product'])): float(r['Demand']) for _, r in demand_df.iterrows()}
    capacity = {str(r['Period']): float(r['Capacity']) for _, r in capacity_df.iterrows()}

    missing_capacity_periods = [period for period in periods if period not in capacity]
    if missing_capacity_periods:
        raise Exception(
            'sop_capacity must contain Capacity for every planning period. Missing: '
            + ', '.join(missing_capacity_periods)
        )

    overtime_capacity = {}
    overtime_cost = {}
    if _as_bool(overtime_enabled) and not overtime_df.empty:
        overtime_periods = set(overtime_df['Period'].tolist())
        missing_overtime_periods = [period for period in periods if period not in overtime_periods]
        if missing_overtime_periods:
            raise Exception(
                'sop_overtime must contain Overtime Capacity and Overtime Cost for every planning period. Missing: '
                + ', '.join(missing_overtime_periods)
            )
        overtime_capacity = {str(r['Period']): float(r['Overtime Capacity']) for _, r in overtime_df.iterrows()}
        overtime_cost = {str(r['Period']): float(r['Overtime Cost']) for _, r in overtime_df.iterrows()}

    objective = str(objective).strip().lower()
    qty_cat = pulp.LpInteger if str(qty_type).lower() == 'integer' else pulp.LpContinuous

    backlog_policy_raw = backlog_policy
    if backlog_policy_raw is None or str(backlog_policy_raw).strip() == '':
        backlog_policy_raw = 'allow'
    backlog_policy = str(backlog_policy_raw).strip().lower()

    stability_enabled = _as_bool(stability_enabled)
    scenario_flag = enable_scenarios if enable_scenarios is not None else scenarios_enabled
    scenario_enabled = _as_bool(scenario_flag)
    backlog_cap_pct = float(max_backlog_pct)
    service_floor_pct = float(service_level_floor_pct)
    stability_penalty = float(stability_penalty)
    max_change_pct = float(max_change_pct)

    if service_floor_pct < 0 or service_floor_pct > 100:
        raise Exception('service_level_floor_pct must be between 0 and 100')
    if backlog_cap_pct < 0 or backlog_cap_pct > 100:
        raise Exception('max_backlog_pct must be between 0 and 100')
    if stability_penalty < 0:
        raise Exception('stability_penalty must be non-negative')
    if max_change_pct < 0:
        raise Exception('max_change_pct must be non-negative')

    if objective == 'service_level' and backlog_policy == 'disallow':
        raise Exception('service_level objective requires backlog to be allowed')
    if backlog_policy not in ('allow', 'disallow', 'cap'):
        raise Exception("backlog_policy must be one of 'allow', 'disallow', or 'cap'")

    scenarios_enabled_df = scenarios_df.copy()
    if scenario_enabled:
        if scenarios_enabled_df.empty:
            raise Exception('sop_scenarios must contain at least one row when scenario analysis is enabled')
        required_scenario_cols = [
            'Scenario',
            'Demand Multiplier',
            'Capacity Multiplier',
            'Production Cost Multiplier',
            'Holding Cost Multiplier',
            'Backlog Penalty Multiplier',
        ]
        for col in required_scenario_cols:
            if col not in scenarios_enabled_df.columns:
                raise Exception(f'Missing required column in sop_scenarios: {col}')
        scenarios_enabled_df['Scenario'] = scenarios_enabled_df['Scenario'].astype(str).str.strip()
        require_unique_values(scenarios_enabled_df, 'sop_scenarios', 'Scenario')

    use_stability = stability_enabled and (stability_penalty > 0 or max_change_pct > 0)
    previous_lookup = {}
    if use_stability:
        previous_lookup, has_previous_plan = _extract_previous_plan(previous_plan_df, products, periods)
        if not has_previous_plan:
            raise Exception('sop_previous_plan is required when previous-plan stability is enabled')

    return {
        'product_df': product_df,
        'demand_df': demand_df,
        'capacity_df': capacity_df,
        'overtime_df': overtime_df,
        'bom_enabled': _as_bool(bom_enabled),
        'bom_df': bom_df,
        'overtime_capacity': overtime_capacity,
        'overtime_cost': overtime_cost,
        'previous_plan_df': previous_plan_df,
        'scenarios_enabled_df': scenarios_enabled_df,
        'objective': objective,
        'qty_cat': qty_cat,
        'backlog_policy': backlog_policy,
        'backlog_cap_pct': backlog_cap_pct,
        'service_floor_pct': service_floor_pct,
        'stability_enabled': stability_enabled,
        'stability_penalty': stability_penalty,
        'max_change_pct': max_change_pct,
        'scenario_enabled': scenario_enabled,
        'use_stability': use_stability,
        'previous_lookup': previous_lookup,
    }


def optima_sop(
    sop_product_master: qtable,
    sop_demand: qtable,
    sop_capacity: qtable,
    objective,
    qty_type,
    backlog_policy='allow',
    max_backlog_pct=25.0,
    service_level_floor_pct=0.0,
    stability_enabled=False,
    stability_penalty=0.0,
    max_change_pct=0.0,
    sop_previous_plan: qtable = None,
    enable_scenarios=None,
    scenarios_enabled=False,
    sop_scenarios: qtable = None,
    show_zero=False,
    overtime_enabled=False,
    sop_overtime: qtable = None,
    bom_enabled=False,
    sop_material_requirements: qtable = None,
    procurement_enabled=False,
    supplier_master: qtable = None,
    supplier_item_cost: qtable = None,
    procurement_max_suppliers=0,
    procurement_material_qty_type='continuous',
    procurement_budget_limit=None,
    procurement_min_avg_quality=None,
    procurement_max_avg_risk=None,
):
    prepared = _prepare_sop_inputs(
        sop_product_master,
        sop_demand,
        sop_capacity,
        overtime_enabled,
        sop_overtime,
        bom_enabled,
        sop_material_requirements,
        objective,
        qty_type,
        backlog_policy,
        max_backlog_pct,
        service_level_floor_pct,
        stability_enabled,
        stability_penalty,
        max_change_pct,
        sop_previous_plan,
        enable_scenarios,
        scenarios_enabled,
        sop_scenarios,
    )

    product_df = prepared['product_df']
    demand_df = prepared['demand_df']
    capacity_df = prepared['capacity_df']
    overtime_df = prepared['overtime_df']
    bom_enabled = prepared['bom_enabled']
    bom_df = prepared['bom_df']
    overtime_capacity = prepared['overtime_capacity']
    overtime_cost = prepared['overtime_cost']
    previous_plan_df = prepared['previous_plan_df']
    scenarios_enabled_df = prepared['scenarios_enabled_df']
    objective = prepared['objective']
    qty_cat = prepared['qty_cat']
    backlog_policy = prepared['backlog_policy']
    backlog_cap_pct = prepared['backlog_cap_pct']
    service_floor_pct = prepared['service_floor_pct']
    stability_enabled = prepared['stability_enabled']
    stability_penalty = prepared['stability_penalty']
    max_change_pct = prepared['max_change_pct']
    scenario_enabled = prepared['scenario_enabled']
    use_stability = prepared['use_stability']
    previous_lookup = prepared['previous_lookup']
    overtime_allowed = _as_bool(overtime_enabled) and not overtime_df.empty
    procurement_allowed = _as_bool(procurement_enabled)

    def solve_plan(product_frame, demand_frame, capacity_frame, previous_lookup_map=None, build_details=True):
        local_product_df = product_frame.copy()
        local_demand_df = demand_frame.copy()
        local_capacity_df = capacity_frame.copy()

        local_product_df['Product'] = local_product_df['Product'].astype(str).str.strip()
        local_demand_df['Product'] = local_demand_df['Product'].astype(str).str.strip()
        local_demand_df['Period'] = local_demand_df['Period'].astype(str).str.strip()
        local_capacity_df['Period'] = local_capacity_df['Period'].astype(str).str.strip()
        local_demand_df['Demand'] = pd.to_numeric(local_demand_df['Demand'])
        local_capacity_df['Capacity'] = pd.to_numeric(local_capacity_df['Capacity'])

        local_products = require_unique_values(local_product_df, 'sop_product_master', 'Product')
        local_demand_df = local_demand_df.groupby(['Period', 'Product'], as_index=False)['Demand'].sum()
        local_periods = sorted(
            set(local_demand_df['Period'].tolist()) | set(local_capacity_df['Period'].tolist()),
            key=_period_sort_key,
        )
        if not local_periods:
            raise Exception('No periods found in sop_demand or sop_capacity')

        local_demand = {
            (str(r['Period']), str(r['Product'])): float(r['Demand'])
            for _, r in local_demand_df.iterrows()
        }
        local_capacity = {
            str(r['Period']): float(r['Capacity'])
            for _, r in local_capacity_df.iterrows()
        }

        local_opening_inventory = dict(zip(local_product_df['Product'], pd.to_numeric(local_product_df['Opening Inventory'])))
        local_safety_stock = dict(zip(local_product_df['Product'], pd.to_numeric(local_product_df['Safety Stock'])))
        local_production_cost = dict(zip(local_product_df['Product'], pd.to_numeric(local_product_df['Production Cost'])))
        local_holding_cost = dict(zip(local_product_df['Product'], pd.to_numeric(local_product_df['Holding Cost'])))
        local_max_production = dict(zip(local_product_df['Product'], pd.to_numeric(local_product_df['Max Production'])))
        local_backlog_penalty = dict(zip(local_product_df['Product'], pd.to_numeric(local_product_df['Backlog Penalty'])))
        local_setup_cost = {}
        local_has_setup = 'Setup Cost' in local_product_df.columns
        if local_has_setup:
            local_product_df['Setup Cost'] = pd.to_numeric(local_product_df['Setup Cost'])
            local_setup_cost = dict(zip(local_product_df['Product'], local_product_df['Setup Cost']))

        demand_total = sum(local_demand.values())
        backlog_allowed = backlog_policy != 'disallow'
        backlog_capped = backlog_policy == 'cap'
        if objective == 'service_level' and not backlog_allowed:
            raise Exception('service_level objective requires backlog to be allowed')

        prob = pulp.LpProblem(
            'optima_sop',
            pulp.LpMaximize if objective == 'service_level' else pulp.LpMinimize,
        )

        production = pulp.LpVariable.dicts(
            'Production', [(p, t) for p in local_products for t in local_periods], lowBound=0, cat=qty_cat
        )
        inventory = pulp.LpVariable.dicts(
            'Inventory', [(p, t) for p in local_products for t in local_periods], lowBound=0, cat=qty_cat
        )
        fulfilled = pulp.LpVariable.dicts(
            'Fulfilled', [(p, t) for p in local_products for t in local_periods], lowBound=0, cat=qty_cat
        )

        backlog = {}
        if backlog_allowed:
            backlog = pulp.LpVariable.dicts(
                'Backlog', [(p, t) for p in local_products for t in local_periods], lowBound=0, cat=qty_cat
            )

        setup_use = {}
        has_positive_setup = local_has_setup and any(float(local_setup_cost[p]) > 0 for p in local_products)
        if has_positive_setup:
            setup_use = pulp.LpVariable.dicts(
                'Setup', [(p, t) for p in local_products for t in local_periods], lowBound=0, upBound=1, cat=pulp.LpBinary
            )

        overtime_use = {}
        if overtime_allowed:
            overtime_use = pulp.LpVariable.dicts(
                'Overtime', [t for t in local_periods], lowBound=0, cat=qty_cat
            )

        procurement_ctx = None
        if procurement_allowed:
            if not bom_enabled:
                raise Exception('procurement_enabled requires BOM to be enabled')
            procurement_ctx = _attach_procurement_model(
                prob,
                production,
                local_products,
                local_periods,
                bom_df,
                supplier_master,
                supplier_item_cost,
                qty_cat,
                procurement_max_suppliers,
                procurement_material_qty_type,
                procurement_budget_limit,
                procurement_min_avg_quality,
                procurement_max_avg_risk,
            )

        change_pos = {}
        change_neg = {}
        abs_change = {}
        if use_stability and previous_lookup_map:
            change_pos = pulp.LpVariable.dicts(
                'ChangePos', [(p, t) for p in local_products for t in local_periods], lowBound=0, cat=qty_cat
            )
            change_neg = pulp.LpVariable.dicts(
                'ChangeNeg', [(p, t) for p in local_products for t in local_periods], lowBound=0, cat=qty_cat
            )
            abs_change = pulp.LpVariable.dicts(
                'AbsChange', [(p, t) for p in local_products for t in local_periods], lowBound=0, cat=qty_cat
            )

        objective_expr = 0
        overtime_cost_expr = 0
        if overtime_allowed:
            overtime_cost_expr = pulp.lpSum(
                float(overtime_cost.get(period, 0.0)) * overtime_use[period]
                for period in local_periods
            )
        procurement_cost_expr = 0
        if procurement_ctx is not None:
            procurement_cost_expr = procurement_ctx['variable_cost_expr'] + procurement_ctx['fixed_cost_expr']
        if objective == 'cost_minimize':
            objective_expr += pulp.lpSum(
                float(local_production_cost[p]) * production[(p, t)]
                for p in local_products for t in local_periods
            )
            objective_expr += pulp.lpSum(
                float(local_holding_cost[p]) * inventory[(p, t)]
                for p in local_products for t in local_periods
            )
            if backlog_allowed:
                objective_expr += pulp.lpSum(
                    float(local_backlog_penalty[p]) * backlog[(p, t)]
                    for p in local_products for t in local_periods
                )
            if has_positive_setup:
                objective_expr += pulp.lpSum(
                    float(local_setup_cost[p]) * setup_use[(p, t)]
                    for p in local_products for t in local_periods
                )
            objective_expr += overtime_cost_expr
            objective_expr += procurement_cost_expr
        elif objective == 'inventory_minimize':
            objective_expr += pulp.lpSum(inventory[(p, t)] for p in local_products for t in local_periods)
            if backlog_allowed:
                objective_expr += 1e-6 * pulp.lpSum(backlog[(p, t)] for p in local_products for t in local_periods)
            if overtime_allowed:
                objective_expr += 1e-6 * overtime_cost_expr
            if procurement_ctx is not None:
                objective_expr += 1e-6 * procurement_cost_expr
        else:
            objective_expr += pulp.lpSum(fulfilled[(p, t)] for p in local_products for t in local_periods)
            objective_expr -= 1e-6 * pulp.lpSum(production[(p, t)] for p in local_products for t in local_periods)
            objective_expr -= 1e-6 * pulp.lpSum(inventory[(p, t)] for p in local_products for t in local_periods)
            if backlog_allowed:
                objective_expr -= 1e-6 * pulp.lpSum(backlog[(p, t)] for p in local_products for t in local_periods)
            if overtime_allowed:
                objective_expr -= 1e-6 * overtime_cost_expr
            if procurement_ctx is not None:
                objective_expr -= 1e-6 * procurement_cost_expr

        if use_stability and previous_lookup_map:
            objective_expr += stability_penalty * pulp.lpSum(abs_change[(p, t)] for p in local_products for t in local_periods)
            if objective == 'service_level':
                objective_expr = pulp.lpSum(fulfilled[(p, t)] for p in local_products for t in local_periods)
                objective_expr -= stability_penalty * pulp.lpSum(abs_change[(p, t)] for p in local_products for t in local_periods)
                objective_expr -= 1e-6 * pulp.lpSum(production[(p, t)] for p in local_products for t in local_periods)
                objective_expr -= 1e-6 * pulp.lpSum(inventory[(p, t)] for p in local_products for t in local_periods)
                if backlog_allowed:
                    objective_expr -= 1e-6 * pulp.lpSum(backlog[(p, t)] for p in local_products for t in local_periods)

        prob += objective_expr

        for product in local_products:
            for period in local_periods:
                prob += production[(product, period)] <= float(local_max_production[product]), f'max_prod_{product}_{period}'
                if has_positive_setup:
                    prob += (
                        production[(product, period)] <= float(local_max_production[product]) * setup_use[(product, period)],
                        f'setup_link_{product}_{period}'
                    )

        for period in local_periods:
            prob += (
                pulp.lpSum(production[(product, period)] for product in local_products) <= float(local_capacity[period]) + (overtime_use[period] if overtime_allowed else 0),
                f'capacity_{period}'
            )
            if overtime_allowed:
                prob += (
                    overtime_use[period] <= float(overtime_capacity.get(period, 0.0)),
                    f'overtime_cap_{period}'
                )

        for product in local_products:
            for idx, period in enumerate(local_periods):
                pair = (product, period)
                demand_value = float(local_demand.get((period, product), 0.0))
                if idx == 0:
                    prev_inventory = float(local_opening_inventory[product])
                    prev_backlog = 0.0
                else:
                    prev_period = local_periods[idx - 1]
                    prev_inventory = inventory[(product, prev_period)]
                    prev_backlog = backlog[(product, prev_period)] if backlog_allowed else 0.0

                if backlog_allowed:
                    prob += (
                        fulfilled[pair] + backlog[pair] == demand_value + prev_backlog,
                        f'demand_balance_{product}_{period}'
                    )
                    if backlog_capped:
                        prob += (
                            backlog[pair] <= demand_value * (backlog_cap_pct / 100.0),
                            f'backlog_cap_{product}_{period}'
                        )
                else:
                    prob += fulfilled[pair] == demand_value, f'demand_balance_{product}_{period}'

                prob += (
                    prev_inventory + production[pair] == fulfilled[pair] + inventory[pair],
                    f'inventory_balance_{product}_{period}'
                )
                prob += inventory[pair] >= float(local_safety_stock[product]), f'safety_stock_{product}_{period}'
                if use_stability and previous_lookup_map:
                    prev_prod = float(previous_lookup_map[(product, period)])
                    prob += (
                        production[pair] - prev_prod == change_pos[pair] - change_neg[pair],
                        f'stability_balance_{product}_{period}'
                    )
                    prob += abs_change[pair] == change_pos[pair] + change_neg[pair], f'stability_abs_{product}_{period}'
                    if max_change_pct > 0:
                        prob += (
                            abs_change[pair] <= abs(prev_prod) * (max_change_pct / 100.0),
                            f'stability_cap_{product}_{period}'
                        )

        if objective == 'cost_minimize' and service_floor_pct > 0:
            prob += (
                pulp.lpSum(fulfilled[(product, period)] for product in local_products for period in local_periods)
                >= demand_total * (service_floor_pct / 100.0),
                'service_floor'
            )

        prob.solve(solver())
        status = pulp.LpStatus[prob.status]

        summary_row = {
            'Status': status,
            'Objective': safe_objective_value(prob),
            'Objective Mode': objective,
            'Periods': len(local_periods),
            'Products': len(local_products),
            'Total Demand': round(demand_total, 6),
        }

        period_rows = []
        product_rows = []
        stability_rows = []
        total_production = 0.0
        total_fulfilled = 0.0
        total_backlog = 0.0
        total_abs_change = 0.0
        total_stability_cost = 0.0
        total_overtime_used = 0.0
        total_overtime_cost = 0.0
        ending_inventory = 0.0

        for product in local_products:
            product_demand = 0.0
            product_production = 0.0
            product_fulfilled = 0.0
            product_backlog = 0.0
            product_end_inventory = 0.0
            for period in local_periods:
                pair = (product, period)
                demand_value = float(local_demand.get((period, product), 0.0))
                prod_value = float(production[pair].value() or 0.0)
                inv_value = float(inventory[pair].value() or 0.0)
                fulfilled_value = float(fulfilled[pair].value() or 0.0)
                backlog_value = float(backlog[pair].value() or 0.0) if backlog_allowed else 0.0
                period_capacity = float(local_capacity[period])
                overtime_value = float(overtime_use[period].value() or 0.0) if overtime_allowed else 0.0
                overtime_capacity_value = float(overtime_capacity.get(period, 0.0)) if overtime_allowed else 0.0
                overtime_cost_value = overtime_value * float(overtime_cost.get(period, 0.0)) if overtime_allowed else 0.0
                period_total_production = sum(float(production[(p, period)].value() or 0.0) for p in local_products)
                total_capacity = period_capacity + overtime_value
                capacity_util = (period_total_production / total_capacity * 100.0) if total_capacity else 0.0
                setup_value = float(setup_use[pair].value() or 0.0) if has_positive_setup else 0.0
                abs_change_value = float(abs_change[pair].value() or 0.0) if abs_change else 0.0
                stability_cost_value = stability_penalty * abs_change_value if abs_change else 0.0

                product_demand += demand_value
                product_production += prod_value
                product_fulfilled += fulfilled_value
                product_backlog += backlog_value
                product_end_inventory = inv_value

                total_production += prod_value
                total_fulfilled += fulfilled_value
                total_backlog += backlog_value
                total_abs_change += abs_change_value
                total_stability_cost += stability_cost_value
                if overtime_allowed and period == local_periods[0]:
                    total_overtime_used += overtime_value
                    total_overtime_cost += overtime_cost_value
                if period == local_periods[-1]:
                    ending_inventory += inv_value

                if build_details and (show_zero or demand_value > 0 or prod_value > 0 or inv_value > 0 or backlog_value > 0):
                    period_rows.append({
                        'Period': period,
                        'Product': product,
                        'Demand': round(demand_value, 6),
                        'Fulfilled': round(fulfilled_value, 6),
                        'Production': round(prod_value, 6),
                        'Ending Inventory': round(inv_value, 6),
                        'Ending Backlog': round(backlog_value, 6),
                        'Safety Stock': round(float(local_safety_stock[product]), 6),
                        'Unit Production Cost': round(float(local_production_cost[product]), 6),
                        'Unit Holding Cost': round(float(local_holding_cost[product]), 6),
                        'Max Production': round(float(local_max_production[product]), 6),
                        'Period Capacity': round(period_capacity, 6),
                        'Overtime Capacity': round(overtime_capacity_value, 6),
                        'Overtime Used': round(overtime_value, 6),
                        'Overtime Cost': round(overtime_cost_value, 6),
                        'Capacity Utilization %': round(capacity_util, 4),
                        'Setup Used': int(round(setup_value)) if has_positive_setup else 0,
                        'Setup Cost': round(float(local_setup_cost.get(product, 0.0)), 6) if local_has_setup else 0.0,
                        'Abs Change': round(abs_change_value, 6),
                        'Stability Cost': round(stability_cost_value, 6),
                    })

                if build_details and abs_change:
                    stability_rows.append({
                        'Product': product,
                        'Period': period,
                        'Previous Production': round(float(previous_lookup_map[(product, period)]), 6),
                        'Current Production': round(prod_value, 6),
                        'Abs Change': round(abs_change_value, 6),
                        'Change Cost': round(stability_cost_value, 6),
                    })

            if build_details:
                product_rows.append({
                    'Product': product,
                    'Total Demand': round(product_demand, 6),
                    'Total Fulfilled': round(product_fulfilled, 6),
                    'Total Production': round(product_production, 6),
                    'Total Backlog': round(product_backlog, 6),
                    'Ending Inventory': round(product_end_inventory, 6),
                    'Opening Inventory': round(float(local_opening_inventory[product]), 6),
                    'Safety Stock': round(float(local_safety_stock[product]), 6),
                })

        total_production_cost = sum(
            float(local_production_cost[p]) * float(production[(p, t)].value() or 0.0)
            for p in local_products for t in local_periods
        )
        total_holding_cost = sum(
            float(local_holding_cost[p]) * float(inventory[(p, t)].value() or 0.0)
            for p in local_products for t in local_periods
        )
        total_backlog_cost = (
            sum(float(local_backlog_penalty[p]) * float(backlog[(p, t)].value() or 0.0) for p in local_products for t in local_periods)
            if backlog_allowed else 0.0
        )
        total_setup_cost = (
            sum(float(local_setup_cost[p]) * float(setup_use[(p, t)].value() or 0.0) for p in local_products for t in local_periods)
            if has_positive_setup else 0.0
        )
        if overtime_allowed:
            total_overtime_used = sum(float(overtime_use[period].value() or 0.0) for period in local_periods)
            total_overtime_cost = sum(float(overtime_cost.get(period, 0.0)) * float(overtime_use[period].value() or 0.0) for period in local_periods)
        total_procurement_cost = 0.0
        procurement_result = {}
        if procurement_ctx is not None:
            material_requirement_rows = []
            material_demand_map = {}
            product_totals = {
                product: sum(float(production[(product, period)].value() or 0.0) for period in local_periods)
                for product in local_products
            }
            for _, row in bom_df.iterrows():
                product = str(row['Product']).strip()
                material = str(row['Material']).strip()
                qty_per_unit = float(row['Qty per Unit'])
                required_qty = float(product_totals.get(product, 0.0)) * qty_per_unit
                material_requirement_rows.append({
                    'Product': product,
                    'Material': material,
                    'Total Production': round(float(product_totals.get(product, 0.0)), 6),
                    'Qty per Unit': round(qty_per_unit, 6),
                    'Required Qty': round(required_qty, 6),
                })
                material_demand_map[material] = material_demand_map.get(material, 0.0) + required_qty

            material_demand_df = pd.DataFrame([
                {'Item': material, 'Demand': round(demand, 6)}
                for material, demand in sorted(material_demand_map.items())
                if demand > 0
            ])

            procurement_decision_rows = []
            procurement_supplier_rows = []
            for supplier in procurement_ctx['supplier_rows']:
                supplier_pairs = [pair for pair in procurement_ctx['pair_cost'] if pair[0] == supplier]
                purchased = sum(float(procurement_ctx['purchase'][pair].value() or 0.0) for pair in supplier_pairs)
                selected = int(round(float(procurement_ctx['supplier_use'][supplier].value() or 0.0)))
                supplier_row = {
                    'Supplier': supplier,
                    'Selected': selected,
                    'Purchased': round(purchased, 6),
                    'Capacity': round(float(procurement_ctx['supplier_capacity'][supplier]), 6),
                    'Utilization %': round((purchased / float(procurement_ctx['supplier_capacity'][supplier]) * 100.0) if float(procurement_ctx['supplier_capacity'][supplier]) else 0.0, 4),
                    'Fixed Cost': round(float(procurement_ctx['supplier_fixed_cost'][supplier]), 6),
                }
                if 'Risk' in procurement_ctx['supplier_master_df'].columns:
                    supplier_row['Risk'] = round(float(procurement_ctx['supplier_master_df'].loc[procurement_ctx['supplier_master_df']['Supplier'] == supplier, 'Risk'].iloc[0]), 6)
                if 'Quality' in procurement_ctx['supplier_master_df'].columns:
                    supplier_row['Quality'] = round(float(procurement_ctx['supplier_master_df'].loc[procurement_ctx['supplier_master_df']['Supplier'] == supplier, 'Quality'].iloc[0]), 6)
                procurement_supplier_rows.append(supplier_row)

                for material in procurement_ctx['materials']:
                    pair = (supplier, material)
                    if pair not in procurement_ctx['purchase']:
                        continue
                    qty = float(procurement_ctx['purchase'][pair].value() or 0.0)
                    if show_zero or qty > 0:
                        unit_cost = float(procurement_ctx['pair_cost'][pair])
                        procurement_decision_rows.append({
                            'Supplier': supplier,
                            'Material': material,
                            'Qty': round(qty, 6),
                            'Unit Cost': round(unit_cost, 6),
                            'Line Cost': round(unit_cost * qty, 6),
                        })

            total_procurement_cost = sum(float(procurement_ctx['pair_cost'][pair]) * float(procurement_ctx['purchase'][pair].value() or 0.0) for pair in procurement_ctx['pair_cost'])
            total_procurement_cost += sum(float(procurement_ctx['supplier_fixed_cost'][supplier]) * float(procurement_ctx['supplier_use'][supplier].value() or 0.0) for supplier in procurement_ctx['supplier_rows'])
            procurement_result = {
                'Procurement Summary': pd.DataFrame([{
                    'Model': 'Integrated Procurement',
                    'Status': status,
                    'Objective': round(total_procurement_cost, 6),
                    'Selected Suppliers': int(sum(int(round(float(procurement_ctx['supplier_use'][supplier].value() or 0.0))) for supplier in procurement_ctx['supplier_rows'])),
                    'Total Purchased': round(sum(float(procurement_ctx['purchase'][pair].value() or 0.0) for pair in procurement_ctx['pair_cost']), 6),
                    'Total Demand': round(sum(material_demand_map.values()), 6),
                }]),
                'Material Requirement Detail': pd.DataFrame(material_requirement_rows),
                'Material Demand': material_demand_df,
                'Procurement Decision Table': pd.DataFrame(procurement_decision_rows),
                'Procurement Supplier Utilization': pd.DataFrame(procurement_supplier_rows),
                'Procurement Constraint Slack': slack_table(prob),
            }

        total_cost = total_production_cost + total_holding_cost + total_backlog_cost + total_setup_cost + total_stability_cost + total_overtime_cost + total_procurement_cost
        service_level_pct = (total_fulfilled / demand_total * 100.0) if demand_total else 0.0
        avg_capacity_utilization = (
            sum(
                (sum(float(production[(p, period)].value() or 0.0) for p in local_products) / float(local_capacity[period]) * 100.0)
                if float(local_capacity[period]) else 0.0
                for period in local_periods
            ) / len(local_periods)
        ) if local_periods else 0.0
        max_capacity_utilization = max(
            ((sum(float(production[(p, period)].value() or 0.0) for p in local_products) / float(local_capacity[period]) * 100.0)
             if float(local_capacity[period]) else 0.0)
            for period in local_periods
        ) if local_periods else 0.0

        summary_row.update({
            'Periods': len(local_periods),
            'Products': len(local_products),
            'Total Fulfilled': round(total_fulfilled, 6),
            'Service Level %': round(service_level_pct, 4),
            'Total Production': round(total_production, 6),
            'Ending Inventory': round(ending_inventory, 6),
            'Ending Backlog': round(total_backlog if backlog_allowed else 0.0, 6),
            'Production Cost': round(total_production_cost, 6),
            'Holding Cost': round(total_holding_cost, 6),
            'Backlog Cost': round(total_backlog_cost, 6),
            'Setup Cost': round(total_setup_cost, 6),
            'Stability Cost': round(total_stability_cost, 6),
            'Overtime Used': round(total_overtime_used, 6),
            'Overtime Cost': round(total_overtime_cost, 6),
            'Total Cost': round(total_cost, 6),
            'Average Capacity Utilization %': round(avg_capacity_utilization, 4),
            'Max Capacity Utilization %': round(max_capacity_utilization, 4),
            'Backlog Policy': backlog_policy,
            'Service Floor %': round(service_floor_pct, 4),
            'Backlog Cap %': round(backlog_cap_pct, 4) if backlog_capped else 0.0,
        })

        if build_details:
            capacity_rows = []
            for period in local_periods:
                period_production = sum(float(production[(product, period)].value() or 0.0) for product in local_products)
                cap = float(local_capacity[period])
                overtime_value = float(overtime_use[period].value() or 0.0) if overtime_allowed else 0.0
                capacity_rows.append({
                    'Period': period,
                    'Capacity': round(cap, 6),
                    'Overtime Capacity': round(float(overtime_capacity.get(period, 0.0)), 6) if overtime_allowed else 0.0,
                    'Overtime Used': round(overtime_value, 6),
                    'Overtime Cost': round(float(overtime_cost.get(period, 0.0)) * overtime_value, 6),
                    'Production Used': round(period_production, 6),
                    'Capacity Utilization %': round((period_production / (cap + overtime_value) * 100.0) if (cap + overtime_value) else 0.0, 4),
                })

            return {
                'summary': summary_row,
                'period_rows': period_rows,
                'capacity_rows': capacity_rows,
                'product_rows': product_rows,
                'stability_rows': stability_rows,
                'constraint_slack': slack_table(prob),
                'procurement_result': procurement_result,
            }

        return {
            'summary': summary_row,
            'constraint_slack': None,
            'procurement_result': procurement_result,
        }

    base_result = solve_plan(
        product_df,
        demand_df,
        capacity_df,
        previous_lookup_map=previous_lookup if use_stability else None,
        build_details=True,
    )

    output = _build_sop_output(
        base_result,
        use_stability,
        overtime_allowed,
        scenario_enabled,
        scenarios_enabled_df,
        product_df,
        demand_df,
        capacity_df,
        previous_lookup,
        objective,
        solve_plan,
    )
    output.update(base_result.get('procurement_result', {}))

    return output


def optima_sop__info():
    return {
        'title': 'Planning: S&OP Optimization',
        'desc': (
            'Optimize a multi-period production and inventory plan from demand, product economics, '
            'and capacity data. The model can minimize cost, maximize service level, or minimize inventory. '
            'Optional overtime and procurement companion modules can be enabled for modular planning workflows.'
        ),
        'layout': 'tb',
        'calculate': 'Solve',
        'input_columns': 1,
        'output_columns': 1,
        'input_blocks': [
            {
                'column': 1,
                'tabs': [
                    {
                        'title': 'Settings',
                        'fields': [
                            'objective',
                            'qty_type',
                            'backlog_policy',
                            'max_backlog_pct',
                            'service_level_floor_pct',
                            'stability_enabled',
                            'scenarios_enabled',
                            'bom_enabled',
                            'overtime_enabled',
                            'procurement_enabled',
                            'show_zero',
                        ],
                    },
                    {
                        'title': 'Product Master',
                        'fields': ['sop_product_master'],
                    },
                    {
                        'title': 'Demand',
                        'fields': ['sop_demand'],
                    },
                    {
                        'title': 'Capacity',
                        'fields': ['sop_capacity'],
                    },
                    {
                        'title': 'BOM',
                        'fields': ['sop_material_requirements'],
                    },
                    {
                        'title': 'Overtime',
                        'fields': [
                            'sop_overtime',
                        ],
                    },
                    {
                        'title': 'Procurement',
                        'fields': [
                            'procurement_max_suppliers',
                            'procurement_material_qty_type',
                            'procurement_budget_limit',
                            'procurement_min_avg_quality',
                            'procurement_max_avg_risk',
                            'supplier_master',
                            'supplier_item_cost',
                        ],
                    },
                    {
                        'title': 'Stability',
                        'fields': [
                            'stability_penalty',
                            'max_change_pct',
                            'sop_previous_plan',
                        ],
                    },
                    {
                        'title': 'Scenarios',
                        'fields': [
                            'sop_scenarios',
                        ],
                    },
                ],
            },
        ],
        'output_blocks': [
            {
                'column': 1,
                'tabs': [
                    {
                        'title': 'Summary',
                        'fields': ['Summary'],
                    },
                    {
                        'title': 'Period Plan',
                        'fields': ['Period Plan'],
                    },
                    {
                        'title': 'Capacity',
                        'fields': ['Capacity Utilization'],
                    },
                    {
                        'title': 'Product',
                        'fields': ['Product Summary'],
                    },
                    {
                        'title': 'Stability',
                        'fields': ['Stability Summary'],
                    },
                    {
                        'title': 'Scenarios',
                        'fields': ['Scenario Summary', 'Scenario Chart'],
                    },
                    {
                        'title': 'Overtime',
                        'fields': ['Overtime Summary'],
                    },
                    {
                        'title': 'Procurement',
                        'fields': [
                            'Procurement Summary',
                            'Material Requirement Detail',
                            'Material Demand',
                            'Procurement Decision Table',
                            'Procurement Supplier Utilization',
                            'Procurement Constraint Slack',
                        ],
                    },
                    {
                        'title': 'Diagnostics',
                        'fields': ['Constraint Slack', 'Constraint Slack Note'],
                    },
                ],
            },
        ],
        'showhide': {
            'objective': {
                'fields': ['service_level_floor_pct'],
                'callback': 'toggle_service_level_floor',
            },
            'backlog_policy': {
                'fields': ['max_backlog_pct'],
                'callback': 'toggle_backlog_cap',
            },
            'stability_enabled': {
                'fields': ['stability_penalty', 'max_change_pct', 'sop_previous_plan'],
                'callback': 'toggle_stability_fields',
            },
            'scenarios_enabled': {
                'fields': ['sop_scenarios'],
                'callback': 'toggle_scenario_fields',
            },
            'bom_enabled': {
                'fields': ['sop_material_requirements'],
                'callback': 'toggle_bom_fields',
            },
            'overtime_enabled': {
                'fields': ['sop_overtime'],
                'callback': 'toggle_overtime_fields',
            },
            'procurement_enabled': {
                'fields': [
                    'procurement_max_suppliers',
                    'procurement_material_qty_type',
                    'procurement_budget_limit',
                    'procurement_min_avg_quality',
                    'procurement_max_avg_risk',
                    'supplier_master',
                    'supplier_item_cost',
                ],
                'callback': 'toggle_procurement_fields',
            },
        },
        'script': """
        function isTruthySelection(v){
            if (typeof v === 'boolean') return v;
            if (Array.isArray(v)) return v.length > 0;
            if (v && typeof v === 'object') return Object.keys(v).length > 0;
            if (v === null || v === undefined) return false;
            var t = String(v).trim().toLowerCase();
            return ['1', 'true', 'yes', 'y', 'on'].indexOf(t) >= 0;
        }
        function toggle_service_level_floor(v){
            return v === 'cost_minimize';
        }
        function toggle_backlog_cap(v){
            return v === 'cap';
        }
        function toggle_stability_fields(v){
            return isTruthySelection(v);
        }
        function toggle_scenario_fields(v){
            return isTruthySelection(v);
        }
        function toggle_bom_fields(v){
            return isTruthySelection(v);
        }
        function toggle_overtime_fields(v){
            return isTruthySelection(v);
        }
        function toggle_procurement_fields(v){
            return isTruthySelection(v);
        }
        """,
        'schema': {
            'objective': {
                'type': 'choice',
                'choices': {
                    'cost_minimize': 'Minimize Total Cost',
                    'service_level': 'Maximize Service Level',
                    'inventory_minimize': 'Minimize Inventory',
                },
                'initial': 'cost_minimize',
                'help_text': 'Select the main planning objective for the S&OP model.',
            },
            'qty_type': {
                'type': 'choice',
                'choices': {
                    'continuous': 'Continuous',
                    'integer': 'Integer',
                },
                'initial': 'continuous',
                'help_text': 'Use integer quantities when production must be whole units.',
            },
            'backlog_policy': {
                'type': 'choice',
                'choices': {
                    'allow': 'Allow Backlog',
                    'disallow': 'Disallow Backlog',
                    'cap': 'Cap Backlog',
                },
                'initial': 'allow',
                'help_text': 'Choose whether backlog is allowed, forbidden, or capped as a percentage of demand.',
            },
            'max_backlog_pct': {
                'type': 'float',
                'initial': 25.0,
                'help_text': 'Maximum backlog as a percentage of demand when backlog policy is set to Cap Backlog.',
            },
            'service_level_floor_pct': {
                'type': 'float',
                'initial': 0.0,
                'help_text': 'Minimum service level percentage for cost-minimization runs. Set 0 to ignore.',
            },
            'stability_enabled': {
                'type': 'checkbox',
                'initial': False,
                'help_text': 'Enable previous-plan stability penalties and caps.',
            },
            'stability_penalty': {
                'type': 'float',
                'initial': 0.0,
                'help_text': 'Penalty per unit absolute change from the previous approved production plan.',
            },
            'max_change_pct': {
                'type': 'float',
                'initial': 0.0,
                'help_text': 'Optional maximum change as a percentage of previous production. Set 0 to disable.',
            },
            'sop_previous_plan': table_sop_previous_plan('sop_previous_plan'),
            'scenarios_enabled': {
                'type': 'checkbox',
                'initial': False,
                'help_text': 'Enable built-in scenario reruns and chart comparison.',
            },
            'sop_scenarios': table_sop_scenarios('sop_scenarios'),
            'sop_product_master': table_sop_product_master('sop_product_master'),
            'sop_demand': table_sop_demand('sop_demand'),
            'sop_capacity': table_sop_capacity('sop_capacity'),
            'bom_enabled': {
                'type': 'checkbox',
                'initial': False,
                'help_text': 'Enable the bill-of-materials layer used to derive procurement demand from the production plan.',
            },
            'overtime_enabled': {
                'type': 'checkbox',
                'initial': False,
                'help_text': 'Enable overtime as an extra modular production capacity source for each period.',
            },
            'sop_material_requirements': table_sop_material_requirements('sop_material_requirements'),
            'sop_overtime': table_sop_overtime('sop_overtime'),
            'procurement_enabled': {
                'type': 'checkbox',
                'initial': False,
                'help_text': 'Enable a companion multi-supplier procurement module fed by the BOM-driven material requirements.',
            },
            'supplier_master': _optional_table_schema(table_supplier_master, 'supplier_master'),
            'supplier_item_cost': _optional_table_schema(table_supplier_item_cost, 'supplier_item_cost'),
            'procurement_max_suppliers': {
                'initial': 0,
                'help_text': 'Maximum number of suppliers to use in the procurement submodel. Use 0 for no limit.',
            },
            'procurement_material_qty_type': {
                'type': 'choice',
                'choices': {
                    'continuous': 'Continuous',
                    'integer': 'Integer',
                },
                'initial': 'continuous',
                'help_text': 'Quantity type for procurement purchase variables.',
            },
            'procurement_budget_limit': {
                'initial': None,
                'help_text': 'Optional procurement budget cap for the companion sourcing model.',
            },
            'procurement_min_avg_quality': {
                'initial': None,
                'help_text': 'Optional lower bound on demand-weighted average supplier quality in the procurement submodel.',
            },
            'procurement_max_avg_risk': {
                'initial': None,
                'help_text': 'Optional upper bound on demand-weighted average supplier risk in the procurement submodel.',
            },
            'show_zero': field_show_zero(),
        },
        'tags': 'planning, sop, optimization, production, inventory, overtime, procurement, mixed integer programming',
    }
