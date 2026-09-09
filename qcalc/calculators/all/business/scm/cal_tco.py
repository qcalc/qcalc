# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

from qcore import Qty, qtbl
from qapi import qdf, qsum
from calc import QResults
from calculators.all.finance.cal_fin import circ

# keyword -> row label match (case-insensitive substring) for the standard cost categories
_ROW_KEYWORDS = {
    'purchase': 'purchase',
    'freight': 'freight',
    'installation': 'installation',
    'operating': 'operating',
    'maintenance': 'maintenance',
    'financing': 'financing',
    'disposal': 'disposal',
    'residual': 'residual',
}

_METRICS = [
    'Initial Cost',
    'Operating Cost (PV)',
    'Maintenance Cost (PV)',
    'Financing Cost (PV)',
    'Disposal Cost (PV)',
    'Residual Value (PV)',
    'Total Cost of Ownership (TCO)',
    'Annualized TCO',
    'Cost / Hour',
    '% vs Lowest TCO',
    'Rank',
]


def _row_index(labels, keyword):
    for i, label in enumerate(labels):
        if keyword in str(label).lower():
            return i
    return None


def _num(v):
    return float(v) if v not in (None, '') else 0.0


def _growing_annuity_pv(cashflow1, rate, growth, periods):
    # PV of a cost that starts at cashflow1 and grows each year at 'growth', discounted at 'rate'
    if periods <= 1e-10:
        return 0.0
    if abs(rate - growth) < 1e-10:
        return cashflow1 * periods / (1 + rate) if abs(1 + rate) > 1e-10 else cashflow1 * periods
    return cashflow1 * (1 - ((1 + growth) / (1 + rate)) ** periods) / (rate - growth)


def tco__info():
    return {
        'title': 'Total Cost of Ownership (TCO) Comparison',
        'desc': (
            'Compare the total cost of ownership of two or more suppliers '
            '(or alternatives) side by side across the standard cost '
            'categories - purchase, freight, installation, operating, '
            'maintenance, financing, disposal and residual value - '
            'discounted over an analysis period, with optional annual cost '
            'escalation. Leave any irrelevant cost row as zero.'
        ),
        'tags': 'business, procurement, tco, supplier, comparison, finance',
        'outcol': 'result',
        'proper': 'TCO',
    }


def tco(
    # Supplier A (higher upfront, lower running cost) and Supplier C (lower
    # upfront, higher running cost) are deliberately close competitors -
    # a small change in analysis_period or discount_rate flips the winner
    # between them. Supplier B is a clearly-worse third option for contrast.
    costs: qtbl = {
        'columns': ['Cost Component', 'Supplier A', 'Supplier B', 'Supplier C'],
        'data': [
            ['Purchase Price', 80000, 70000, 75000],
            ['Freight', 5000, 8000, 5000],
            ['Installation', 10000, 15000, 8000],
            ['Annual Operating Cost', 6000, 9000, 7500],
            ['Annual Maintenance', 2000, 4000, 2500],
            ['Annual Financing Cost', 0, 0, 0],
            ['Disposal Cost', 0, 0, 0],
            ['Residual Value', 5000, 3000, 4000],
        ],
    },
    analysis_period='5 yr',
    discount_rate='8 pct/yr',
    cost_escalation_rate='0 pct/yr',
    usage='2000 hr/yr',
):
    df = qdf(costs)
    labels = df['Cost Component']
    row_idx = {name: _row_index(labels, kw) for name, kw in _ROW_KEYWORDS.items()}

    periods = Qty(analysis_period, 'yr').val
    rate = circ(discount_rate, 'yr').val / 100
    growth = circ(cost_escalation_rate, 'yr').val / 100
    usage_per_yr = Qty(usage, 'hr/yr').val

    if abs(rate) > 1e-10:
        capital_recovery_factor = rate / (1 - (1 + rate) ** -periods)
    elif periods > 1e-10:
        capital_recovery_factor = 1.0 / periods
    else:
        capital_recovery_factor = 0.0
    discount_factor_n = (1 + rate) ** -periods

    suppliers = costs['columns'][1:]
    values_by_metric = {m: [] for m in _METRICS}

    for supplier in suppliers:
        col = [_num(v) for v in df[supplier]]

        def at(key):
            i = row_idx[key]
            return col[i] if i is not None and i < len(col) else 0.0

        initial_cost = at('purchase') + at('freight') + at('installation')
        operating_pv = _growing_annuity_pv(at('operating'), rate, growth, periods)
        maintenance_pv = _growing_annuity_pv(at('maintenance'), rate, growth, periods)
        financing_pv = _growing_annuity_pv(at('financing'), rate, growth, periods)
        disposal_pv = at('disposal') * discount_factor_n
        residual_pv = at('residual') * discount_factor_n

        tco_total = qsum([initial_cost, operating_pv, maintenance_pv, financing_pv, disposal_pv, -residual_pv])
        annualized_tco = tco_total * capital_recovery_factor
        cost_per_hour = annualized_tco / usage_per_yr if usage_per_yr else None

        # '% vs Lowest TCO' and 'Rank' are filled in below, once every supplier's TCO is known
        for metric, value in zip(_METRICS[:-2], [
            initial_cost, operating_pv, maintenance_pv, financing_pv,
            disposal_pv, residual_pv, tco_total, annualized_tco, cost_per_hour,
        ]):
            values_by_metric[metric].append(value)

    tco_values = values_by_metric['Total Cost of Ownership (TCO)']
    best_tco = min(tco_values)
    best_supplier = suppliers[tco_values.index(best_tco)]
    values_by_metric['% vs Lowest TCO'] = [
        (t / best_tco - 1) * 100 if best_tco else None for t in tco_values
    ]
    values_by_metric['Rank'] = ['Best' if t == best_tco else 'OK' for t in tco_values]

    comparison = {
        'columns': ['Metric'] + list(suppliers),
        'data': [[metric] + values_by_metric[metric] for metric in _METRICS],
    }

    chart = QResults.df2chart(
        qdf({'columns': ['Supplier', 'TCO'], 'data': [[s, t] for s, t in zip(suppliers, tco_values)]}),
        x_column='Supplier',
        y_columns=['TCO'],
        chart_title='Total Cost of Ownership by Supplier',
        chart_type='bars',
        ylabel='TCO',
    )

    return {
        'TCO Comparison': comparison,
        'Lowest TCO Supplier': best_supplier,
        'Chart': chart,
    }
