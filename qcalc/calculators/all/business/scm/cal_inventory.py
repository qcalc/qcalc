# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

from qcore import Qty, ucur
import numpy as np
from calc import results2chart, show_choice


def purcost__info(): return {
    'title': 'Calculate Purchase Cost',
    'anyof': {'1': {'fields': ['unit_cost', 'cost_of_excess']},
              '2': {'fields': ['cost_of_capital', 'cost_of_excess']}
              },
    'kins': 'eoq, invlevel',
}


def purcost(
    demand='1200 unit/yr',
    transaction_cost='100 USD',
    unit_cost='5 USD/unit',
    cost_of_capital='0.2 peryr',
    cost_of_excess='1 USD/unit/yr',  # optional
    order_quantity='300 unit',
):
    demand_v = Qty(demand, 'unit/yr').val
    transaction_cost_q = Qty(transaction_cost)
    to_cur = transaction_cost_q.uom
    transaction_cost_v = transaction_cost_q.val
    unit_cost_v = Qty(unit_cost, f'{to_cur}/unit').val  # can be posted with null value
    if unit_cost_v is None:
        cost_of_excess_v = Qty(cost_of_excess, f'{to_cur}/unit/yr').val
    else:
        cost_of_excess_v = unit_cost_v * Qty(cost_of_capital, 'peryr').val

    order_quantity_v = Qty(order_quantity, 'unit').val  # unit
    num_tran = demand_v / order_quantity_v  # 1/yr
    interval = 12 / num_tran  # mo
    inv_cost = order_quantity_v / 2 * cost_of_excess_v  # USD/yr
    tran_cost = transaction_cost_v * num_tran  # USD/yr
    operational_cost = inv_cost + tran_cost  # USD/yr
    if unit_cost_v is None:
        material_cost = None
        total_cost = None
    else:
        material_cost = num_tran * order_quantity_v * unit_cost_v
        total_cost = material_cost + inv_cost + tran_cost  # USD/yr

    eco_order_qty = np.sqrt(2 * transaction_cost_v * demand_v / cost_of_excess_v)  # unit

    return {
        'Order Interval': Qty(interval, 'mo'),
        'Material Cost Total': Qty(material_cost, f'{to_cur}/yr'),
        'Inventory Cost Total': Qty(inv_cost, f'{to_cur}/yr'),
        'Transaction Cost Total': Qty(tran_cost, f'{to_cur}/yr'),
        'Operational Cost Total': Qty(operational_cost, f'{to_cur}/yr'),
        'Total Cost': Qty(total_cost, f'{to_cur}/yr'),
        'Number of Transactions': Qty(num_tran, '1/yr'),
        'Economic Order Quantity': Qty(eco_order_qty, 'unit')
    }


def invlevel__info():
    return {
        'title': 'Calculate Inventory Level',
        'desc': 'Calculate inventory level as stock is issued, ordered and received',
        'schema': {
            'show': show_choice
        },
        'kins': 'eoq, purcost',
        'outcol': ['chart__r']
    }


def invlevel(
    demand='1200.0 unit/yr',
    current_stock='150.0 unit',
    reorder_point='200.0 unit',
    reorder_quantity='500.0 unit',
    lead_time='30.0 d',
    time_horizon='1.0 yr',
    calculate_every='1.0 wk',
    chart_columns: str = '', chart_units: str = '', show='both'
):
    demand = Qty(demand, 'unit/d').val
    current_stock = Qty(current_stock, 'unit').val
    reorder_point = Qty(reorder_point, 'unit').val
    reorder_quantity = Qty(reorder_quantity, 'unit').val
    lead_time = int(Qty(lead_time, 'd').val)
    time_horizon = int(Qty(time_horizon, 'd').val)
    calculate_every = int(Qty(calculate_every, 'd').val)

    if calculate_every < 1:
        raise Exception(f"Error (INVLEVEL): calculate at least every 1 day")

    order_placed = []
    results = []
    stock_consumed = 0
    stock_promised = 0
    results.append({
        "Day": 0,
        "Current Stock": current_stock,
        "Order Placed": '',
        "Goods Received": '',
        "Reorder Point": reorder_point,
        "Stock Promised": stock_promised})
    for i in range(1, time_horizon):
        po = ''
        gr = ''
        stock_consumed = demand
        if len(order_placed) > 0 and i == order_placed[0] + lead_time:
            order_placed.pop(0)
            stock_received = reorder_quantity
            stock_promised -= reorder_quantity
            gr = 'GR'
        else:
            stock_received = 0
        current_stock = current_stock - stock_consumed + stock_received
        if current_stock + stock_promised <= reorder_point:
            order_placed.append(i)
            stock_promised += reorder_quantity
            po = 'PO'
        if i % calculate_every == 0 or po or gr:
            results.append({
                "Day": i,
                "Current Stock": current_stock,
                "Order Placed": po,
                "Goods Received": gr,
                "Reorder Point": reorder_point,
                "Stock Promised": stock_promised})
    # print(results)
    return results2chart(
        results=results, chart_x_axis='Day', chart_columns=chart_columns,
        chart_units=chart_units, show=show, title='Inventory Levels Over Time'
    )
