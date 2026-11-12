# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

"""Material quantities of a building: Quick rule (area based) and Detailed (derived) methods.

See qcalc_res/_docs_/building-materials-estimator-spec.md for the formulas and sources.
"""

from math import ceil, hypot, sqrt
from types import SimpleNamespace

from calc import QCost
from qcore import Qty, QTable, qwarn

PRESETS = ['light', 'lean', 'typical', 'heavy']
FLAG_PCT = 20
FRAME = ('footing', 'column', 'beam', 'slab')

# Every coefficient lives in this table so users can edit it (materials_table); values are illustrative, not quotations.
_ROWS = {
    'density': dict(light=0.024, lean=0.030, typical=0.034, heavy=0.040),  # frame m3 per sft BUA
    'steel_scale': dict(light=0.80, lean=1.0, typical=1.0, heavy=1.0),
    'member_share': dict(footing=0.12, column=0.18, beam=0.22, slab=0.48),
    'steel_kg_m3': dict(footing=65, column=190, beam=130, slab=75, stair=100, lintel=70),
    'formwork_m2_m3': dict(footing=4, column=12, beam=11, slab=8, stair=5, lintel=12),
    'floor_scale': {'1_2': 1.0, '3_4': 1.1, '5_6': 1.2, '7_plus': 1.3},
    'soil_scale': dict(good=0.9, normal=1.0, poor=1.3),
    'seismic_steel': dict(normal=1.0, high=1.15),
    'steel_lap_wastage': dict(all=0.07),
    'mix_m10': dict(cement=1, sand=3, aggregate=6),
    'mix_m15': dict(cement=1, sand=2, aggregate=4),
    'mix_m20': dict(cement=1, sand=1.5, aggregate=3),
    'pcc': dict(thickness_mm=75, footing_depth_m=0.45, footing_projection=1.2),
    'geometry': dict(opening_share=0.15, beam_slab_depth_ft=1.25),
    'stair': dict(width_m=1.0, riser_m=0.17, tread_m=0.25, waist_m=0.15, landing_count=1),
    'lintel': dict(opening_height_m=1.5, bearing_allowance=1.25, depth_m=0.15),
    'finish': dict(plaster_in=0.5, screed_in=2, tiled_share=0.9, paint_coats=2, paint_sft_per_l=100),
    'wastage': dict(cement=0.03, sand=0.07, aggregate=0.05, tiles=0.10, paint=0.05, ready_mix=0.03),
    'quick_cement_bag_sft': dict(low=0.40, typical=0.45, high=0.50),
    'quick_steel_kg_sft': dict(low=3.5, typical=4.0, high=4.5),
    'quick_concrete_m3_sft': dict(low=0.033, typical=0.038, high=0.042),
    'quick_sand_cft_sft': dict(low=1.1, typical=1.2, high=1.3),
    'quick_aggregate_cft_sft': dict(low=1.35, typical=1.45, high=1.6),
    'quick_bricks_sft': dict(low=8, typical=8.5, high=9),
    'quick_area_sft_sft': dict(formwork=3.0, plaster=4.0, paint=4.2, tiles=1.0),
    'quick_rmc_removed': dict(cement=0.67, sand=0.44, aggregate=1.0),
    # mandays per unit of finished work; only brickwork, concrete and steel have published sources
    'labour_skilled': dict(brickwork_m3=0.9, plaster_m2=0.12, screed_tile_m2=0.16, concrete_m3=0.2, pcc_m3=0.10,
                           formwork_m2=0.25, steel_tonne=0.10, paint_m2=0.04, soling_m2=0.05),
    'labour_unskilled': dict(brickwork_m3=1.4, plaster_m2=0.12, screed_tile_m2=0.16, concrete_m3=2.25, pcc_m3=1.0,
                             formwork_m2=0.25, steel_tonne=1.9, paint_m2=0.04, soling_m2=0.10),
    'labour_rmc_scale': dict(skilled=1.0, unskilled=0.5),  # structural concrete placed from ready-mix
}
_BANDS = [g for g in _ROWS if g.startswith('quick_') and 'low' in _ROWS[g]]
_TRADES = {  # key -> (title, quantity kind)
    'brickwork_m3': ('Brickwork', 'm3'), 'plaster_m2': ('Plaster', 'area'),
    'screed_tile_m2': ('Screed and tiles', 'area'), 'concrete_m3': ('Structural concrete', 'm3'),
    'pcc_m3': ('PCC', 'm3'), 'formwork_m2': ('Formwork', 'area'), 'steel_tonne': ('Steel', 'tonne'),
    'paint_m2': ('Paint', 'area'), 'soling_m2': ('Soling', 'area'),
}

# Likely cause shown beside a flagged row: (row, +1 when Detailed is higher / -1 when lower)
_NOTES = {
    ('Bricks', 1): 'Thick (one-brick) external walls or many rooms',
    ('Bricks', -1): 'Thin walls, large opening share or few rooms',
    ('Aggregate', -1): 'Sunshades, parapets, tanks and boundary works are not modelled; light or lean density',
    ('Cement', 1): 'Thick walls, plaster or screed share',
    ('Cement', -1): 'Minor concrete not modelled; ready-mix share; light or lean density',
    ('Steel', 1): 'High seismic zone or heavy density',
    ('Steel', -1): 'Light or lean density (the Quick rule has no light-house band)',
    ('Concrete', 1): 'Heavy density or tall building',
    ('Concrete', -1): 'Light density; sunshades and other minor concrete not modelled',
    ('Plaster area', 1): 'Many rooms or tall storey',
    ('Plaster area', -1): 'Few rooms or large opening share',
}
_KINDS = {'Cement': 'bag', 'Steel': 'kg', 'Concrete': 'm3', 'Sand': 'vol', 'Aggregate': 'vol', 'Bricks': 'nos',
          'Formwork': 'area', 'Plaster area': 'area', 'Paint area': 'area', 'Floor tile area': 'area'}

# What each row means, for the Label column of the Coefficients table: (text, unit), {k} is the key in plain words.
_GROUP_LABELS = {
    'density': ('Frame concrete, {k}', 'm³ per sft of floor'),
    'steel_scale': ('Frame steel scale, {k}', 'multiplier on member steel'),
    'member_share': ('Share of frame concrete in {k}', 'fraction of total'),
    'steel_kg_m3': ('Steel in {k}', 'kg per m³ of concrete'),
    'formwork_m2_m3': ('Formwork for {k}', 'm² per m³ of concrete'),
    'floor_scale': ('Concrete and steel on {k} floors', 'multiplier'),
    'soil_scale': ('Footing concrete on {k} soil', 'multiplier'),
    'seismic_steel': ('Steel in {k} seismic zone', 'multiplier'),
    'steel_lap_wastage': ('Steel lap and wastage', 'fraction added'),
    'mix_m10': ('M10 mix (used for PCC), {k}', 'parts by volume'),
    'mix_m15': ('M15 mix, {k}', 'parts by volume'),
    'mix_m20': ('M20 mix, {k}', 'parts by volume'),
    'wastage': ('Wastage of {k}', 'fraction added'),
    'quick_cement_bag_sft': ('Quick rule: cement, {k}', 'bags per sft'),
    'quick_steel_kg_sft': ('Quick rule: steel, {k}', 'kg per sft'),
    'quick_concrete_m3_sft': ('Quick rule: concrete, {k}', 'm³ per sft'),
    'quick_sand_cft_sft': ('Quick rule: sand, {k}', 'cft per sft'),
    'quick_aggregate_cft_sft': ('Quick rule: coarse aggregate, {k}', 'cft per sft'),
    'quick_bricks_sft': ('Quick rule: bricks, {k}', 'pcs per sft'),
    'quick_area_sft_sft': ('Quick rule: {k} area', 'sft per sft of floor'),
    'quick_rmc_removed': ('Quick rule: {k} that is concrete', 'fraction, dropped for ready-mix'),
    'labour_rmc_scale': ('Ready-mix: {k} labour on concrete', 'fraction of site-mix mandays'),
}
_ROW_LABELS = {  # rows whose key is not a plain word
    ('pcc', 'thickness_mm'): ('PCC layer thickness', 'mm'),
    ('pcc', 'footing_depth_m'): ('Average footing depth', 'm'),
    ('pcc', 'footing_projection'): ('PCC width beyond the footing', 'multiplier on footing plan'),
    ('geometry', 'opening_share'): ('Doors and windows', 'fraction of wall area'),
    ('geometry', 'beam_slab_depth_ft'): ('Beam and slab depth taken off the wall height', 'ft'),
    ('stair', 'width_m'): ('Stair width', 'm'),
    ('stair', 'riser_m'): ('Stair riser height', 'm'),
    ('stair', 'tread_m'): ('Stair tread width', 'm'),
    ('stair', 'waist_m'): ('Stair waist slab thickness', 'm'),
    ('stair', 'landing_count'): ('Mid-landings per stair', 'number'),
    ('lintel', 'opening_height_m'): ('Average opening height', 'm'),
    ('lintel', 'bearing_allowance'): ('Lintel length for bearing', 'multiplier on opening width'),
    ('lintel', 'depth_m'): ('Lintel depth', 'm'),
    ('finish', 'plaster_in'): ('Plaster thickness', 'inch'),
    ('finish', 'screed_in'): ('Floor screed thickness', 'inch'),
    ('finish', 'tiled_share'): ('Tiled part of the floor', 'fraction of floor area'),
    ('finish', 'paint_coats'): ('Paint coats', 'number'),
    ('finish', 'paint_sft_per_l'): ('Paint coverage', 'sft per litre per coat'),
}
_KEY_WORDS = {'1_2': '1-2', '3_4': '3-4', '5_6': '5-6', '7_plus': '7 or more', 'ready_mix': 'ready-mix'}
_TRADE_UNITS = {'m3': 'm³', 'area': 'm²', 'tonne': 'tonne'}


def _label(group, key):
    if (group, key) in _ROW_LABELS:
        text, unit = _ROW_LABELS[(group, key)]
    elif group in ('labour_skilled', 'labour_unskilled'):
        title, kind = _TRADES[key]
        text = f'{group[7:].capitalize()} labour, {title if title.isupper() else title.lower()}'
        unit = f'mandays per {_TRADE_UNITS[kind]}'
    else:
        text, unit = _GROUP_LABELS[group]
        text = text.format(k=_KEY_WORDS.get(key, key))
    return f'{text} ({unit})'


def default_materials_table():
    return {
        'columns': ['Group', 'Key', 'Label', 'Value', 'Default'],
        'data': [[group, key, _label(group, key), value, value]
                 for group, keys in _ROWS.items() for key, value in keys.items()],
    }


def _txt(value):
    return str(value).strip()


def _cell_num(value):
    """A number from a table cell: Qty cannot read a plain numeric string such as '0.024' or '1,234.5'."""
    text = _txt(value).replace(',', '')
    try:
        return float(text)
    except ValueError:
        return Qty(text, 'unit').val


def _is_metric(length):
    return Qty(length).uom in ('m', 'cm', 'mm', 'km')


def _ratio(value, label, parts=2):
    try:
        nums = [float(x) for x in _txt(value).split(':')]
    except ValueError:
        nums = []
    if len(nums) != parts or min(nums, default=0) <= 0:
        example = '1:4' if parts == 2 else '1:1.5:3'
        raise ValueError(f'{label} must be {parts} positive numbers separated by ":", e.g. {example}.')
    return nums


def _positive(value, label):
    if value <= 0:
        raise ValueError(f'{label} must be greater than zero.')
    return value


def _read_table(materials_table):
    qt = QTable(materials_table, name='materials_table', schema={
        'Group': {'cast': lambda x: _txt(x).lower()},
        'Key': {'cast': lambda x: _txt(x).lower()},
        'Label': {'type': str, 'required': False},
        'Default': {'type': str, 'required': False},
        'Value': {'cast': _cell_num},
    })
    qt.assert_columns(['Group', 'Key', 'Value'], optional_cols=['Label', 'Default'])
    qt.assert_unique_pairs('Group', 'Key')
    qt.assert_in('Group', list(_ROWS))
    values = qt.to_map(['Group', 'Key'], 'Value')
    missing = [f'{g}/{k}' for g, keys in _ROWS.items() for k in keys if (g, k) not in values]
    if missing:
        raise ValueError(f'materials_table is missing: {", ".join(missing[:8])}.')
    share = qt.sum_by('Group', 'Value')['member_share']
    if abs(share - 1) > 0.001:
        raise ValueError(f'materials_table: member_share values must add up to 1, they add up to {share:g}.')
    for group in _BANDS:
        low, typ, high = (values[(group, k)] for k in ('low', 'typical', 'high'))
        if not 0 < low <= typ <= high:
            raise ValueError(f'materials_table: {group} must satisfy 0 < low <= typical <= high.')
    if min(values.values()) < 0:
        raise ValueError('materials_table: values cannot be negative.')
    if any(values[('labour_rmc_scale', k)] > 1 for k in ('skilled', 'unskilled')):
        raise ValueError('materials_table: labour_rmc_scale values must be between 0 and 1.')
    return values


def _edited(values):
    return [f'{g}/{k}: {_ROWS[g][k]:g} -> {x:g}' for (g, k), x in values.items()
            if g in _ROWS and k in _ROWS[g] and abs(x - _ROWS[g][k]) > 1e-12]


def _out_of_range(values):
    """Edited values outside 0.5x to 2x of the built-in default; a likely typo such as 0.45 -> 45."""
    return [f'{g}/{k}: {_ROWS[g][k]:g} -> {x:g}' for (g, k), x in values.items()
            if g in _ROWS and k in _ROWS[g] and _ROWS[g][k] > 0 and not 0.5 <= x / _ROWS[g][k] <= 2]


def estimate_materials(*, plot_length, plot_width, coverage, floors, soil, materials_table, method,
                       structure_density, concrete_supply, mix, mix_ratio, seismic, include_base_works,
                       finishes, rooms, stairs, storey_height, brick_length, brick_width, brick_height,
                       ext_wall_thickness, int_wall_thickness, joint_thickness, masonry_mortar,
                       plaster_mortar, mortar_dry_factor, concrete_dry_factor, cement_bag_volume,
                       brick_wastage, include_labour, labour_productivity, include_cost=False):
    """Return the result items (scalars and tables) of the building_cost_detailed calculator."""
    v = _read_table(materials_table)
    metric = _is_metric(plot_length)
    rmc = concrete_supply == 'ready_mix'
    both, detailed_on, quick_on = method == 'both', method != 'quick', method != 'detailed'
    if structure_density not in PRESETS:
        raise ValueError(f'structure_density must be one of {", ".join(PRESETS)}.')
    floors, rooms = int(floors), int(rooms)
    if floors < 1:
        raise ValueError('Number of floors must be at least 1.')
    if rooms < 1:
        raise ValueError('Number of rooms per floor must be at least 1.')

    length, width = Qty(plot_length, 'm').val, Qty(plot_width, 'm').val
    footprint = length * width * Qty(coverage, 'unit').val  # m2, the model works in SI units
    bua = footprint * floors
    bua_sft = Qty(bua, 'm^2', 'ft^2').val  # the table coefficients are per sft
    brick_waste = Qty(brick_wastage, 'unit').val
    if not 0 <= brick_waste <= 0.25:
        raise ValueError('Brick wastage must be between 0 and 25 pct.')
    productivity = Qty(labour_productivity, 'unit').val
    if not 0 < productivity <= 2:
        raise ValueError('Labour productivity must be greater than 0 and at most 200 pct.')
    waste = {k: v[('wastage', k)] for k in ('cement', 'sand', 'aggregate', 'tiles', 'paint', 'ready_mix')}
    waste['bricks'] = brick_waste
    lap = v[('steel_lap_wastage', 'all')]

    # Quick rule: coefficient per sft x BUA in sft, then to SI units when the coefficient is not metric
    def band(group, unit=None, si_unit=None):
        values = [v[(group, b)] * bua_sft for b in ('low', 'typical', 'high')]
        return [Qty(x, unit, si_unit).val for x in values] if unit else values

    quick = {'Cement': band('quick_cement_bag_sft'), 'Steel': band('quick_steel_kg_sft'),
             'Concrete': band('quick_concrete_m3_sft'), 'Sand': band('quick_sand_cft_sft', 'cft', 'm^3'),
             'Aggregate': band('quick_aggregate_cft_sft', 'cft', 'm^3'), 'Bricks': band('quick_bricks_sft')}
    if rmc:  # the concrete share of cement, sand and aggregate is bought as ready-mix
        for name in ('Cement', 'Sand', 'Aggregate'):
            quick[name] = [x * (1 - v[('quick_rmc_removed', name.lower())]) for x in quick[name]]
    area = {k: Qty(v[('quick_area_sft_sft', k)] * bua_sft, 'ft^2', 'm^2').val
            for k in ('formwork', 'plaster', 'paint', 'tiles')}
    quick.update({'Formwork': [area['formwork']] * 3, 'Plaster area': [area['plaster']] * 3,
                  'Paint area': [area['paint']] * 3, 'Floor tile area': [area['tiles']] * 3})

    detail = {}
    if detailed_on:
        g = SimpleNamespace(
            length=length, width=width, footprint=footprint, bua=bua, bua_sft=bua_sft, floors=floors, rooms=rooms,
            soil=soil, density=structure_density, seismic=seismic, rmc=rmc, base_works=include_base_works,
            finishes=finishes,
            storey=_positive(Qty(storey_height, 'm').val, 'Storey height'),
            brick=[_positive(Qty(x, 'm').val, 'Brick size') for x in (brick_length, brick_width, brick_height)],
            joint=_positive(Qty(joint_thickness, 'm').val, 'Joint thickness'),
            ext_t=_txt(ext_wall_thickness).lower(), int_t=_txt(int_wall_thickness).lower(),
            stairs=_txt(stairs).lower(), mix=mix, mix_ratio=mix_ratio,
            masonry_ratio=_ratio(masonry_mortar, 'masonry_mortar'), plaster_ratio=_ratio(plaster_mortar, 'plaster_mortar'),
            mortar_dry=_positive(float(mortar_dry_factor), 'Mortar dry-volume factor'),
            concrete_dry=_positive(float(concrete_dry_factor), 'Concrete dry-volume factor'),
            bag_m3=_positive(Qty(cement_bag_volume, 'm^3/bag').val, 'Cement bag volume'),
            floor_key='1_2' if floors <= 2 else '3_4' if floors <= 4 else '5_6' if floors <= 6 else '7_plus',
            productivity=productivity,
        )
        if g.ext_t != 'auto':
            g.ext_t = _positive(Qty(ext_wall_thickness, 'm').val, 'External wall thickness')
        if g.int_t != 'auto':
            g.int_t = _positive(Qty(int_wall_thickness, 'm').val, 'Internal wall thickness')
        detail = _detailed(v, g)

    # Result values in display units: SI for metric input, otherwise ft2 and cft
    def cell(kind, x):
        if kind == 'vol':
            return Qty(x, 'm^3') if metric else Qty(x, 'm^3').to('cft')
        if kind == 'area':
            return Qty(x, 'm^2') if metric else Qty(x, 'm^2').to('ft^2')
        if kind == 'nos':
            return Qty(round(x), 'nos')
        return Qty(x, {'m3': 'm^3'}.get(kind, kind))

    names = [n for n in _KINDS if finishes or n not in ('Plaster area', 'Paint area', 'Floor tile area')]
    label = {'Aggregate': 'Coarse aggregate', 'Concrete': 'Ready-mix concrete' if rmc else 'Concrete'}

    comp_cols = ['Material']
    if quick_on:
        comp_cols += ['Quick Low', 'Quick Typical', 'Quick High']
    if detailed_on:
        comp_cols += ['Detailed Low', 'Detailed Typical', 'Detailed High']
    if both:
        comp_cols += ['Difference', 'Note']
    comp, flagged = [], []
    for n in names:
        row = [label.get(n, n)]
        if quick_on:
            row += [cell(_KINDS[n], x) for x in quick[n]]
        if detailed_on:
            row += [cell(_KINDS[n], x) for x in detail['rows'][n]]
        if both:
            q, d = quick[n][1], detail['rows'][n][1]
            diff = (d - q) / q * 100 if q else 0
            note = ''
            if abs(diff) > FLAG_PCT:
                flagged.append(label.get(n, n))
                note = _NOTES.get((n, 1 if diff > 0 else -1), 'The methods differ; check the assumptions')
            row += [f'{diff:+.0f} %', note]
        comp.append(row)
    if detailed_on and include_base_works:
        for title, kind, x in (('PCC (lean concrete)', 'm3', detail['pcc']), ('Brick soling (flat)', 'nos', detail['soling'])):
            comp.append([title] + ['-'] * 3 * quick_on + [cell(kind, x)] * 3 + ['', ''] * both)

    # Order quantities of the headline method (Detailed unless only Quick is selected)
    src = {n: (detail['rows'][n] if detailed_on else quick[n])[1] for n in names}
    soling = detail['soling'] if detailed_on and include_base_works else 0
    orders = [('Cement', 'bag', src['Cement'], waste['cement']), ('Steel', 'kg', src['Steel'], lap),
              ('Sand', 'vol', src['Sand'], waste['sand']), ('Gravel', 'vol', src['Aggregate'], waste['aggregate']),
              ('Brick', 'nos', src['Bricks'], waste['bricks'])]
    if soling:
        orders.append(('Brick soling', 'nos', soling, waste['bricks']))
    if rmc:
        orders.append(('Ready-mix Concrete', 'vol', src['Concrete'], waste['ready_mix']))
    if finishes:
        litres = Qty(src['Paint area'], 'm^2', 'ft^2').val * v[('finish', 'paint_coats')] / v[('finish', 'paint_sft_per_l')]
        orders += [('Floor Tiles', 'area', src['Floor tile area'], waste['tiles']), ('Paint', 'L', litres, waste['paint'])]
    ordered = {n: x * (1 + w) for n, _, x, w in orders}

    result = {
        'Footprint Area': cell('area', footprint), 'Total Built-up Area': cell('area', bua),
        'Concrete': cell('m3', src['Concrete']), 'Steel': cell('kg', ordered['Steel']),
        'Cement': cell('bag', ordered['Cement']), 'Sand': cell('vol', ordered['Sand']),
        'Gravel': cell('vol', ordered['Gravel']),
        'Brick': cell('nos', ordered['Brick'] + ordered.get('Brick soling', 0)),
    }
    if rmc:
        result['Ready-mix Concrete'] = cell('vol', ordered['Ready-mix Concrete'])
    if include_labour and detailed_on:
        trades = detail['labour'][structure_density]
        result['Skilled Labour'] = Qty(sum(t[1] for t in trades.values()), 'manday')
        result['Unskilled Labour'] = Qty(sum(t[2] for t in trades.values()), 'manday')
    result['Method Comparison'] = {'data': comp, 'columns': comp_cols}
    result['Order Quantities'] = {
        'data': [[n, cell(k, x), f'{w * 100:g} %', cell(k, x * (1 + w))] for n, k, x, w in orders],
        'columns': ['Material', 'Net Qty', 'Wastage', 'Order Qty']}
    if detailed_on:
        result['Concrete by Member'] = {'data': detail['members'], 'columns': ['Member', 'Volume', 'Steel (net)', 'Formwork']}
        result['Cement Sources'] = {'data': detail['cement_sources'], 'columns': ['Source', 'Bags']}

    # Intensity per unit of built-up area
    per, unit = (bua, 'm^2') if metric else (bua_sft, 'ft^2')
    vol_unit = 'm^3' if metric else 'cft'
    intensity = []
    for title, key, qk in (('Cement', 'Cement', 'bag'), ('Steel (net)', 'Steel', 'kg'), ('Concrete', 'Concrete', 'm^3'),
                           ('Sand', 'Sand', vol_unit), ('Coarse aggregate', 'Aggregate', vol_unit), ('Bricks', 'Bricks', 'nos')):
        row = [title]
        for on, data in ((quick_on, quick), (detailed_on, detail.get('rows'))):
            if on:
                x = Qty(data[key][1], 'm^3', 'cft').val if qk == 'cft' else data[key][1]
                row.append(Qty(x / per, f'{qk}/{unit}'))
        intensity.append(row)
    result['Intensity per Area'] = {
        'data': intensity, 'columns': ['Material'] + ['Quick'] * quick_on + ['Detailed'] * detailed_on}

    if include_labour and detailed_on:
        result['Labour by Trade'] = {'data': _labour_rows(detail, structure_density, cell),
                                     'columns': ['Trade', 'Quantity', 'Skilled', 'Unskilled']}

    notes = ['Preliminary estimate; foundation type, structural design and local practice can change quantities by 20 pct or more.']
    if include_cost:
        items = {n: cell(k, ordered[n]) for n, k, _, _ in orders if n != 'Brick soling'}
        items['Brick'] = result['Brick']  # includes the soling bricks
        items.update({n: result[n] for n in ('Skilled Labour', 'Unskilled Labour') if n in result})
        cost = QCost()
        cost.add_all(items)
        result.update(cost.results(per=result['Total Built-up Area'], per_label='Area'))
    if detailed_on and structure_density == 'light' and (floors > 2 or seismic == 'high' or soil == 'poor'):
        notes.append('Light density is intended for 1-2 floor single-family houses with short spans, normal seismic zone '
                     'and normal or good soil. Consider typical density and consult an engineer.')
    if both and flagged:
        notes.append(f'The two methods differ by more than {FLAG_PCT} pct on: {", ".join(flagged)}.')
    if include_labour and not detailed_on:
        notes.append('Labour is estimated by the Detailed method only; choose Detailed or Both methods to see it.')
    if include_labour and detailed_on:
        notes.append('Detailed labour counts the modelled trades only; earthwork, electrical, plumbing, doors and windows, '
                     'supervision and contractor overhead are not included. Tick Include cost to price the mandays.')
    edited = _edited(v)
    if edited:
        notes.append('Edited assumptions in materials_table: ' + '; '.join(edited[:8]) + (' ...' if len(edited) > 8 else ''))
    far = _out_of_range(v)
    if far:
        notes.append('Check these coefficients: they are less than half or more than twice the Default in the '
                     'Coefficients table: ' + '; '.join(far[:8]) + (' ...' if len(far) > 8 else ''))
    result['Notes'] = qwarn('\n'.join(f'- {x}' for x in notes))
    return result


def _labour_rows(detail, density, cell):
    """Rows of the Labour by Trade table: each trade, the total, and the totals of the neighbouring presets."""
    def qty(kind, x):
        return Qty(x, 'm^3') if kind == 'm3' else Qty(x, 'tonne') if kind == 'tonne' else cell('area', x)

    trades = detail['labour'][density]
    rows = [[_TRADES[t][0], qty(_TRADES[t][1], q), Qty(sk, 'manday'), Qty(un, 'manday')]
            for t, (q, sk, un) in trades.items()]
    rows.append(['Total', '', Qty(sum(t[1] for t in trades.values()), 'manday'),
                 Qty(sum(t[2] for t in trades.values()), 'manday')])
    for preset in dict.fromkeys(detail['presets']):
        if preset != density:
            other = detail['labour'][preset].values()
            rows.append([f'Total with {preset} density', '', Qty(sum(t[1] for t in other), 'manday'),
                         Qty(sum(t[2] for t in other), 'manday')])
    return rows


def _detailed(v, g):
    """Detailed method: derived quantities for the selected density and its two neighbours (all lengths in m)."""
    perimeter = 2 * (g.length + g.width)
    wall_h = g.storey - Qty(v[('geometry', 'beam_slab_depth_ft')], 'ft', 'm').val
    if wall_h <= 0:
        raise ValueError('Storey height must be greater than the beam and slab depth.')
    opening = v[('geometry', 'opening_share')]
    if not 0 <= opening < 1:
        raise ValueError('opening_share must be between 0 and 1.')
    internal_len = max(0, 2 * sqrt(g.rooms * g.footprint) - perimeter / 2)  # rectangular room grid
    ext_gross, int_gross = perimeter * wall_h * g.floors, internal_len * wall_h * g.floors
    ext_net, int_net = ext_gross * (1 - opening), int_gross * (1 - opening)

    # Masonry
    bl, bw, bh = g.brick
    per_m3 = 1 / ((bl + g.joint) * (bw + g.joint) * (bh + g.joint))
    mortar_wet = 1 - per_m3 * bl * bw * bh
    ext_t = bw if g.ext_t == 'auto' else g.ext_t
    int_t = bw if g.int_t == 'auto' else g.int_t
    masonry_m3 = ext_net * ext_t + int_net * int_t
    bricks = masonry_m3 * per_m3
    soling = g.footprint / ((bl + g.joint) * (bw + g.joint))

    def mortar(volume, ratio):  # dry mortar volume -> (bags, sand m3)
        cement, sand = ratio
        return volume * cement / (cement + sand) / g.bag_m3, volume * sand / (cement + sand)

    cem_masonry, sand_masonry = mortar(masonry_m3 * mortar_wet * g.mortar_dry, g.masonry_ratio)
    cem_plaster = sand_plaster = cem_screed = sand_screed = plaster_area = tile_area = 0
    if g.finishes:
        plaster_area = 2 * (ext_net + int_net) + g.bua
        tile_area = v[('finish', 'tiled_share')] * g.bua
        cem_plaster, sand_plaster = mortar(
            plaster_area * Qty(v[('finish', 'plaster_in')], 'inch', 'm').val * g.mortar_dry, g.plaster_ratio)
        cem_screed, sand_screed = mortar(
            tile_area * Qty(v[('finish', 'screed_in')], 'inch', 'm').val * g.mortar_dry, g.plaster_ratio)

    # Stairs: steps, waist slab and a mid-landing for each storey served
    st = {k: v[('stair', k)] for k in ('width_m', 'riser_m', 'tread_m', 'waist_m', 'landing_count')}
    n_riser = max(2, ceil(round(g.storey / st['riser_m'], 6)))
    run = (n_riser - 2) * st['tread_m']
    per_storey = (st['width_m'] * n_riser * 0.5 * st['tread_m'] * g.storey / n_riser
                  + st['width_m'] * hypot(run, g.storey) * st['waist_m']
                  + st['landing_count'] * st['width_m'] * 2 * st['width_m'] * st['waist_m'])
    n_stairs = (1 if g.floors > 1 else 0) if g.stairs == 'auto' else int(float(g.stairs))
    if n_stairs < 0:
        raise ValueError('Number of staircases cannot be negative.')
    conc_stair = n_stairs * g.floors * per_storey

    # Lintels over the openings
    li = {k: v[('lintel', k)] for k in ('opening_height_m', 'bearing_allowance', 'depth_m')}

    def lintel_length(gross):
        return opening * gross / li['opening_height_m'] * li['bearing_allowance']

    conc_lintel = (lintel_length(ext_gross) * ext_t + lintel_length(int_gross) * int_t) * li['depth_m']

    # Concrete mix
    if g.mix == 'custom':
        ratio = _ratio(g.mix_ratio, 'mix_ratio', 3)
    else:
        ratio = [v[(f'mix_{g.mix}', k)] for k in ('cement', 'sand', 'aggregate')]
    pcc_ratio = [v[('mix_m10', k)] for k in ('cement', 'sand', 'aggregate')]

    def concrete(volume, parts):  # concrete volume -> (bags, sand m3, aggregate m3)
        dry = volume * g.concrete_dry / sum(parts)
        return dry * parts[0] / g.bag_m3, dry * parts[1], dry * parts[2]

    order = PRESETS.index(g.density)
    low, high = PRESETS[max(order - 1, 0)], PRESETS[min(order + 1, len(PRESETS) - 1)]
    runs = {}
    for p in {low, g.density, high}:
        frame = v[('density', p)] * g.bua_sft * v[('floor_scale', g.floor_key)]
        vol = {m: frame * v[('member_share', m)] for m in FRAME}
        vol['footing'] *= v[('soil_scale', g.soil)]
        vol['stair'], vol['lintel'] = conc_stair, conc_lintel
        steel = {m: vol[m] * v[('steel_kg_m3', m)] * v[('seismic_steel', g.seismic)] *
                 (v[('steel_scale', p)] if m in FRAME else 1) for m in vol}
        form = {m: vol[m] * v[('formwork_m2_m3', m)] for m in vol}
        total = sum(vol.values())
        cem_c = sand_c = agg_c = pcc = cem_p = sand_p = agg_p = 0
        if not g.rmc:
            cem_c, sand_c, agg_c = concrete(total, ratio)
        if g.base_works:
            pcc = (vol['footing'] / v[('pcc', 'footing_depth_m')] * v[('pcc', 'footing_projection')]
                   + g.footprint) * Qty(v[('pcc', 'thickness_mm')], 'mm', 'm').val
            cem_p, sand_p, agg_p = concrete(pcc, pcc_ratio)
        sources = [['Concrete', cem_c], ['Masonry', cem_masonry], ['Plaster', cem_plaster],
                   ['Screed', cem_screed], ['PCC', cem_p]]
        # labour: quantity of each trade x mandays per unit, divided by the productivity factor
        quantity = {'brickwork_m3': masonry_m3, 'plaster_m2': plaster_area, 'screed_tile_m2': tile_area,
                    'concrete_m3': total, 'pcc_m3': pcc, 'formwork_m2': sum(form.values()),
                    'steel_tonne': Qty(sum(steel.values()), 'kg', 'tonne').val, 'paint_m2': plaster_area,
                    'soling_m2': g.footprint if g.base_works else 0}
        scale = {t: {'skilled': 1.0, 'unskilled': 1.0} for t in quantity}
        if g.rmc:
            scale['concrete_m3'] = {k: v[('labour_rmc_scale', k)] for k in ('skilled', 'unskilled')}
        labour = {t: (q, q * v[('labour_skilled', t)] * scale[t]['skilled'] / g.productivity,
                      q * v[('labour_unskilled', t)] * scale[t]['unskilled'] / g.productivity)
                  for t, q in quantity.items() if q > 0}
        runs[p] = {'vol': vol, 'steel': steel, 'form': form, 'total': total, 'pcc': pcc, 'sources': sources,
                   'labour': labour, 'Cement': sum(x[1] for x in sources),
                   'Sand': sand_c + sand_masonry + sand_plaster + sand_screed + sand_p, 'Aggregate': agg_c + agg_p}

    def values(p):
        r = runs[p]
        return {'Cement': r['Cement'], 'Steel': sum(r['steel'].values()), 'Concrete': r['total'],
                'Sand': r['Sand'], 'Aggregate': r['Aggregate'], 'Bricks': bricks,
                'Formwork': sum(r['form'].values()), 'Plaster area': plaster_area,
                'Paint area': plaster_area, 'Floor tile area': tile_area}

    triple = [values(low), values(g.density), values(high)]
    r = runs[g.density]
    titles = {'footing': 'Footing', 'column': 'Column', 'beam': 'Beam', 'slab': 'Slab', 'stair': 'Stairs', 'lintel': 'Lintels'}
    members = [[titles[m], Qty(r['vol'][m], 'm^3'), Qty(r['steel'][m], 'kg'), Qty(r['form'][m], 'm^2')] for m in r['vol']]
    members.append(['Total', Qty(r['total'], 'm^3'), Qty(sum(r['steel'].values()), 'kg'), Qty(sum(r['form'].values()), 'm^2')])
    return {
        'rows': {n: [t[n] for t in triple] for n in triple[1]},
        'members': members,
        'cement_sources': [[name, Qty(x, 'bag')] for name, x in r['sources']] + [['Total', Qty(r['Cement'], 'bag')]],
        'pcc': r['pcc'], 'soling': soling,
        'labour': {p: runs[p]['labour'] for p in runs}, 'presets': (low, g.density, high),
    }
