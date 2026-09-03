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
    q_variable_cost = Qty(variable_cost_per_unit)
    q_selling_price = Qty(selling_price_per_unit)
    q_target_profit = Qty(target_profit)

    fixed = q_fixed_costs.to('USD').val
    variable = q_variable_cost.to('USD').val
    price = q_selling_price.to('USD').val
    target = q_target_profit.to('USD').val
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
                    Qty(break_even_revenue, 'USD'),
                    Qty(target_revenue, 'USD'),
                    Qty(scenario_revenue, 'USD'),
                ],
                [
                    'Variable Cost',
                    Qty(break_even_units * variable, 'USD'),
                    Qty(target_units * variable, 'USD'),
                    Qty(scenario_variable_cost, 'USD'),
                ],
                [
                    'Fixed Cost',
                    Qty(fixed, 'USD'),
                    Qty(fixed, 'USD'),
                    Qty(fixed, 'USD'),
                ],
                [
                    'Profit',
                    Qty(0, 'USD'),
                    Qty(target, 'USD'),
                    Qty(scenario_profit, 'USD'),
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
            contribution, 'USD'
        ),
        'contribution_margin_pct': Qty(
            contribution_pct * 100, 'pct'
        ),
        'break_even_quantity': break_even_units,
        'break_even_revenue': Qty(
            break_even_revenue, 'USD'
        ),
        'target_profit_quantity': target_units,
        'target_profit_revenue': Qty(
            target_revenue, 'USD'
        ),
        'scenario_profit': Qty(
            scenario_profit, 'USD'
        ),
    }
