# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

import pandas as pd
import pulp
from qcore import qtable, QTable, Qty
from qcore import validate_schema_if_needed
from qcore import normalize_name, val2fraction

from calc import FERT_NUTRIENTS_SCHEMA, FERT_PRODUCTS_SCHEMA
from calc import field_show_zero, table_fert_nutrients, table_fert_products
from calc import safe_objective_value, solver, slack_table

_PRODUCT_COLUMNS = {'fertilizer', 'price', 'min qty', 'max qty'}
_TOL = 1e-7


def optima_fertilizer(
    nutrients: qtable,
    fertilizers: qtable,
    area_unit,
    quantity_unit,
    currency,
    show_zero,
):
    validate_schema_if_needed('optima_fertilizer')
    needs = QTable(nutrients, name='nutrients', schema=FERT_NUTRIENTS_SCHEMA)
    products = QTable(fertilizers, name='fertilizers', schema=FERT_PRODUCTS_SCHEMA)
    # units are labels only: every table value is already in these units, so nothing is converted
    area_u, qty_u, cur_u = (Qty(1, u).uom for u in (area_unit, quantity_unit, currency))
    per_area = f'{qty_u}/{area_u}'
    if not products.nrows:
        raise Exception('fertilizers must contain at least one fertilizer row')

    names = products.assert_unique('Fertilizer')
    rows = {row['Fertilizer']: row for row in products.select()}
    content_cols = {normalize_name(c): c for c in products.columns if normalize_name(c) not in _PRODUCT_COLUMNS}

    nutrient_names = needs.assert_unique('Nutrient')
    need = {}
    for row in needs.select():
        name = row['Nutrient']
        soil = row.get('Soil Supply') or 0.0
        cap = row.get('Max Supply')
        net = max(0.0, row['Required'] - soil)
        if cap is not None and cap < net:
            raise Exception(f'Max Supply is below the fertilizer requirement for nutrient: {name}')
        if normalize_name(name) not in content_cols:
            raise Exception(f"No '{name} %' content column found in fertilizers")
        need[name] = {'required': row['Required'], 'soil': soil, 'net': net, 'cap': cap}

    # every content column is reported; only the required nutrients are constrained
    content = {
        f: {col: val2fraction(rows[f][col] or 0, f'fertilizers.{col} ({f})') for col in content_cols.values()}
        for f in names
    }
    for f, by_col in content.items():
        if any(v < 0 or v > 1 for v in by_col.values()):
            raise Exception(f'Nutrient content must be between 0% and 100% for fertilizer: {f}')
    nutrient_col = {n: content_cols[normalize_name(n)] for n in nutrient_names}

    price = {f: rows[f]['Price'] for f in names}
    lo = {f: rows[f].get('Min Qty') or 0.0 for f in names}
    hi = {f: rows[f].get('Max Qty') for f in names}
    for f in names:
        if hi[f] is not None and lo[f] > hi[f]:
            raise Exception(f'Min Qty cannot exceed Max Qty for fertilizer: {f}')

    prob = pulp.LpProblem('optima_fertilizer', pulp.LpMinimize)
    x = {f: pulp.LpVariable(f'Qty_{f}', lowBound=lo[f], upBound=hi[f]) for f in names}
    prob += pulp.lpSum(price[f] * x[f] for f in names)

    def supplied(col):
        return pulp.lpSum(content[f][col] * x[f] for f in names)

    for n in nutrient_names:
        key = n.replace(' ', '_')
        prob += supplied(nutrient_col[n]) >= need[n]['net'], f'need_{key}'
        if need[n]['cap'] is not None:
            prob += supplied(nutrient_col[n]) <= need[n]['cap'], f'cap_{key}'

    prob.solve(solver())
    status = pulp.LpStatus[prob.status]

    qty = {f: float(x[f].value() or 0.0) for f in names}
    cost_area = sum(price[f] * qty[f] for f in names)

    plan_rows = []
    for f in names:
        if not (show_zero or qty[f] > _TOL):
            continue
        plan_rows.append({
            'Fertilizer': f,
            f'Qty ({per_area})': round(qty[f], 4),
            f'Price ({cur_u}/{qty_u})': round(price[f], 6),
            f'Cost ({cur_u}/{area_u})': round(price[f] * qty[f], 4),
            **{f'{col} ({per_area})': round(content[f][col] * qty[f], 4) for col in content_cols.values()},
        })

    balance_rows = []
    for n in nutrient_names:
        got = sum(content[f][nutrient_col[n]] * qty[f] for f in names)
        info = need[n]
        con = prob.constraints.get(f"need_{n.replace(' ', '_')}")
        balance_rows.append({
            'Nutrient': n,
            f'Required ({per_area})': round(info['required'], 4),
            f'Soil Supply ({per_area})': round(info['soil'], 4),
            f'Fertilizer Need ({per_area})': round(info['net'], 4),
            f'Fertilizer Supply ({per_area})': round(got, 4),
            f'Surplus ({per_area})': round(got - info['net'], 4) or 0.0,
            f'Cost of 1 More {qty_u} ({cur_u})': None if con is None or con.pi is None else round(float(con.pi), 6),
        })
    extra_rows = [
        {'Nutrient': col, f'Supply ({per_area})': round(sum(content[f][col] * qty[f] for f in names), 4)}
        for col in content_cols.values() if col not in nutrient_col.values()
    ]

    sensitivity_rows = []
    for f in names:
        used = qty[f] > _TOL
        drop = None if used or x[f].dj is None else max(0.0, float(x[f].dj))
        sensitivity_rows.append({
            'Fertilizer': f,
            f'Price ({cur_u}/{qty_u})': round(price[f], 6),
            'Used': 'Yes' if used else 'No',
            'Price Drop to Enter': None if drop is None else round(drop, 6),
            'Break-even Price': None if drop is None else round(price[f] - drop, 6),
        })

    out = {
        'Summary': pd.DataFrame([{
            'Model': 'Fertilizer Optimization',
            'Status': status,
            'Objective': safe_objective_value(prob),
            f'Cost ({cur_u}/{area_u})': round(cost_area, 4),
            'Fertilizers Used': sum(qty[f] > _TOL for f in names),
        }]),
        'Decision Table': pd.DataFrame(plan_rows),
        'Nutrient Balance': pd.DataFrame(balance_rows),
    }
    if extra_rows:
        out['Other Nutrients'] = pd.DataFrame(extra_rows)
    out['Price Sensitivity'] = pd.DataFrame(sensitivity_rows)
    out['Constraint Slack'] = slack_table(prob)
    return out


def optima_fertilizer__info():
    return {
        'title': 'Optimization: Fertilizer Mix',
        'desc': (
            'Find the cheapest combination of fertilizers that meets crop nutrient requirements, '
            'after soil credits and optional nutrient caps and per-product limits. '
            'Also shows nutrient balance, shadow prices and the price at which an unused fertilizer would enter the mix.'
        ),
        'calculate': 'Solve',
        'schema': {
            'nutrients': table_fert_nutrients('nutrients'),
            'fertilizers': table_fert_products('fertilizers'),
            'area_unit': {
                'initial': 'ha',
                'help_text': (
                    'Area unit the nutrient requirements and Min/Max Qty refer to. '
                    'It only labels the results; no values are converted.'
                ),
            },
            'quantity_unit': {
                'initial': 'kg',
                'help_text': (
                    'Quantity unit of fertilizer and nutrient amounts, and the basis of Price. '
                    'It only labels the results; no values are converted.'
                ),
            },
            'currency': {
                'initial': 'usd',
                'help_text': 'Currency of the fertilizer Price (price per quantity unit).',
            },
            'show_zero': field_show_zero(),
        },
        'layout': 'lr',
        'tags': 'agriculture, fertilizer, NPK, crop nutrition, optimization, linear programming, cost',
    }
