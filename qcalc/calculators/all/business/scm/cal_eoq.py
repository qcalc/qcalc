# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

from qcore import Qty
import numpy as np


def eoq__info():
    return {
        'title': 'Economic Order Quantity and Total Cost',
        'anyof': {'1': {'fields': ['unit_cost', 'cost_of_excess']},
                  '2': {'fields': ['cost_of_capital', 'cost_of_excess']}
                  },
        'kins': 'purcost, invlevel',
    }


def eoq(
    demand='1200 unit/yr',
    transaction_cost='100 USD',
    unit_cost='5 USD/unit',
    cost_of_capital='0.2 peryr',
    cost_of_excess='1 USD/unit/yr',  # optionall
):
    demand_v = Qty(demand, 'unit/yr').val
    transaction_cost_q = Qty(transaction_cost)
    to_cur = transaction_cost_q.uom
    transaction_cost_v = transaction_cost_q.val
    unit_cost_v = Qty(unit_cost, f'{to_cur}/unit').val  # can be posted with null value
    if unit_cost_v is None:
        cost_of_excess_v = Qty(cost_of_excess, f'{to_cur}/unit/yr').val
    else:
        cost_of_excess_v = unit_cost_v * Qty(cost_of_capital, f'peryr').val

    eco_order_qty = np.sqrt(2 * transaction_cost_v * demand_v / cost_of_excess_v)  # unit
    num_tran = demand_v / eco_order_qty  # 1/yr
    interval = 12 / num_tran  # mo
    inv_cost = eco_order_qty / 2 * cost_of_excess_v  # $/yr
    tran_cost = transaction_cost_v * num_tran  # $/yr
    operational_cost = inv_cost + tran_cost
    if unit_cost_v is None:
        material_cost = None
        total_cost = None
    else:
        material_cost = num_tran * eco_order_qty * unit_cost_v
        total_cost = material_cost + inv_cost + tran_cost

    return {
        'Order Interval': Qty(interval, 'mo'),
        'Material Cost Total': Qty(material_cost, f'{to_cur}/yr'),
        'Inventory Cost Total': Qty(inv_cost, f'{to_cur}/yr'),
        'Transaction Cost Total': Qty(tran_cost, f'{to_cur}/yr'),
        'Operational Cost Total': Qty(operational_cost, f'{to_cur}/yr'),
        'Total Cost': Qty(total_cost, f'{to_cur}/yr'),
        'Number of Transactions': Qty(num_tran, 'nos/yr'),
        'Economic Order Quantity': Qty(eco_order_qty, 'unit'),
    }
