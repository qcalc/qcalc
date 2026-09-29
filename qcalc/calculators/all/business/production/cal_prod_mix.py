# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

import pulp
import qconst

from qcore import Qty, qtbl
from qutil import is_debug
from calc import require_columns


def production_mix_profit__info():
    return {
        'title': 'Optimization: Production Mix Profitability',
        'desc': (
            'Optimize product quantities to maximize monthly contribution profit '
            'subject to machine time, labor time, demand, and ramp-change constraints.'
        ),
        'tags': 'business, production, optimization, linear',
        'layout': 'tb',
        'out1': '1-3,17-21',
    }


def production_mix_profit(
    products: qtbl = {
        'columns': [
            'Product',
            'Selling Price | USD/unit',
            'Variable Cost | USD/unit',
            'Machine Time | min/unit',
            'Labor Time | min/unit',
            'Max Demand | unit/mo',
            'Current Production Quantity | unit/mo',
            'Max Ramp Change | unit/mo',
        ],
        'data': [
            ['A', 50, 30, 5, 3, 7500, 4200, 1200],
            ['B', 80, 48, 7, 4, 5000, 2600, 900],
            ['C', 110, 60, 15, 8, 2000, 900, 500],
        ],
    },
    available_machine_time='1000 hr/mo',
    available_labor_time='800 hr/mo',
):
    required_cols = [
        'Product',
        'Selling Price',
        'Variable Cost',
        'Machine Time',
        'Labor Time',
        'Max Demand',
        'Current Production Quantity',
        'Max Ramp Change',
    ]
    required_col_uoms = {
        'Selling Price': 'USD/unit',
        'Variable Cost': 'USD/unit',
        'Machine Time': 'hr/unit',
        'Labor Time': 'hr/unit',
        'Max Demand': 'unit/mo',
        'Current Production Quantity': 'unit/mo',
        'Max Ramp Change': 'unit/mo',
    }

    def _split_header_uom(title):
        text = str(title).strip()
        if qconst.TBL_UOM_SEP not in text:
            return text, None
        base, uom = text.split(qconst.TBL_UOM_SEP, 1)
        return base.strip(), uom.strip()

    def _qty_cell_value(raw_value, header_title, target_uom):
        _, header_uom = _split_header_uom(header_title)
        if header_uom:
            try:
                scalar_value = float(raw_value)
            except Exception as e:
                raise Exception(
                    f"Expected unitless numeric value because column '{header_title}' declares unit '{header_uom}'. "
                    f"Found: {raw_value}"
                ) from e
            return Qty(scalar_value, header_uom, target_uom).val
        return Qty(raw_value, target_uom).val

    try:
        resolved_cols = require_columns(
            products,
            'products',
            required_cols,
            required_col_uoms=required_col_uoms,
        )
    except Exception as e:
        return str(e)

    rows = products.get('data', [])
    if not rows:
        return 'Products table is empty.'

    col_idx = {c: products['columns'].index(resolved_cols[c]) for c in required_cols}

    q_cap = Qty(available_machine_time, 'hr/mo')
    cap_hr_mo = float(q_cap.val)
    q_labor_cap = Qty(available_labor_time, 'hr/mo')
    labor_cap_hr_mo = float(q_labor_cap.val)

    # Use first product currency as reporting currency.
    selling_price_col = resolved_cols['Selling Price']
    _, price_header_uom = _split_header_uom(selling_price_col)
    if price_header_uom:
        to_cur = price_header_uom.split('/')[0].strip()
    else:
        first_price = Qty(rows[0][col_idx['Selling Price']])
        to_cur = first_price.uom.split('/')[0]

    product_names = []
    margin_per_unit = {}
    machine_time_hr_per_unit = {}
    labor_time_hr_per_unit = {}
    demand_cap_unit_per_mo = {}
    current_qty_unit_per_mo = {}
    max_ramp_unit_per_mo = {}

    for i, row in enumerate(rows):
        try:
            p = str(row[col_idx['Product']]).strip()
            if not p:
                p = f'Product {i + 1}'

            price = _qty_cell_value(row[col_idx['Selling Price']], resolved_cols['Selling Price'], f'{to_cur}/unit')
            var_cost = _qty_cell_value(row[col_idx['Variable Cost']], resolved_cols['Variable Cost'], f'{to_cur}/unit')
            margin = float(price - var_cost)

            mtime = _qty_cell_value(row[col_idx['Machine Time']], resolved_cols['Machine Time'], 'hr/unit')
            ltime = _qty_cell_value(row[col_idx['Labor Time']], resolved_cols['Labor Time'], 'hr/unit')
            dcap = _qty_cell_value(row[col_idx['Max Demand']], resolved_cols['Max Demand'], 'unit/mo')
            current_q = _qty_cell_value(
                row[col_idx['Current Production Quantity']],
                resolved_cols['Current Production Quantity'],
                'unit/mo',
            )
            ramp = _qty_cell_value(row[col_idx['Max Ramp Change']], resolved_cols['Max Ramp Change'], 'unit/mo')

            product_names.append(p)
            margin_per_unit[p] = margin
            machine_time_hr_per_unit[p] = float(mtime)
            labor_time_hr_per_unit[p] = float(ltime)
            demand_cap_unit_per_mo[p] = max(0.0, float(dcap))
            current_qty_unit_per_mo[p] = max(0.0, float(current_q))
            max_ramp_unit_per_mo[p] = max(0.0, float(ramp))
        except Exception as e:
            return f'Invalid value in products row {i + 1}: {e}'

    prob = pulp.LpProblem('ProductionMixProfitability', pulp.LpMaximize)

    qty = {
        p: pulp.LpVariable(f'Qty_{p}', lowBound=0, upBound=demand_cap_unit_per_mo[p], cat='Continuous')
        for p in product_names
    }

    prob += pulp.lpSum(margin_per_unit[p] * qty[p] for p in product_names)
    prob += pulp.lpSum(machine_time_hr_per_unit[p] * qty[p] for p in product_names) <= cap_hr_mo
    prob += pulp.lpSum(labor_time_hr_per_unit[p] * qty[p] for p in product_names) <= labor_cap_hr_mo

    for p in product_names:
        current_q = current_qty_unit_per_mo[p]
        ramp = max_ramp_unit_per_mo[p]
        prob += qty[p] <= current_q + ramp
        prob += qty[p] >= current_q - ramp

    prob.solve(pulp.PULP_CBC_CMD(msg=is_debug()))
    status = pulp.LpStatus[prob.status]
    if status != 'Optimal':
        return {
            'Optimization Status': status,
            'Message': 'No optimal solution found. Check constraints and input values.',
        }

    mix_rows = []
    total_units = 0.0
    total_used_hours = 0.0
    total_labor_used_hours = 0.0
    total_profit = 0.0
    total_current_units = 0.0
    total_current_used_hours = 0.0
    total_current_labor_used_hours = 0.0
    total_current_profit = 0.0
    ramp_limited_products = 0

    for p in product_names:
        qv = float(qty[p].value() or 0.0)
        used_hrs = qv * machine_time_hr_per_unit[p]
        labor_used_hrs = qv * labor_time_hr_per_unit[p]
        profit = qv * margin_per_unit[p]
        current_qv = current_qty_unit_per_mo[p]
        current_used_hrs = current_qv * machine_time_hr_per_unit[p]
        current_labor_used_hrs = current_qv * labor_time_hr_per_unit[p]
        current_profit = current_qv * margin_per_unit[p]
        qty_gap = qv - current_qv
        profit_gap = profit - current_profit
        ramp = max_ramp_unit_per_mo[p]
        at_ramp_limit = abs(abs(qty_gap) - ramp) <= 1e-8

        total_units += qv
        total_used_hours += used_hrs
        total_labor_used_hours += labor_used_hrs
        total_profit += profit
        total_current_units += current_qv
        total_current_used_hours += current_used_hrs
        total_current_labor_used_hours += current_labor_used_hrs
        total_current_profit += current_profit
        if at_ramp_limit:
            ramp_limited_products += 1
        mix_rows.append([
            p,
            Qty(current_qv, 'unit/mo'),
            Qty(qv, 'unit/mo'),
            Qty(qty_gap, 'unit/mo'),
            Qty(max_ramp_unit_per_mo[p], 'unit/mo'),
            Qty(demand_cap_unit_per_mo[p], 'unit/mo'),
            Qty(machine_time_hr_per_unit[p], 'hr/unit'),
            Qty(labor_time_hr_per_unit[p], 'hr/unit'),
            Qty(current_used_hrs, 'hr/mo'),
            Qty(used_hrs, 'hr/mo'),
            Qty(current_labor_used_hrs, 'hr/mo'),
            Qty(labor_used_hrs, 'hr/mo'),
            Qty(margin_per_unit[p], f'{to_cur}/unit'),
            Qty(current_profit, f'{to_cur}/mo'),
            Qty(profit, f'{to_cur}/mo'),
            Qty(profit_gap, f'{to_cur}/mo'),
            at_ramp_limit,
        ])

    utilization = 0.0 if cap_hr_mo <= 0 else (total_used_hours / cap_hr_mo) * 100.0
    current_utilization = 0.0 if cap_hr_mo <= 0 else (total_current_used_hours / cap_hr_mo) * 100.0
    labor_utilization = 0.0 if labor_cap_hr_mo <= 0 else (total_labor_used_hours / labor_cap_hr_mo) * 100.0
    current_labor_utilization = 0.0 if labor_cap_hr_mo <= 0 else (total_current_labor_used_hours / labor_cap_hr_mo) * 100.0

    executive_summary = {
        'columns': ['Metric', 'Current', 'Optimized', 'Change'],
        'data': [
            [
                'Contribution Profit (Monthly)',
                Qty(total_current_profit, f'{to_cur}/mo'),
                Qty(total_profit, f'{to_cur}/mo'),
                Qty(total_profit - total_current_profit, f'{to_cur}/mo'),
            ],
            [
                'Contribution Profit (Annual)',
                Qty(total_current_profit * 12.0, f'{to_cur}/yr'),
                Qty(total_profit * 12.0, f'{to_cur}/yr'),
                Qty((total_profit - total_current_profit) * 12.0, f'{to_cur}/yr'),
            ],
            [
                'Machine Utilization',
                Qty(current_utilization, 'pct'),
                Qty(utilization, 'pct'),
                Qty(utilization - current_utilization, 'pct'),
            ],
            [
                'Labor Utilization',
                Qty(current_labor_utilization, 'pct'),
                Qty(labor_utilization, 'pct'),
                Qty(labor_utilization - current_labor_utilization, 'pct'),
            ],
            [
                'Total Production',
                Qty(total_current_units, 'unit/mo'),
                Qty(total_units, 'unit/mo'),
                Qty(total_units - total_current_units, 'unit/mo'),
            ],
            [
                'Products at Ramp Limit',
                '-',
                ramp_limited_products,
                '-',
            ],
        ],
    }

    return {
        'Optimization Status': status,
        'Executive Summary': executive_summary,
        'Optimal Production Mix': {
            'columns': [
                'Product',
                'Current Quantity',
                'Optimal Quantity',
                'Quantity Gap (Optimal - Current)',
                'Max Ramp Change',
                'Demand Limit',
                'Machine Time per Unit',
                'Labor Time per Unit',
                'Current Machine Hours',
                'Machine Hours Used',
                'Current Labor Hours',
                'Labor Hours Used',
                'Contribution Margin per Unit',
                'Current Contribution Profit',
                'Contribution Profit',
                'Contribution Profit Gap',
                'Ramp Limit Binding',
            ],
            'data': mix_rows,
        },
        'Current Total Production': Qty(total_current_units, 'unit/mo'),
        'Total Production': Qty(total_units, 'unit/mo'),
        'Current Machine Time Used': Qty(total_current_used_hours, 'hr/mo'),
        'Machine Time Used': Qty(total_used_hours, 'hr/mo'),
        'Unused Machine Time': Qty(cap_hr_mo - total_used_hours, 'hr/mo'),
        'Current Utilization': Qty(current_utilization, 'pct'),
        'Utilization': Qty(utilization, 'pct'),
        'Current Labor Time Used': Qty(total_current_labor_used_hours, 'hr/mo'),
        'Labor Time Used': Qty(total_labor_used_hours, 'hr/mo'),
        'Unused Labor Time': Qty(labor_cap_hr_mo - total_labor_used_hours, 'hr/mo'),
        'Current Labor Utilization': Qty(current_labor_utilization, 'pct'),
        'Labor Utilization': Qty(labor_utilization, 'pct'),
        'Ramp-Limited Products': ramp_limited_products,
        'Current Total Contribution Profit': Qty(total_current_profit, f'{to_cur}/mo'),
        'Total Contribution Profit': Qty(total_profit, f'{to_cur}/mo'),
        'Contribution Profit Improvement': Qty(total_profit - total_current_profit, f'{to_cur}/mo'),
        'Annual Contribution Profit Improvement': Qty((total_profit - total_current_profit) * 12.0, f'{to_cur}/yr'),
        'Annual Contribution Profit': Qty(total_profit * 12.0, f'{to_cur}/yr'),
    }
