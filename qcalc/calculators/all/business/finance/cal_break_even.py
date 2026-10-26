# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

from qcore import Qty

def break_even__info():
    return {
        'title': 'Break-Even Analysis',
        'desc': (
            'Calculate break-even quantity and revenue, contribution margin, '
            'target-profit requirements, and profit at a selected sales volume.'
        ),
    }


def break_even(
    fixed_costs='10000 USD',
    variable_cost_per_unit='20 USD',
    selling_price_per_unit='50 USD',
    target_profit='6000 USD',
    scenario_units=500,
):
    q_fixed_costs = Qty(fixed_costs)
    to_cur = q_fixed_costs.uom
    q_variable_cost = Qty(variable_cost_per_unit)
    q_selling_price = Qty(selling_price_per_unit)
    q_target_profit = Qty(target_profit)

    fixed = q_fixed_costs.to(to_cur).val
    variable = q_variable_cost.to(to_cur).val
    price = q_selling_price.to(to_cur).val
    target = q_target_profit.to(to_cur).val

    contribution = price - variable
    contribution_pct = contribution / price

    break_even_units = fixed / contribution
    break_even_revenue = break_even_units * price
    break_even_variable_cost = break_even_units * variable
    break_even_total_cost = break_even_variable_cost + fixed

    target_units = (fixed + target) / contribution
    target_revenue = target_units * price
    target_variable_cost = target_units * variable
    target_total_cost = target_variable_cost + fixed
    target_profit = target_revenue - target_total_cost

    sc_units = float(scenario_units)
    scenario_revenue = sc_units * price
    scenario_variable_cost = sc_units * variable
    scenario_total_cost = scenario_variable_cost + fixed
    scenario_profit = scenario_revenue - scenario_total_cost

    return {
        'Break-Even Analysis': {
            'data': [
                [
                    'Units',
                    break_even_units,
                    target_units,
                    sc_units,
                ],
                [
                    'Revenue',
                    Qty(break_even_revenue, to_cur),
                    Qty(target_revenue, to_cur),
                    Qty(scenario_revenue, to_cur),
                ],
                [
                    'Variable Cost',
                    Qty(break_even_variable_cost, to_cur),
                    Qty(target_variable_cost, to_cur),
                    Qty(scenario_variable_cost, to_cur),
                ],
                [
                    'Fixed Cost',
                    Qty(fixed, to_cur),
                    Qty(fixed, to_cur),
                    Qty(fixed, to_cur),
                ],
                [
                    'Total Cost',
                    Qty(break_even_total_cost, to_cur),
                    Qty(target_total_cost, to_cur),
                    Qty(scenario_total_cost, to_cur),
                ],
                [
                    'Profit',
                    Qty(0, to_cur),
                    Qty(target_profit, to_cur),
                    Qty(scenario_profit, to_cur),
                ],
            ],
            'columns': [
                'Metric',
                'Break-Even',
                'Target Profit',
                'Scenario',
            ],
        },
        'contribution_margin_per_unit': Qty(
            contribution, to_cur
        ),
        'contribution_margin_pct': Qty(
            contribution_pct * 100, 'pct'
        ),
        'break_even_quantity': break_even_units,
        'break_even_revenue': Qty(
            break_even_revenue, to_cur
        ),
        'scenario_revenue': Qty(
            scenario_revenue, to_cur
        ),
        'scenario_total_cost': Qty(
            scenario_total_cost, to_cur
        ),
        'scenario_profit': Qty(
            scenario_profit, to_cur
        ),
    }
