# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

import copy

import qsett

qsett.init()

from calculators.all.analytics.optimization.cal_optima import (
    optima_assignment,
    optima_assignment__info,
    optima_capacity,
    optima_capacity__info,
    optima_knapsack,
    optima_knapsack__info,
    optima_placement,
    optima_placement__info,
    optima_redundancy,
    optima_redundancy__info,
    optima_routing,
    optima_routing__info,
    optima_supplier_selection,
    optima_supplier_selection__info,
    optima_transport,
    optima_transport__info,
)


def _inputs_from_info(info_fn):
    schema = info_fn()['schema']
    payload = {}
    for field, spec in schema.items():
        payload[field] = copy.deepcopy(spec.get('initial'))
    return payload


def _assert_common_output_shape(result):
    assert isinstance(result, dict)
    assert 'Summary' in result
    assert 'Decision Table' in result
    assert len(result['Summary']) == 1
    assert 'Status' in result['Summary'].columns


def test_optima_transport_smoke_with_schema_defaults():
    payload = _inputs_from_info(optima_transport__info)
    result = optima_transport(**payload)

    _assert_common_output_shape(result)
    assert result['Summary'].iloc[0]['Model'] == 'Transportation'



def test_optima_assignment_smoke_with_schema_defaults():
    payload = _inputs_from_info(optima_assignment__info)
    result = optima_assignment(**payload)

    _assert_common_output_shape(result)
    assert result['Summary'].iloc[0]['Model'] == 'Assignment'



def test_optima_knapsack_smoke_with_schema_defaults():
    payload = _inputs_from_info(optima_knapsack__info)
    result = optima_knapsack(**payload)

    _assert_common_output_shape(result)
    assert result['Summary'].iloc[0]['Model'] == 'Knapsack'



def test_optima_supplier_selection_smoke_with_schema_defaults():
    payload = _inputs_from_info(optima_supplier_selection__info)
    result = optima_supplier_selection(**payload)

    _assert_common_output_shape(result)
    assert result['Summary'].iloc[0]['Model'] == 'Supplier Selection'


def test_optima_capacity_smoke_with_schema_defaults():
    payload = _inputs_from_info(optima_capacity__info)
    result = optima_capacity(**payload)

    _assert_common_output_shape(result)
    assert result['Summary'].iloc[0]['Model'] == 'Capacity'


def test_optima_routing_smoke_with_schema_defaults():
    payload = _inputs_from_info(optima_routing__info)
    result = optima_routing(**payload)

    _assert_common_output_shape(result)
    assert result['Summary'].iloc[0]['Model'] == 'Routing'


def test_optima_placement_smoke_with_schema_defaults():
    payload = _inputs_from_info(optima_placement__info)
    result = optima_placement(**payload)

    _assert_common_output_shape(result)
    assert result['Summary'].iloc[0]['Model'] == 'Placement'


def test_optima_redundancy_smoke_with_schema_defaults():
    payload = _inputs_from_info(optima_redundancy__info)
    result = optima_redundancy(**payload)

    _assert_common_output_shape(result)
    assert result['Summary'].iloc[0]['Model'] == 'Redundancy'



def test_schema_initial_table_defaults_are_not_shared_between_calls():
    info_1 = optima_transport__info()
    info_2 = optima_transport__info()

    info_1['schema']['supply']['initial'].loc[0, 'Capacity'] = 999
    assert info_2['schema']['supply']['initial'].loc[0, 'Capacity'] == 100
