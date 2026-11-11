# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

from qcore import Qty, qtbl, QTable

from .mod_building_materials import _num, _txt, building_materials, default_materials_table

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


def building_cost__info():
    return {
        'title': 'Quick Building Cost Estimator',
        'desc': (
            'Rough on-the-spot estimate of the construction cost and the major materials of a one or multi-storied building. '
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
                     'help_text': 'Soil condition affects the foundation cost and the footing concrete.'},
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
            'method': {
                'type': 'radio', 'initial': 'both',
                'choices': {'both': 'Both methods', 'detailed': 'Detailed', 'quick': 'Quick rule'},
                'help_text': 'Quick rule = area-based rule of thumb. Detailed = derived from concrete, steel, walls and mortar. '
                             'The headline quantities follow Detailed unless only Quick rule is chosen.'},
            'structure_density': {
                'type': 'radio', 'initial': 'typical',
                'choices': {'light': 'Light', 'lean': 'Lean', 'typical': 'Typical', 'heavy': 'Heavy'},
                'help_text': 'Light is for a 1-2 floor single-family house with short spans (about 4 m or less), normal seismic zone '
                             'and normal or good soil. Typical is the safer choice when unsure. Heavy is for long spans, '
                             'higher loads or taller buildings.'},
            'concrete_supply': {'type': 'radio', 'initial': 'site_mix',
                                'choices': {'site_mix': 'Site mix', 'ready_mix': 'Ready-mix'}},
            'mix': {'type': 'radio', 'initial': 'm20',
                    'choices': {'m20': 'M20 (1:1.5:3)', 'm15': 'M15 (1:2:4)', 'custom': 'Custom ratio'},
                    'help_text': 'Nominal mix by volume for site-mixed structural concrete.'},
            'mix_ratio': {'type': 'char',
                          'help_text': 'Used only for a custom mix: cement:sand:aggregate by volume, e.g. 1:1.5:3.'},
            'seismic': {'type': 'radio', 'initial': 'normal', 'choices': {'normal': 'Normal', 'high': 'High'},
                        'help_text': 'High seismic zone or coastal area adds about 15 pct to the reinforcement.'},
            'include_base_works': {'help_text': 'Include lean concrete (PCC) under footings and the ground floor, and brick soling.'},
            'finishes': {'help_text': 'Include plaster, floor screed, tiles and paint quantities.'},
            'include_labour': {
                'help_text': 'Include labour: a quick share of the estimated cost and detailed skilled and unskilled mandays. '
                             'Price the mandays with the cost calculator.'},
            'rooms': {
                'type': 'integer',
                'help_text': 'Enclosed rooms per floor: bedrooms, living or drawing room, dining if walled, kitchen, '
                             'bathrooms, store. Open-plan spaces count once; balconies, corridors and the stair do not count.'},
            'stairs': {'help_text': 'Number of staircases, or auto (1 when there is more than one floor, otherwise none).'},
            'storey_height': {'help_text': 'Floor-to-floor height.'},
            'brick_length': {'help_text': 'Brick length with unit. Bangladesh standard 9.5 inch, India traditional 230 mm, modular 190 mm.'},
            'brick_width': {'help_text': 'Brick width with unit. Bangladesh standard 4.5 inch, India traditional 115 mm, modular 90 mm.'},
            'brick_height': {'help_text': 'Brick height with unit. Bangladesh standard 2.75 inch, India traditional 75 mm, modular 90 mm.'},
            'ext_wall_thickness': {'help_text': 'auto = one brick length plus joint, or enter a length such as 5 inch.'},
            'int_wall_thickness': {'help_text': 'auto = one brick width (half-brick wall), or enter a length such as 5 inch.'},
            'joint_thickness': {'help_text': 'Mortar joint between bricks.'},
            'masonry_mortar': {'type': 'char', 'help_text': 'Cement:sand by volume for brickwork, e.g. 1:4.'},
            'plaster_mortar': {'type': 'char',
                               'help_text': 'Cement:sand by volume for plaster and floor screed, e.g. 1:4.'},
            'mortar_dry_factor': {'help_text': 'Dry-to-wet volume of mortar, usually 1.27 to 1.33.'},
            'concrete_dry_factor': {'help_text': 'Dry-to-wet volume of concrete, usually 1.52 to 1.57.'},
            'cement_bag_volume': {'help_text': 'Volume of one cement bag, 1.225 ft³ for 50 kg at 1440 kg/m³.'},
            'brick_wastage': {'help_text': 'Brick breakage and waste.'},
            'labour_productivity': {
                'help_text': 'Labour efficiency against the book norms in the materials table. 100 pct = book norms (manual handling); '
                             '80 pct raises mandays by 25 pct. Use less than 100 pct for monsoon, small crews, no hoist or congested sites.'},
            'materials_table': {
                'help_text': 'Editable coefficients for the materials estimate. Keep unique (Group, Key) rows and numeric values.',
                'attrs': {'readonly_cols': ['Group', 'Key', 'Label'], 'fixed_headers': ['Group', 'Key', 'Label', 'Value']}
            },
        },
        'input_blocks': [
            {'column': 1, 'tabs': [
                {'title': 'Building', 'fields': 'plot_length, plot_width, floors, coverage'},
                {'title': 'Specification', 'fields': 'base_rate, quality, location, soil'},
                {'title': 'Assumptions',
                 'fields': 'foundation_share, foundation_increase_per_floor, contractor_markup, contingency, range_pct'},
                {'title': 'Settings', 'fields': 'factors_table'},
            ]},
            {'column': 1, 'tabs': [
                {'title': 'Materials',
                 'fields': 'method, structure_density, concrete_supply, mix, mix_ratio, seismic, include_base_works, '
                           'finishes, include_labour'},
                {'title': 'Walls and Stairs',
                 'fields': 'rooms, stairs, storey_height, brick_length, brick_width, brick_height, '
                           'ext_wall_thickness, int_wall_thickness'},
                {'title': 'Constants',
                 'fields': 'joint_thickness, masonry_mortar, plaster_mortar, mortar_dry_factor, concrete_dry_factor, '
                           'cement_bag_volume, brick_wastage, labour_productivity'},
                {'title': 'Materials Table', 'fields': 'materials_table'},
            ]},
        ],
        'step2': [
            {'step': 'run', 'func': 'cost', 'caption': 'Calculate Cost of Materials',
             'spec': '~Footprint Area, ~Total Built-up Area, ~Concrete'},
        ],
    }


def building_cost(plot_length='37 ft', plot_width='27 ft', floors=1, coverage='100 pct',
                  base_rate='3000 BDT/sft', quality='standard', location='urban', soil='normal',
                  factors_table: qtbl = _default_factors_table(),
                  foundation_share='15 pct', foundation_increase_per_floor='20 pct',
                  contractor_markup='0 pct', contingency='5 pct', range_pct='15 pct',
                  method='both', structure_density='typical', concrete_supply='site_mix', mix='m20',
                  mix_ratio='1:1.5:3', seismic='normal', include_base_works=True, finishes=True,
                  rooms=6, stairs='auto', storey_height='10 ft',
                  brick_length='9.5 inch', brick_width='4.5 inch', brick_height='2.75 inch',
                  ext_wall_thickness='auto', int_wall_thickness='auto',
                  joint_thickness='10 mm', masonry_mortar='1:4', plaster_mortar='1:4',
                  mortar_dry_factor=1.33, concrete_dry_factor=1.54, cement_bag_volume='1.225 ft^3/bag',
                  brick_wastage='5 pct', labour_productivity='100 pct', include_labour=True,
                  materials_table: qtbl = default_materials_table()):
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

    result = {
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
    result.update(building_materials(
        plot_length=plot_length, plot_width=plot_width, coverage=coverage, floors=floors, soil=soil,
        materials_table=materials_table, method=method, structure_density=structure_density,
        concrete_supply=concrete_supply, mix=mix, mix_ratio=mix_ratio, seismic=seismic,
        include_base_works=include_base_works, finishes=finishes, rooms=rooms, stairs=stairs,
        storey_height=storey_height, brick_length=brick_length, brick_width=brick_width,
        brick_height=brick_height, ext_wall_thickness=ext_wall_thickness, int_wall_thickness=int_wall_thickness,
        joint_thickness=joint_thickness, masonry_mortar=masonry_mortar, plaster_mortar=plaster_mortar,
        mortar_dry_factor=mortar_dry_factor, concrete_dry_factor=concrete_dry_factor,
        cement_bag_volume=cement_bag_volume, brick_wastage=brick_wastage, include_labour=include_labour,
        labour_productivity=labour_productivity, estimated_cost=total, currency=to_cur))
    return result
