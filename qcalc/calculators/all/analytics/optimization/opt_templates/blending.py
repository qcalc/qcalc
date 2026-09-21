# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

import re

import pandas as pd
import pulp

from ..opt_core import require_columns, safe_objective_value, solver, slack_table


def _is_blank(value):
    if value is None:
        return True
    text = str(value).strip().lower()
    return text in {'', 'none', 'null', 'nan', 'na'}


def _to_float(value, field_name):
    if _is_blank(value):
        raise Exception(f"{field_name} cannot be blank")
    if isinstance(value, (int, float)):
        return float(value)

    text = str(value).strip()
    text = text.replace(',', '')
    text = re.sub(r'(?i)\s*(usd|inr|eur|gbp)\b', '', text)
    text = text.replace('%', '')
    match = re.search(r'[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?', text)
    if not match:
        raise Exception(f"Invalid numeric value for {field_name}: {value}")
    return float(match.group(0))


def _to_optional_float(value, field_name):
    if _is_blank(value):
        return None
    return _to_float(value, field_name)


def _to_fraction(value, field_name):
    raw = _to_float(value, field_name)
    return raw / 100.0


def _to_optional_fraction(value, field_name):
    if _is_blank(value):
        return None
    return _to_fraction(value, field_name)


def _normalize_name(name):
    text = str(name).strip().lower()
    text = text.replace('%', '')
    text = text.replace('_', ' ')
    return ' '.join(text.split())


def solve_blending(
    blend_materials,
    blend_specs,
    batch_size,
    blend_qty_type,
    show_zero,
):
    require_columns(blend_materials, 'blend_materials', ['Material', 'Unit Cost'])
    require_columns(blend_specs, 'blend_specs', ['Property', 'Min %', 'Max %'])

    if blend_materials.empty:
        raise Exception('blend_materials must contain at least one material row')

    batch_size_val = _to_float(batch_size, 'batch_size')
    if batch_size_val <= 0:
        raise Exception('batch_size must be greater than zero')

    materials_df = blend_materials.copy()
    specs_df = blend_specs.copy()

    material_names = []
    unit_cost = {}
    min_qty = {}
    max_qty = {}

    for idx, row in materials_df.iterrows():
        material = str(row['Material']).strip() if not _is_blank(row['Material']) else f'Material {len(material_names) + 1}'
        if material in material_names:
            raise Exception(f"Duplicate material name found: {material}")

        cost = _to_float(row['Unit Cost'], f'blend_materials.Unit Cost (row {idx + 1})')
        if cost < 0:
            raise Exception(f'Unit Cost must be non-negative for material: {material}')

        lo = 0.0
        if 'Min Qty' in materials_df.columns:
            min_val = _to_optional_float(row.get('Min Qty'), f'blend_materials.Min Qty (row {idx + 1})')
            if min_val is not None:
                lo = float(min_val)

        hi = None
        if 'Max Qty' in materials_df.columns:
            max_val = _to_optional_float(row.get('Max Qty'), f'blend_materials.Max Qty (row {idx + 1})')
            if max_val is not None:
                hi = float(max_val)

        if lo < 0:
            raise Exception(f'Min Qty must be non-negative for material: {material}')
        if hi is not None and hi < 0:
            raise Exception(f'Max Qty must be non-negative for material: {material}')
        if hi is not None and lo > hi:
            raise Exception(f'Min Qty cannot exceed Max Qty for material: {material}')

        material_names.append(material)
        unit_cost[material] = float(cost)
        min_qty[material] = float(lo)
        max_qty[material] = float(hi) if hi is not None else None

    property_col_map = {}
    reserved = {'material', 'unit cost', 'min qty', 'max qty'}
    for col in materials_df.columns:
        key = _normalize_name(col)
        if key in reserved:
            continue
        if key:
            property_col_map[key] = col

    if not property_col_map:
        raise Exception('blend_materials must include at least one property column besides Material/Unit Cost/Min Qty/Max Qty')

    spec_rows = []
    for idx, row in specs_df.iterrows():
        prop_raw = row.get('Property')
        if _is_blank(prop_raw):
            continue
        prop_name = str(prop_raw).strip()
        prop_key = _normalize_name(prop_name)
        min_frac = _to_optional_fraction(row.get('Min %'), f'blend_specs.Min % (row {idx + 1})')
        max_frac = _to_optional_fraction(row.get('Max %'), f'blend_specs.Max % (row {idx + 1})')

        if min_frac is None and max_frac is None:
            continue
        if min_frac is not None and (min_frac < 0 or min_frac > 1):
            raise Exception(f'Invalid Min % for property: {prop_name}')
        if max_frac is not None and (max_frac < 0 or max_frac > 1):
            raise Exception(f'Invalid Max % for property: {prop_name}')
        if min_frac is not None and max_frac is not None and min_frac > max_frac:
            raise Exception(f'Min % cannot exceed Max % for property: {prop_name}')
        if prop_key not in property_col_map:
            raise Exception(
                f"Property '{prop_name}' not found in blend_materials columns. "
                'Ensure a matching property column exists in blend_materials.'
            )

        spec_rows.append({
            'name': prop_name,
            'key': prop_key,
            'min_frac': min_frac,
            'max_frac': max_frac,
        })

    if not spec_rows:
        raise Exception('blend_specs must include at least one active property bound')

    comp = {}
    for material in material_names:
        row = materials_df.loc[materials_df['Material'].astype(str).str.strip() == material].iloc[0]
        comp[material] = {}
        for spec in spec_rows:
            col = property_col_map[spec['key']]
            frac = _to_fraction(row[col], f"blend_materials.{col} ({material})")
            if frac < 0 or frac > 1:
                raise Exception(f'Composition must be between 0% and 100% for material {material}, property {spec["name"]}')
            comp[material][spec['key']] = float(frac)

    min_total = sum(min_qty[m] for m in material_names)
    max_total = sum(max_qty[m] if max_qty[m] is not None else batch_size_val for m in material_names)
    if min_total > batch_size_val + 1e-9:
        raise Exception('Sum of material Min Qty values exceeds batch_size')
    if max_total + 1e-9 < batch_size_val:
        raise Exception('Sum of material Max Qty values is less than batch_size')

    qty_cat = pulp.LpInteger if str(blend_qty_type).lower() == 'integer' else pulp.LpContinuous

    prob = pulp.LpProblem('optima_blending', pulp.LpMinimize)
    x = {}
    for material in material_names:
        x[material] = pulp.LpVariable(
            f'Qty_{material}',
            lowBound=min_qty[material],
            upBound=max_qty[material],
            cat=qty_cat,
        )

    prob += pulp.lpSum(unit_cost[material] * x[material] for material in material_names)
    prob += pulp.lpSum(x[material] for material in material_names) == batch_size_val, 'batch_balance'

    for spec in spec_rows:
        if spec['min_frac'] is not None:
            prob += (
                pulp.lpSum(comp[material][spec['key']] * x[material] for material in material_names)
                >= float(spec['min_frac']) * batch_size_val,
                f"prop_min_{spec['key'].replace(' ', '_')}",
            )
        if spec['max_frac'] is not None:
            prob += (
                pulp.lpSum(comp[material][spec['key']] * x[material] for material in material_names)
                <= float(spec['max_frac']) * batch_size_val,
                f"prop_max_{spec['key'].replace(' ', '_')}",
            )

    prob.solve(solver())
    status = pulp.LpStatus[prob.status]

    qty_values = {material: float(x[material].value() or 0.0) for material in material_names}
    total_cost = float(sum(unit_cost[m] * qty_values[m] for m in material_names))
    cost_per_unit = (total_cost / batch_size_val) if batch_size_val else None

    tol = 1e-7
    mix_rows = []
    active_count = 0
    for material in material_names:
        qty = qty_values[material]
        if qty > tol:
            active_count += 1
        if show_zero or qty > tol:
            lo = min_qty[material]
            hi = max_qty[material]
            at_min = abs(qty - lo) <= tol
            at_max = (hi is not None) and (abs(qty - hi) <= tol)
            if at_min and at_max:
                bound_status = 'Min/Max Bound'
            elif at_min:
                bound_status = 'Min Bound'
            elif at_max:
                bound_status = 'Max Bound'
            else:
                bound_status = 'Free'
            mix_rows.append({
                'Material': material,
                'Quantity': round(qty, 6),
                'Batch %': round((qty / batch_size_val) * 100 if batch_size_val else 0.0, 4),
                'Unit Cost': round(unit_cost[material], 6),
                'Line Cost': round(unit_cost[material] * qty, 6),
                'Min Qty': round(lo, 6),
                'Max Qty': None if hi is None else round(hi, 6),
                'Remaining to Max': None if hi is None else round(max(0.0, hi - qty), 6),
                'Bound Status': bound_status,
            })

    compliance_rows = []
    for spec in spec_rows:
        prop_num = sum(comp[material][spec['key']] * qty_values[material] for material in material_names)
        actual_frac = (prop_num / batch_size_val) if batch_size_val else 0.0
        min_frac = spec['min_frac']
        max_frac = spec['max_frac']
        min_slack = None if min_frac is None else actual_frac - min_frac
        max_slack = None if max_frac is None else max_frac - actual_frac
        min_ok = True if min_frac is None else (actual_frac >= min_frac - tol)
        max_ok = True if max_frac is None else (actual_frac <= max_frac + tol)
        binding = False
        if min_frac is not None and abs(actual_frac - min_frac) <= tol:
            binding = True
        if max_frac is not None and abs(actual_frac - max_frac) <= tol:
            binding = True
        compliance_rows.append({
            'Property': spec['name'],
            'Required Min %': None if min_frac is None else round(min_frac * 100, 6),
            'Required Max %': None if max_frac is None else round(max_frac * 100, 6),
            'Actual %': round(actual_frac * 100, 6),
            'Min Slack %': None if min_slack is None else round(min_slack * 100, 6),
            'Max Slack %': None if max_slack is None else round(max_slack * 100, 6),
            'Binding': bool(binding),
            'Status': 'OK' if (min_ok and max_ok) else 'Violation',
        })

    return {
        'Summary': pd.DataFrame([{
            'Model': 'Raw Material Mix (Blending)',
            'Status': status,
            'Objective': safe_objective_value(prob),
            'Batch Size': round(batch_size_val, 6),
            'Total Cost': round(total_cost, 6),
            'Cost per Unit': None if cost_per_unit is None else round(cost_per_unit, 6),
            'Material Count': len(material_names),
            'Active Materials': int(active_count),
        }]),
        'Optimal Mix': pd.DataFrame(mix_rows),
        'Property Compliance': pd.DataFrame(compliance_rows),
        'Constraint Slack': slack_table(prob),
    }