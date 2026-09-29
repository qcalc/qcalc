# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

import copy

import qsett

qsett.init()

from calculators.all.business.planning import optima_sop, optima_sop__info


def _payload_from_info():
    schema = optima_sop__info()['schema']
    payload = {}
    for field, spec in schema.items():
        if isinstance(spec, dict) and 'initial' in spec:
            payload[field] = copy.deepcopy(spec.get('initial'))
    return payload


def test_optima_sop_trims_whitespace_in_required_product_columns():
    payload = _payload_from_info()

    product_table = payload['sop_product_master']
    cols = list(product_table.columns)
    opening_idx = cols.index('Opening Inventory')
    cols[opening_idx] = 'Opening Inventory    '
    product_table.columns = cols

    result = optima_sop(**payload)

    assert isinstance(result, dict)
    assert 'Summary' in result
    assert result['Summary'].iloc[0]['Status'] in {'Optimal', 'Feasible'}
