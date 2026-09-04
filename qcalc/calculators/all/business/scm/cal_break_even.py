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
    target_profit='5000 USD',
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
    units = float(scenario_units)

    contribution = price - variable
    contribution_pct = contribution / price

    break_even_units = fixed / contribution
    break_even_revenue = break_even_units * price

    target_units = (fixed + target) / contribution
    target_revenue = target_units * price

    scenario_revenue = units * price
    scenario_variable_cost = units * variable
    scenario_profit = scenario_revenue - scenario_variable_cost - fixed

    return {
        'Break-Even Analysis': {
            'data': [
                [
                    'Units',
                    break_even_units,
                    target_units,
                    units,
                ],
                [
                    'Revenue',
                    Qty(break_even_revenue, to_cur),
                    Qty(target_revenue, to_cur),
                    Qty(scenario_revenue, to_cur),
                ],
                [
                    'Variable Cost',
                    Qty(break_even_units * variable, to_cur),
                    Qty(target_units * variable, to_cur),
                    Qty(scenario_variable_cost, to_cur),
                ],
                [
                    'Fixed Cost',
                    Qty(fixed, to_cur),
                    Qty(fixed, to_cur),
                    Qty(fixed, to_cur),
                ],
                [
                    'Profit',
                    Qty(0, to_cur),
                    Qty(target, to_cur),
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
        'target_profit_quantity': target_units,
        'target_profit_revenue': Qty(
            target_revenue, to_cur
        ),
        'scenario_profit': Qty(
            scenario_profit, to_cur
        ),
    }
