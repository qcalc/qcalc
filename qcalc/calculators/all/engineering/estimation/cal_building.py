# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

from qcore import Qty, qtbl, QTable

__all__ = ['building_cost', 'building_cost__info']

# Factors are kept outside the calculation so they can be tuned
# without touching the logic. They are illustrative, not quotations.
QUALITY = {'economy': ('Economy', 0.8), 'standard': ('Standard', 1.0), 'premium': ('Premium', 1.5)}
LOCATION = {'rural': ('Rural', 0.6), 'semi_urban': ('Semi-urban', 0.8),
            'urban': ('Urban', 1.0), 'metropolitan': ('Metropolitan', 1.5)}
SOIL = {'good': ('Good', 0.8), 'normal': ('Normal', 1.0), 'poor': ('Poor', 1.5)}


def _default_factors_table():
    return {
        'columns': ['Category', 'Key', 'Label', 'Factor'],
        'data': [
                    ['quality', key, label, factor]
                    for key, (label, factor) in QUALITY.items()
                ] + [
                    ['location', key, label, factor]
                    for key, (label, factor) in LOCATION.items()
                ] + [
                    ['soil', key, label, factor]
                    for key, (label, factor) in SOIL.items()
                ],
    }


def _txt(value):
    return str(value).strip()


def _num(value, unit='unit'):
    text = _txt(value).replace(',', '')
    try:
        return float(text)
    except Exception:
        return Qty(text, unit).val


def building_cost__info():
    return {
        'title': 'Quick Building Cost Estimator',
        'desc': (
            'Rough on-the-spot estimate of the construction cost of a one or multi-storied building. '
            'Enter the base rate in any currency, e.g. 3000 BDT/sft, 25 USD/sft. '
            'Preliminary budget only, not a substitute for a BOQ, drawings, soil investigation or local quotations.'
        ),
        'calculate': 'Estimate',
        'schema': {
            'plot_length': {'help_text': 'Overall plot/building length. Example: 37 ft or 11.3 m.'},
            'plot_width': {'help_text': 'Overall plot/building width. Example: 27 ft or 8.2 m.'},
            'floors': {'type': 'integer', 'help_text': 'Number of identical floors above the foundation.'},
            'coverage': {'help_text': 'Share of length × width actually built, e.g. 90 pct for open courts.'},
            'base_rate': {
                'help_text': 'All-inclusive rate per built-up area for standard quality, urban, normal soil.'},
            'quality': {'type': 'radio', 'choices': {k: v[0] for k, v in QUALITY.items()}, 'initial': 'standard'},
            'location': {'type': 'choice', 'choices': {k: v[0] for k, v in LOCATION.items()}, 'initial': 'urban'},
            'soil': {'type': 'radio', 'choices': {k: v[0] for k, v in SOIL.items()}, 'initial': 'normal',
                     'help_text': 'Soil condition affects only the foundation cost.'},
            'foundation_share': {'help_text': 'Share of the base rate attributed to the foundation.'},
            'foundation_increase_per_floor': {
                'help_text': 'Extra foundation cost for every floor above the first (heavier loading).'},
            'contractor_markup': {'help_text': 'Contractor markup/profit applied on subtotal, e.g. 10 pct.'},
            'contingency': {'help_text': 'Risk buffer added after markup, e.g. 5 pct.'},
            'range_pct': {'help_text': 'Low/high estimate range around total, e.g. 15 pct.'},
            'factors_table': {
                'help_text': 'Editable factor table for quality, location and soil. Keep unique (Category, Key) rows.',
                'attrs': {'readonly_cols': ['Category', 'Key', 'Label'], 'fixed_headers': ['Category', 'Key', 'Label', 'Factor']}
            },
        },
        'input_blocks': [{
            'column': 1,
            'tabs': [
                {'title': 'Building', 'fields': 'plot_length, plot_width, floors, coverage'},
                {'title': 'Specification', 'fields': 'base_rate, quality, location, soil'},
                {'title': 'Assumptions',
                 'fields': 'foundation_share, foundation_increase_per_floor, contractor_markup, contingency, range_pct'},
                {'title': 'Settings', 'fields': 'factors_table'},
            ],
        }],
    }


def building_cost(plot_length='37 ft', plot_width='27 ft', floors=1, coverage='100 pct',
                  base_rate='3000 BDT/sft', quality='standard', location='urban', soil='normal',
                  factors_table: qtbl = _default_factors_table(),
                  foundation_share='15 pct', foundation_increase_per_floor='20 pct',
                  contractor_markup='0 pct', contingency='5 pct', range_pct='15 pct'):
    factors_qt = QTable(factors_table, name='factors_table', schema={
        'Category': {'cast': lambda v: _txt(v).lower()},
        'Key': str,
        'Label': {'type': str, 'required': False},
        'Factor': {'cast': _num},
    })
    factors_qt.assert_columns(['Category', 'Key', 'Label', 'Factor'])
    factors_qt.assert_unique_pairs('Category', 'Key')
    factors_map = factors_qt.to_map(['Category', 'Key'], ['Label', 'Factor'])
    for category, key in factors_map:
        if category not in {'quality', 'location', 'soil'}:
            raise ValueError(f'Invalid factors_table: Unknown category "{category}".')

    if ('quality', quality) not in factors_map:
        raise ValueError(f'Quality key "{quality}" not found in factors_table.')
    if ('location', location) not in factors_map:
        raise ValueError(f'Location key "{location}" not found in factors_table.')
    if ('soil', soil) not in factors_map:
        raise ValueError(f'Soil key "{soil}" not found in factors_table.')

    base = Qty(base_rate)
    to_cur = base.uom.split('/')[0]
    rate = base.to(f'{to_cur}/ft^2').val
    floors = int(floors)
    if floors < 1:
        raise ValueError('Number of floors must be at least 1.')

    footprint = Qty(plot_length, 'ft').val * Qty(plot_width, 'ft').val * Qty(coverage, 'unit').val
    total_area = footprint * floors
    share = Qty(foundation_share, 'unit').val
    markup_v = Qty(contractor_markup, 'unit').val
    contingency_v = Qty(contingency, 'unit').val
    range_v = Qty(range_pct, 'unit').val

    def estimate(quality_key):
        foundation = (footprint * rate * share * factors_map[('location', location)][1] * factors_map[('soil', soil)][1]
                      * (1 + Qty(foundation_increase_per_floor, 'unit').val * (floors - 1)))
        superstructure = (total_area * rate * (1 - share) * factors_map[('quality', quality_key)][1]
                          * factors_map[('location', location)][1])
        subtotal = foundation + superstructure
        markup_cost = subtotal * markup_v
        contingency_cost = (subtotal + markup_cost) * contingency_v
        return foundation, superstructure, markup_cost, contingency_cost, subtotal + markup_cost + contingency_cost

    foundation, superstructure, markup_cost, contingency_cost, total = estimate(quality)

    quality_keys = [k for (cat, k) in factors_map if cat == 'quality']
    comparison = [[factors_map[('quality', k)][0], Qty(t, to_cur), Qty(t / total_area, f'{to_cur}/ft^2')]
                  for k in quality_keys for t in [estimate(k)[-1]]]

    return {
        'Estimated Cost': Qty(total, to_cur),
        'Low Estimate': Qty(total * (1 - range_v), to_cur),
        'High Estimate': Qty(total * (1 + range_v), to_cur),
        'Cost per unit Area': Qty(total / total_area, f'{to_cur}/ft^2'),
        'Cost per Floor': Qty(total / floors, to_cur),
        'Footprint Area': Qty(footprint, 'ft^2'),
        'Total Built-up Area': Qty(total_area, 'ft^2'),
        'Cost Breakdown': {
            'data': [['Foundation', Qty(foundation, to_cur)],
                     ['Superstructure and finishing', Qty(superstructure, to_cur)],
                     ['Contractor markup', Qty(markup_cost, to_cur)],
                     ['Contingency', Qty(contingency_cost, to_cur)],
                     ['Total', Qty(total, to_cur)]],
            'columns': ['Component', 'Cost'],
        },
        'Quality Comparison': {
            'data': comparison,
            'columns': ['Quality', 'Total Cost', 'Cost per sft'],
        },
    }
