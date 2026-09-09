# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

import numpy as np

from qcore import Qty, qtbl
from qapi import qdf


def supdisc__info():
    return {
        'title': 'Supplier Discount Analysis',
        'desc': (
            'Compare all-units supplier quantity-discount tiers, including '
            'purchase, ordering, and inventory carrying cost, and identify '
            'the tier and order quantity with the lowest annual cost.'
        ),
        'tags': 'business, procurement, supplier, discount, inventory, eoq',
        'proper': 'Supplier Discount Analysis',
        'kins': 'eoq, purcost, moq, invlevel',
        'outcol': 'result',
    }


def supdisc(
    demand='12000 unit/yr',
    transaction_cost='100 USD',
    cost_of_capital='0.2 peryr',
    discount_tiers: qtbl = {
        'columns': ['Discount Tier', 'Minimum Order Quantity', 'Unit Price'],
        'data': [
            ['No discount', 0, 10.00],
            ['5% discount', 2000, 9.50],
            ['10% discount', 4000, 9.00],
        ],
    },
):
    demand_v = Qty(demand, 'unit/yr').val
    transaction_cost_q = Qty(transaction_cost)
    to_cur = transaction_cost_q.uom
    transaction_cost_v = transaction_cost_q.val
    cost_of_capital_v = Qty(cost_of_capital, 'peryr').val

    if demand_v <= 0:
        raise ValueError('Demand must be greater than zero.')
    if transaction_cost_v < 0:
        raise ValueError('Transaction Cost cannot be negative.')
    if cost_of_capital_v < 0:
        raise ValueError('Cost of Capital cannot be negative.')

    df = qdf(discount_tiers)
    required_columns = ['Discount Tier', 'Minimum Order Quantity', 'Unit Price']
    missing_columns = [column for column in required_columns if column not in df.columns]
    if missing_columns:
        raise ValueError(f"Discount Tier Table is missing: {', '.join(missing_columns)}.")
    if not len(df):
        raise ValueError('Discount Tier Table needs at least one tier.')

    tiers = []
    for tier_name, minimum_qty, unit_price in zip(
        df['Discount Tier'], df['Minimum Order Quantity'], df['Unit Price']
    ):
        tier_name = str(tier_name)
        minimum_qty = float(minimum_qty)
        unit_price = float(unit_price)
        if minimum_qty < 0:
            raise ValueError('Minimum Order Quantity cannot be negative.')
        if unit_price <= 0:
            raise ValueError('Unit Price must be greater than zero.')

        holding_cost = unit_price * cost_of_capital_v
        eoq = np.sqrt(2 * transaction_cost_v * demand_v / holding_cost) if holding_cost else 0.0
        order_qty = max(eoq, minimum_qty)
        order_count = demand_v / order_qty if order_qty else 0.0
        purchase_cost = demand_v * unit_price
        average_inventory = order_qty / 2
        carrying_cost = average_inventory * holding_cost
        ordering_cost = order_count * transaction_cost_v
        total_cost = purchase_cost + carrying_cost + ordering_cost
        tiers.append({
            'name': tier_name,
            'minimum_qty': minimum_qty,
            'unit_price': unit_price,
            'eoq': eoq,
            'order_qty': order_qty,
            'purchase_cost': purchase_cost,
            'average_inventory': average_inventory,
            'average_inventory_value': average_inventory * unit_price,
            'carrying_cost': carrying_cost,
            'ordering_cost': ordering_cost,
            'total_cost': total_cost,
        })

    base_total_cost = tiers[0]['total_cost']
    lowest_cost = min(tier['total_cost'] for tier in tiers)
    recommended = next(tier for tier in tiers if tier['total_cost'] == lowest_cost)
    comparison = {
        'columns': [
            'Discount Tier', 'Minimum Order Quantity', 'Unit Price',
            'Economic Order Quantity', 'Order Quantity', 'Purchase Cost',
            'Average Inventory', 'Average Inventory Value', 'Inventory Carrying Cost',
            'Transaction Cost', 'Total Annual Cost', 'Savings vs No-Discount Tier',
            'Recommendation',
        ],
        'data': [
            [
                tier['name'],
                Qty(tier['minimum_qty'], 'unit'),
                Qty(tier['unit_price'], f'{to_cur}/unit'),
                Qty(tier['eoq'], 'unit'),
                Qty(tier['order_qty'], 'unit'),
                Qty(tier['purchase_cost'], f'{to_cur}/yr'),
                Qty(tier['average_inventory'], 'unit'),
                Qty(tier['average_inventory_value'], f'{to_cur}'),
                Qty(tier['carrying_cost'], f'{to_cur}/yr'),
                Qty(tier['ordering_cost'], f'{to_cur}/yr'),
                Qty(tier['total_cost'], f'{to_cur}/yr'),
                Qty(base_total_cost - tier['total_cost'], f'{to_cur}/yr'),
                'Recommended' if tier is recommended else '',
            ]
            for tier in tiers
        ],
    }

    return {
        'Discount Analysis': comparison,
        'Recommended Discount Tier': recommended['name'],
        'Recommended Order Quantity': Qty(recommended['order_qty'], 'unit'),
        'Lowest Total Annual Cost': Qty(lowest_cost, f'{to_cur}/yr'),
        'Annual Savings vs No-Discount Tier': Qty(base_total_cost - lowest_cost, f'{to_cur}/yr'),
    }
