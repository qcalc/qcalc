# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

from qcore import Qty


def make_buy__info():
    return {
        'title': 'Make vs Buy Analysis',
        'desc': (
            'Compare the full and relevant costs of making a product or '
            'service internally versus buying it externally, and determine '
            'the break-even quantity.'
        ),
    }


def make_buy(
    annual_quantity=10000,
    make_fixed_cost='50000 USD',
    make_unavoidable_fixed_cost='20000 USD',
    make_variable_cost='12 USD',
    buy_fixed_cost='5000 USD',
    buy_unavoidable_fixed_cost='0 USD',
    buy_unit_cost='18 USD',
):
    q_make_fixed = Qty(make_fixed_cost)
    q_make_unavoidable = Qty(make_unavoidable_fixed_cost)
    q_make_variable = Qty(make_variable_cost)

    q_buy_fixed = Qty(buy_fixed_cost)
    q_buy_unavoidable = Qty(buy_unavoidable_fixed_cost)
    q_buy_unit = Qty(buy_unit_cost)

    quantity = float(annual_quantity)

    make_fixed = q_make_fixed.to('USD').val
    make_unavoidable = q_make_unavoidable.to('USD').val
    make_variable = q_make_variable.to('USD').val

    buy_fixed = q_buy_fixed.to('USD').val
    buy_unavoidable = q_buy_unavoidable.to('USD').val
    buy_unit = q_buy_unit.to('USD').val

    # Full cost
    make_variable_total = quantity * make_variable
    buy_variable_total = quantity * buy_unit

    make_full_cost = make_fixed + make_variable_total
    buy_full_cost = buy_fixed + buy_variable_total

    full_cost_difference = buy_full_cost - make_full_cost

    # Relevant cost
    # Unavoidable fixed costs are excluded from the decision.
    make_relevant_fixed = make_fixed - make_unavoidable
    buy_relevant_fixed = buy_fixed - buy_unavoidable

    make_relevant_cost = (
        make_relevant_fixed +
        make_variable_total
    )

    buy_relevant_cost = (
        buy_relevant_fixed +
        buy_variable_total
    )

    relevant_cost_difference = (
        buy_relevant_cost -
        make_relevant_cost
    )

    # Break-even quantity based on relevant costs.
    variable_cost_difference = make_variable - buy_unit
    fixed_cost_difference = (
        buy_relevant_fixed -
        make_relevant_fixed
    )

    if variable_cost_difference:
        break_even_quantity = (
            fixed_cost_difference /
            variable_cost_difference
        )
    else:
        break_even_quantity = None

    # Effective unit costs
    make_full_unit_cost = (
        make_full_cost / quantity
        if quantity else None
    )

    buy_full_unit_cost = (
        buy_full_cost / quantity
        if quantity else None
    )

    make_relevant_unit_cost = (
        make_relevant_cost / quantity
        if quantity else None
    )

    buy_relevant_unit_cost = (
        buy_relevant_cost / quantity
        if quantity else None
    )

    # Decision based on relevant cost.
    if relevant_cost_difference > 0:
        preferred_option = 'Make'
    elif relevant_cost_difference < 0:
        preferred_option = 'Buy'
    else:
        preferred_option = 'Indifferent'

    return {
        'Full Cost Comparison': {
            'data': [
                [
                    'Fixed Cost',
                    Qty(make_fixed, 'USD'),
                    Qty(buy_fixed, 'USD'),
                    Qty(buy_fixed - make_fixed, 'USD'),
                ],
                [
                    'Variable Cost',
                    Qty(make_variable_total, 'USD'),
                    Qty(buy_variable_total, 'USD'),
                    Qty(
                        buy_variable_total -
                        make_variable_total,
                        'USD',
                    ),
                ],
                [
                    'Total Cost',
                    Qty(make_full_cost, 'USD'),
                    Qty(buy_full_cost, 'USD'),
                    Qty(full_cost_difference, 'USD'),
                ],
                [
                    'Effective Unit Cost',
                    Qty(make_full_unit_cost, 'USD'),
                    Qty(buy_full_unit_cost, 'USD'),
                    Qty(
                        buy_full_unit_cost -
                        make_full_unit_cost,
                        'USD',
                    ),
                ],
            ],
            'columns': ['Metric', 'Make', 'Buy', 'Buy − Make'],
        },

        'Relevant Cost Comparison': {
            'data': [
                [
                    'Relevant Fixed Cost',
                    Qty(make_relevant_fixed, 'USD'),
                    Qty(buy_relevant_fixed, 'USD'),
                    Qty(
                        buy_relevant_fixed -
                        make_relevant_fixed,
                        'USD',
                    ),
                ],
                [
                    'Variable Cost',
                    Qty(make_variable_total, 'USD'),
                    Qty(buy_variable_total, 'USD'),
                    Qty(
                        buy_variable_total -
                        make_variable_total,
                        'USD',
                    ),
                ],
                [
                    'Relevant Cost',
                    Qty(make_relevant_cost, 'USD'),
                    Qty(buy_relevant_cost, 'USD'),
                    Qty(relevant_cost_difference, 'USD'),
                ],
                [
                    'Effective Unit Cost',
                    Qty(make_relevant_unit_cost, 'USD'),
                    Qty(buy_relevant_unit_cost, 'USD'),
                    Qty(
                        buy_relevant_unit_cost -
                        make_relevant_unit_cost,
                        'USD',
                    ),
                ],
            ],
            'columns': ['Metric', 'Make', 'Buy', 'Buy − Make'],
        },

        'break_even_quantity': break_even_quantity,
        'cost_savings': Qty(
            abs(relevant_cost_difference),
            'USD',
        ),
        'preferred_option': preferred_option,
    }
