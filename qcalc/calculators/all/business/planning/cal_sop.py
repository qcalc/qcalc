# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

import pandas as pd
import pulp

from calc import QResults
from qcore import qhtml, qtable, QTable
from qcore import validate_schema_if_needed
from qcore import to_bool

from calc import (
    SOP_CAPACITY_SCHEMA,
    SOP_DEMAND_SCHEMA,
    SOP_MATERIAL_REQUIREMENTS_SCHEMA,
    SOP_OVERTIME_SCHEMA,
    SOP_PREVIOUS_PLAN_SCHEMA,
    SOP_PRODUCT_MASTER_SCHEMA,
    SOP_SCENARIOS_SCHEMA,
    SUPPLIER_ITEM_COST_SCHEMA,
    SUPPLIER_MASTER_SCHEMA,
    field_show_zero,
    optimization_status_description,
    safe_objective_value,
    slack_table,
    solver,
    supplier_attribute,
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


# plan field -> table column it comes from (per product)
_PRODUCT_FIELDS = {
    'opening_inventory': 'Opening Inventory',
    'safety_stock': 'Safety Stock',
    'production_cost': 'Production Cost',
    'holding_cost': 'Holding Cost',
    'max_production': 'Max Production',
    'backlog_penalty': 'Backlog Penalty',
}
# plan field -> scenario column holding its multiplier
_SCENARIO_SCALES = {
    'demand': 'Demand Multiplier',
    'capacity': 'Capacity Multiplier',
    'opening_inventory': 'Opening Inventory Multiplier',
    'safety_stock': 'Safety Stock Multiplier',
    'production_cost': 'Production Cost Multiplier',
    'holding_cost': 'Holding Cost Multiplier',
    'backlog_penalty': 'Backlog Penalty Multiplier',
    'setup_cost': 'Setup Cost Multiplier',
}


def _rounded(value):
    return None if value is None else round(float(value), 6)


def _extract_previous_plan(sop_previous_plan, products, periods):
    previous = QTable.optional(sop_previous_plan, name='sop_previous_plan', schema=SOP_PREVIOUS_PLAN_SCHEMA)
    if previous is None:
        return {}, False

    previous.assert_unique_pairs('Period', 'Product')
    lookup = previous.to_map(['Product', 'Period'], 'Previous Production')
    for product in products:
        for period in periods:
            lookup.setdefault((product, period), 0.0)
    return lookup, True


def _apply_scenario_multipliers(plan, scenario):
    scaled = dict(plan)
    for field, column in _SCENARIO_SCALES.items():
        factor = float(scenario.get(column, 1.0))
        scaled[field] = {key: value * factor for key, value in plan[field].items()}
    return scaled


def _chart_metric_for_objective(objective):
    objective = str(objective).strip().lower()
    if objective == 'service_level':
        return 'Service Level %'
    if objective == 'inventory_minimize':
        return 'Ending Inventory'
    return 'Total Cost'


def _optional_table_schema(table_builder, field_name, **kwargs):
    schema = dict(table_builder(field_name, **kwargs))
    schema.pop('validators', None)
    return schema


def _attach_procurement_model(
    prob,
    production,
    local_products,
    local_periods,
    bom,
    supplier_master,
    supplier_item_cost,
    qty_cat,
    max_suppliers,
    material_qty_type,
    budget_limit,
    min_avg_quality,
    max_avg_risk,
):
    supplier_master = QTable.optional(supplier_master, name='supplier_master', schema=SUPPLIER_MASTER_SCHEMA)
    supplier_items = QTable.optional(supplier_item_cost, name='supplier_item_cost', schema=SUPPLIER_ITEM_COST_SCHEMA)
    if supplier_master is None:
        raise Exception('supplier_master must contain at least one row when procurement is enabled')
    if supplier_items is None:
        raise Exception('supplier_item_cost must contain at least one row when procurement is enabled')

    bom.assert_unique_pairs('Product', 'Material')
    supplier_master.assert_unique('Supplier')
    supplier_items.assert_foreign_key(supplier_master, 'Supplier', 'Supplier')
    bom.assert_foreign_key(supplier_items, 'Material', 'Item')

    bom_map = bom.to_map(['Product', 'Material'], 'Qty per Unit')
    materials = sorted({material for _, material in bom_map}, key=_product_sort_key)
    supplier_rows = supplier_master.column('Supplier')
    supplier_capacity = supplier_master.to_map('Supplier', 'Capacity')
    supplier_fixed_cost = supplier_master.to_map('Supplier', 'Fixed Cost')
    supplier_quality = supplier_master.to_map('Supplier', 'Quality') if 'Quality' in supplier_master.columns else None
    supplier_risk = supplier_master.to_map('Supplier', 'Risk') if 'Risk' in supplier_master.columns else None
    pair_cost = supplier_items.to_map(['Supplier', 'Item'], 'Unit Cost')
    pair_max_qty = {}
    if 'Max Qty' in supplier_items.columns:
        pair_max_qty = {(row['Supplier'], row['Item']): row['Max Qty']
                        for row in supplier_items.select() if row['Max Qty'] is not None}

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
    fixed_cost_expr = pulp.lpSum(
        float(supplier_fixed_cost[supplier]) * supplier_use[supplier] for supplier in supplier_rows)

    for supplier in supplier_rows:
        supplier_pairs = [pair for pair in pair_cost if pair[0] == supplier]
        prob += (
            pulp.lpSum(purchase[pair] for pair in supplier_pairs) <= float(supplier_capacity[supplier]),
            f'procurement_capacity_{supplier}'
        )

    for supplier, material in pair_cost:
        fallback_max = float(supplier_capacity[supplier])
        pair_max = float(pair_max_qty.get((supplier, material), fallback_max))
        prob += purchase[(supplier, material)] <= pair_max * supplier_use[
            supplier], f'procurement_link_{supplier}_{material}'

    max_suppliers_val = int(max_suppliers or 0)
    if max_suppliers_val > 0:
        prob += pulp.lpSum(supplier_use[supplier] for supplier in supplier_rows) <= max_suppliers_val, 'max_suppliers'

    budget_limit_val = None if budget_limit in (None, '') else float(budget_limit)
    if budget_limit_val is not None:
        prob += variable_cost_expr + fixed_cost_expr <= budget_limit_val, 'budget_limit'

    total_material_requirement = pulp.lpSum(material_requirement_expr[material] for material in materials)
    min_avg_quality_val = None if min_avg_quality in (None, '') else float(min_avg_quality)
    if min_avg_quality_val is not None:
        quality = supplier_attribute(supplier_master, 'Quality', 'procurement_min_avg_quality')
        prob += (
            pulp.lpSum(
                float(quality[supplier]) * pulp.lpSum(purchase[pair] for pair in pair_cost if pair[0] == supplier)
                for supplier in supplier_rows
            ) >= min_avg_quality_val * total_material_requirement,
            'min_avg_quality'
        )

    max_avg_risk_val = None if max_avg_risk in (None, '') else float(max_avg_risk)
    if max_avg_risk_val is not None:
        risk = supplier_attribute(supplier_master, 'Risk', 'procurement_max_avg_risk')
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
        'supplier_quality': supplier_quality,
        'supplier_risk': supplier_risk,
    }


def _build_sop_output(base_result, use_stability, overtime_enabled, scenario_enabled, scenarios, plan,
                      previous_lookup, objective, solve_plan):
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
        for scenario in scenarios:
            scen_result = solve_plan(
                _apply_scenario_multipliers(plan, scenario),
                previous_lookup_map=previous_lookup if use_stability else None,
                build_details=False,
            )
            scen_summary = dict(scen_result['summary'])
            scen_summary['Scenario'] = scenario['Scenario']
            for column in ('Demand Multiplier', 'Capacity Multiplier', 'Production Cost Multiplier',
                           'Holding Cost Multiplier', 'Backlog Penalty Multiplier'):
                scen_summary[column] = float(scenario[column])
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

    product = QTable.optional(sop_product_master, name='sop_product_master', schema=SOP_PRODUCT_MASTER_SCHEMA)
    demand = QTable.optional(sop_demand, name='sop_demand', schema=SOP_DEMAND_SCHEMA)
    capacity = QTable.optional(sop_capacity, name='sop_capacity', schema=SOP_CAPACITY_SCHEMA)
    if product is None:
        raise Exception('sop_product_master must contain at least one row')
    if demand is None:
        raise Exception('sop_demand must contain at least one row')
    if capacity is None:
        raise Exception('sop_capacity must contain at least one row')

    overtime = None
    if to_bool(overtime_enabled):
        overtime = QTable.optional(sop_overtime, name='sop_overtime', schema=SOP_OVERTIME_SCHEMA)
        if overtime is None:
            raise Exception('sop_overtime must contain at least one row when overtime is enabled')
        overtime.assert_unique('Period')

    bom = None
    if to_bool(bom_enabled):
        bom = QTable.optional(sop_material_requirements, name='sop_material_requirements', schema=SOP_MATERIAL_REQUIREMENTS_SCHEMA)
        if bom is None:
            raise Exception('sop_material_requirements must contain at least one row when BOM is enabled')

    products = product.assert_unique('Product')
    demand.assert_foreign_key(product, 'Product', 'Product')
    capacity.assert_unique('Period')

    demand_by_period_product = demand.sum_by(['Period', 'Product'], 'Demand')
    capacity_by_period = capacity.to_map('Period', 'Capacity')
    periods = sorted({period for period, _ in demand_by_period_product} | set(capacity_by_period),
                     key=_period_sort_key)
    missing_capacity_periods = [period for period in periods if period not in capacity_by_period]
    if missing_capacity_periods:
        raise Exception(
            'sop_capacity must contain Capacity for every planning period. Missing: '
            + ', '.join(missing_capacity_periods)
        )

    overtime_capacity = {}
    overtime_cost = {}
    if overtime is not None:
        overtime_capacity = overtime.to_map('Period', 'Overtime Capacity')
        overtime_cost = overtime.to_map('Period', 'Overtime Cost')
        missing_overtime_periods = [period for period in periods if period not in overtime_capacity]
        if missing_overtime_periods:
            raise Exception(
                'sop_overtime must contain Overtime Capacity and Overtime Cost for every planning period. Missing: '
                + ', '.join(missing_overtime_periods)
            )

    plan = {
        'products': products,
        'periods': periods,
        'demand': demand_by_period_product,
        'capacity': capacity_by_period,
        'setup_cost': product.to_map('Product', 'Setup Cost') if 'Setup Cost' in product.columns else {},
        **{field: product.to_map('Product', column) for field, column in _PRODUCT_FIELDS.items()},
    }

    objective = str(objective).strip().lower()
    qty_cat = pulp.LpInteger if str(qty_type).lower() == 'integer' else pulp.LpContinuous

    backlog_policy_raw = backlog_policy
    if backlog_policy_raw is None or str(backlog_policy_raw).strip() == '':
        backlog_policy_raw = 'allow'
    backlog_policy = str(backlog_policy_raw).strip().lower()

    stability_enabled = to_bool(stability_enabled)
    scenario_flag = enable_scenarios if enable_scenarios is not None else scenarios_enabled
    scenario_enabled = to_bool(scenario_flag)
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

    scenarios = []
    if scenario_enabled:
        scenario_table = QTable.optional(sop_scenarios, name='sop_scenarios', schema=SOP_SCENARIOS_SCHEMA)
        if scenario_table is None:
            raise Exception('sop_scenarios must contain at least one row when scenario analysis is enabled')
        scenario_table.assert_unique('Scenario')
        scenarios = scenario_table.select()

    use_stability = stability_enabled and (stability_penalty > 0 or max_change_pct > 0)
    previous_lookup = {}
    if use_stability:
        previous_lookup, has_previous_plan = _extract_previous_plan(sop_previous_plan, products, periods)
        if not has_previous_plan:
            raise Exception('sop_previous_plan is required when previous-plan stability is enabled')

    return {
        'plan': plan,
        'overtime_allowed': overtime is not None,
        'bom_enabled': bom is not None,
        'bom': bom,
        'overtime_capacity': overtime_capacity,
        'overtime_cost': overtime_cost,
        'scenarios': scenarios,
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

    plan = prepared['plan']
    bom = prepared['bom']
    bom_enabled = prepared['bom_enabled']
    overtime_allowed = prepared['overtime_allowed']
    overtime_capacity = prepared['overtime_capacity']
    overtime_cost = prepared['overtime_cost']
    scenarios = prepared['scenarios']
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
    procurement_allowed = to_bool(procurement_enabled)

    def solve_plan(plan, previous_lookup_map=None, build_details=True):
        local_products = plan['products']
        local_periods = plan['periods']
        local_demand = plan['demand']
        local_capacity = plan['capacity']
        local_opening_inventory = plan['opening_inventory']
        local_safety_stock = plan['safety_stock']
        local_production_cost = plan['production_cost']
        local_holding_cost = plan['holding_cost']
        local_max_production = plan['max_production']
        local_backlog_penalty = plan['backlog_penalty']
        local_setup_cost = plan['setup_cost']
        local_has_setup = bool(local_setup_cost)

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
                'Setup', [(p, t) for p in local_products for t in local_periods], lowBound=0, upBound=1,
                cat=pulp.LpBinary
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
                bom,
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
            objective_expr += stability_penalty * pulp.lpSum(
                abs_change[(p, t)] for p in local_products for t in local_periods)
            if objective == 'service_level':
                objective_expr = pulp.lpSum(fulfilled[(p, t)] for p in local_products for t in local_periods)
                objective_expr -= stability_penalty * pulp.lpSum(
                    abs_change[(p, t)] for p in local_products for t in local_periods)
                objective_expr -= 1e-6 * pulp.lpSum(production[(p, t)] for p in local_products for t in local_periods)
                objective_expr -= 1e-6 * pulp.lpSum(inventory[(p, t)] for p in local_products for t in local_periods)
                if backlog_allowed:
                    objective_expr -= 1e-6 * pulp.lpSum(backlog[(p, t)] for p in local_products for t in local_periods)

        prob += objective_expr

        for product in local_products:
            for period in local_periods:
                prob += production[(product, period)] <= float(
                    local_max_production[product]), f'max_prod_{product}_{period}'
                if has_positive_setup:
                    prob += (
                        production[(product, period)] <= float(local_max_production[product]) * setup_use[
                            (product, period)],
                        f'setup_link_{product}_{period}'
                    )

        for period in local_periods:
            prob += (
                pulp.lpSum(production[(product, period)] for product in local_products) <= float(
                    local_capacity[period]) + (overtime_use[period] if overtime_allowed else 0),
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
                overtime_cost_value = overtime_value * float(
                    overtime_cost.get(period, 0.0)) if overtime_allowed else 0.0
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

                if build_details and (
                    show_zero or demand_value > 0 or prod_value > 0 or inv_value > 0 or backlog_value > 0):
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
            sum(float(local_backlog_penalty[p]) * float(backlog[(p, t)].value() or 0.0) for p in local_products for t in
                local_periods)
            if backlog_allowed else 0.0
        )
        total_setup_cost = (
            sum(float(local_setup_cost[p]) * float(setup_use[(p, t)].value() or 0.0) for p in local_products for t in
                local_periods)
            if has_positive_setup else 0.0
        )
        if overtime_allowed:
            total_overtime_used = sum(float(overtime_use[period].value() or 0.0) for period in local_periods)
            total_overtime_cost = sum(
                float(overtime_cost.get(period, 0.0)) * float(overtime_use[period].value() or 0.0) for period in
                local_periods)
        total_procurement_cost = 0.0
        procurement_result = {}
        if procurement_ctx is not None:
            material_requirement_rows = []
            material_demand_map = {}
            product_totals = {
                product: sum(float(production[(product, period)].value() or 0.0) for period in local_periods)
                for product in local_products
            }
            for row in bom.select():
                product = row['Product']
                material = row['Material']
                qty_per_unit = row['Qty per Unit']
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
                    'Utilization %': round(
                        (purchased / float(procurement_ctx['supplier_capacity'][supplier]) * 100.0) if float(
                            procurement_ctx['supplier_capacity'][supplier]) else 0.0, 4),
                    'Fixed Cost': round(float(procurement_ctx['supplier_fixed_cost'][supplier]), 6),
                }
                if procurement_ctx['supplier_risk'] is not None:
                    supplier_row['Risk'] = _rounded(procurement_ctx['supplier_risk'][supplier])
                if procurement_ctx['supplier_quality'] is not None:
                    supplier_row['Quality'] = _rounded(procurement_ctx['supplier_quality'][supplier])
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

            total_procurement_cost = sum(
                float(procurement_ctx['pair_cost'][pair]) * float(procurement_ctx['purchase'][pair].value() or 0.0) for
                pair in procurement_ctx['pair_cost'])
            total_procurement_cost += sum(float(procurement_ctx['supplier_fixed_cost'][supplier]) * float(
                procurement_ctx['supplier_use'][supplier].value() or 0.0) for supplier in
                                          procurement_ctx['supplier_rows'])
            procurement_result = {
                'Procurement Summary': pd.DataFrame([{
                    'Model': 'Integrated Procurement',
                    'Status': status,
                    'Objective': round(total_procurement_cost, 6),
                    'Selected Suppliers': int(sum(
                        int(round(float(procurement_ctx['supplier_use'][supplier].value() or 0.0))) for supplier in
                        procurement_ctx['supplier_rows'])),
                    'Total Purchased': round(sum(float(procurement_ctx['purchase'][pair].value() or 0.0) for pair in
                                                 procurement_ctx['pair_cost']), 6),
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
                (sum(float(production[(p, period)].value() or 0.0) for p in local_products) / float(
                    local_capacity[period]) * 100.0)
                if float(local_capacity[period]) else 0.0
                for period in local_periods
            ) / len(local_periods)
        ) if local_periods else 0.0
        max_capacity_utilization = max(
            ((sum(float(production[(p, period)].value() or 0.0) for p in local_products) / float(
                local_capacity[period]) * 100.0)
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
                period_production = sum(
                    float(production[(product, period)].value() or 0.0) for product in local_products)
                cap = float(local_capacity[period])
                overtime_value = float(overtime_use[period].value() or 0.0) if overtime_allowed else 0.0
                capacity_rows.append({
                    'Period': period,
                    'Capacity': round(cap, 6),
                    'Overtime Capacity': round(float(overtime_capacity.get(period, 0.0)),
                                               6) if overtime_allowed else 0.0,
                    'Overtime Used': round(overtime_value, 6),
                    'Overtime Cost': round(float(overtime_cost.get(period, 0.0)) * overtime_value, 6),
                    'Production Used': round(period_production, 6),
                    'Capacity Utilization %': round(
                        (period_production / (cap + overtime_value) * 100.0) if (cap + overtime_value) else 0.0, 4),
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
        plan,
        previous_lookup_map=previous_lookup if use_stability else None,
        build_details=True,
    )

    output = _build_sop_output(
        base_result,
        use_stability,
        overtime_allowed,
        scenario_enabled,
        scenarios,
        plan,
        previous_lookup,
        objective,
        solve_plan,
    )
    output.update(base_result.get('procurement_result', {}))

    return output


def optima_sop__info():
    profile = 'sop'
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
            'supplier_item_cost': _optional_table_schema(
                table_supplier_item_cost,
                'supplier_item_cost',
                profile=profile,
            ),
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

