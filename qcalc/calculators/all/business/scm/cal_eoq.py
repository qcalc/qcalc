# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

from qcore import Qty, ucur
import numpy as np


def eoq__info():
    return {
        'title': 'Economic Order Quantity and Total Cost',
        'anyof': {'1': {'fields': ['unit_cost', 'cost_of_excess']},
                  '2': {'fields': ['cost_of_capital', 'cost_of_excess']}
                  },
        'kins': 'purcost, invlevel',
    }


def eoq__input(_kwargs):
    return {
        'demand': '1200 unit/yr',
        'transaction_cost': ucur('100 UNC'),
        'unit_cost': ucur('5 UNC/unit'),
        'cost_of_capital': ucur('0.2 UNC/UNC/yr'),
        'cost_of_excess': ucur('1 UNC/unit/yr'),
    }


def eoq(
    demand,
    transaction_cost,
    unit_cost,
    cost_of_capital,
    cost_of_excess,  # optionall
):
    demand_v = Qty(demand, 'unit/yr').val
    transaction_cost_q = Qty(transaction_cost, 'UNC')
    transaction_cost_v = transaction_cost_q.val
    currency = transaction_cost_q.uom
    unit_cost_v = Qty(unit_cost, 'UNC/unit').val  # can be posted with null value
    if unit_cost_v is None:
        cost_of_excess_v = Qty(cost_of_excess, 'UNC/unit/yr').val
    else:
        cost_of_excess_v = unit_cost_v * Qty(cost_of_capital, 'UNC/UNC/yr').val

    eco_order_qty = np.sqrt(2 * transaction_cost_v * demand_v / cost_of_excess_v)  # unit
    num_tran = demand_v / eco_order_qty  # 1/yr
    interval = 12 / num_tran  # mo
    inv_cost = eco_order_qty / 2 * cost_of_excess_v  # UNC/yr
    tran_cost = transaction_cost_v * num_tran  # UNC/yr
    operational_cost = inv_cost + tran_cost
    if unit_cost_v is None:
        material_cost = None
        total_cost = None
    else:
        material_cost = num_tran * eco_order_qty * unit_cost_v
        total_cost = material_cost + inv_cost + tran_cost

    return {
        'Order Interval': Qty(interval, 'mo'),
        'Material Cost Total': Qty(material_cost, f'{currency}/yr'),
        'Inventory Cost Total': Qty(inv_cost, f'{currency}/yr'),
        'Transaction Cost Total': Qty(tran_cost, f'{currency}/yr'),
        'Operational Cost Total': Qty(operational_cost, f'{currency}/yr'),
        'Total Cost': Qty(total_cost, f'{currency}/yr'),
        'Number of Transactions': Qty(num_tran, '1/yr'),
        'Economic Order Quantity': Qty(eco_order_qty, 'unit'),
    }
