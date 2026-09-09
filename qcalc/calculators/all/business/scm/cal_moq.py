# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

from qcore import Qty
from calculators.all.business.scm.cal_eoq import eoq
from calculators.all.business.scm.cal_inventory import purcost


def moq__info():
    return {
        'title': 'Minimum Order Quantity (MOQ) Impact',
        'desc': (
            'Compare the Economic Order Quantity (EOQ) against a supplier-'
            'imposed Minimum Order Quantity (MOQ) and quantify the extra '
            'inventory and cost caused when the MOQ forces an order larger '
            'than the economically optimal quantity.'
        ),
        'anyof': {'1': {'fields': ['unit_cost', 'cost_of_excess']},
                  '2': {'fields': ['cost_of_capital', 'cost_of_excess']}
                  },
        'kins': 'eoq, purcost, invlevel',
        'proper': 'MOQ',
    }



def moq(
    demand='1200 unit/yr',
    transaction_cost='100 USD',
    unit_cost='5 USD/unit',
    cost_of_capital='0.2 peryr',
    cost_of_excess='1 USD/unit/yr',  # optional
    moq_qty='1000 unit',
):
    eoq_result = eoq(demand, transaction_cost, unit_cost, cost_of_capital, cost_of_excess)
    eco_order_qty_q = eoq_result['Economic Order Quantity']
    to_uom = eco_order_qty_q.uom

    moq_v = Qty(moq_qty, to_uom).val
    actual_order_qty_v = max(eco_order_qty_q.val, moq_v)
    is_binding = actual_order_qty_v > eco_order_qty_q.val + 1e-9  # MOQ forces a larger order than EOQ

    actual_result = purcost(
        demand=demand,
        transaction_cost=transaction_cost,
        unit_cost=unit_cost,
        cost_of_capital=cost_of_capital,
        cost_of_excess=cost_of_excess,
        order_quantity=Qty(actual_order_qty_v, to_uom),
    )

    def _delta(key):
        a, b = actual_result[key].val, eoq_result[key].val
        return None if a is None or b is None else a - b

    to_cur = Qty(transaction_cost).uom

    return {
        'Economic Order Quantity': eco_order_qty_q,
        'Supplier MOQ': Qty(moq_v, to_uom),
        'Actual Order Quantity': Qty(actual_order_qty_v, to_uom),
        'MOQ is Binding': is_binding,
        'Order Interval': actual_result['Order Interval'],
        'Number of Transactions': actual_result['Number of Transactions'],
        'Inventory Cost Total': actual_result['Inventory Cost Total'],
        'Transaction Cost Total': actual_result['Transaction Cost Total'],
        'Operational Cost Total': actual_result['Operational Cost Total'],
        'Material Cost Total': actual_result['Material Cost Total'],
        'Total Cost': actual_result['Total Cost'],
        'Extra Inventory Cost from MOQ': Qty(_delta('Inventory Cost Total'), f'{to_cur}/yr'),
        'Extra Operational Cost from MOQ': Qty(_delta('Operational Cost Total'), f'{to_cur}/yr'),
        'Extra Total Cost from MOQ': Qty(_delta('Total Cost'), f'{to_cur}/yr'),
    }
