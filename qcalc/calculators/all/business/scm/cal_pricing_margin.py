# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

from qcore import Qty

def pricing_margin__info():
    return {
        'title': 'Pricing and Margin Calculator',
        'desc': (
            'Calculate profit, gross margin, markup, target pricing, '
            'discounted pricing, break-even price, and profit at quantity.'
        ),
    }


def pricing_margin(
    selling_price='100 USD',
    unit_cost='60 USD',
    target_margin='30 pct',
    target_price='100 USD',
    discount='10 pct',
    quantity=1000,
    fixed_cost='10000 USD',
    variable_cost='60 USD',
):
    q_selling_price = Qty(selling_price)
    q_unit_cost = Qty(unit_cost)
    q_target_margin = Qty(target_margin)
    q_target_price = Qty(target_price)
    q_discount = Qty(discount)
    q_fixed_cost = Qty(fixed_cost)
    q_variable_cost = Qty(variable_cost)

    price = q_selling_price.to('USD').val
    cost = q_unit_cost.to('USD').val
    target_margin_pct = q_target_margin.to('pct').val / 100.0
    target_price_value = q_target_price.to('USD').val
    discount_pct = q_discount.to('pct').val / 100.0
    fixed = q_fixed_cost.to('USD').val
    variable = q_variable_cost.to('USD').val
    qty = float(quantity)

    gross_profit = price - cost
    gross_margin = gross_profit / price if price else None
    markup = gross_profit / cost if cost else None

    required_price = (
        cost / (1.0 - target_margin_pct)
        if target_margin_pct < 1.0 else None
    )

    maximum_cost = target_price_value * (1.0 - target_margin_pct)

    discounted_price = price * (1.0 - discount_pct)
    margin_after_discount = (
        (discounted_price - cost) / discounted_price
        if discounted_price else None
    )

    break_even_price = (
        variable + fixed / qty
        if qty else None
    )

    profit_at_quantity = (
        (price - variable) * qty - fixed
    )

    return {
        'Gross Profit': Qty(gross_profit, 'USD'),
        'Gross Margin': Qty(gross_margin * 100, 'pct') if gross_margin is not None else None,
        'Markup': Qty(markup * 100, 'pct') if markup is not None else None,
        'Required Price': Qty(required_price, 'USD') if required_price is not None else None,
        'Maximum Cost': Qty(maximum_cost, 'USD'),
        'Discounted Price': Qty(discounted_price, 'USD'),
        'Margin After Discount': Qty(margin_after_discount * 100, 'pct') if margin_after_discount is not None else None,
        'Break-even Price': Qty(break_even_price, 'USD') if break_even_price is not None else None,
        'Profit at Quantity': Qty(profit_at_quantity, 'USD'),
    }
