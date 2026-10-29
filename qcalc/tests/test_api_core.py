# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha
# Tests generated with AI assistance. Reviewed and validated by the author.

import json

import pytest
import qsett

qsett.init()

from calc.mod_api_core import (
    ApiError, api_enabled, decode_inputs, get_schema, list_calculators, run_calculator,
)


def _err(call, *args, **kwargs):
    with pytest.raises(ApiError) as info:
        call(*args, **kwargs)
    return info.value


def test_only_opted_in_calculators_are_enabled():
    assert api_enabled('bmi')
    assert api_enabled('production_mix_profit')
    assert not api_enabled('redo')  # standard calculator without 'api': True
    assert not api_enabled('no_such_calculator')
    assert not api_enabled('bmi__info')


def test_list_calculators_filters_by_query_and_pages():
    everything = list_calculators()
    ids = {item['id'] for item in everything['calculators']}
    assert {'bmi', 'production_mix_profit'} <= ids
    assert 'redo' not in ids

    only_bmi = list_calculators(query='body mass')
    assert [item['id'] for item in only_bmi['calculators']] == ['bmi']

    page = list_calculators(limit=1, offset=1)
    assert len(page['calculators']) == 1 and page['total'] == everything['total']


def test_schema_lists_arguments_with_defaults():
    schema = get_schema('bmi')
    assert schema['id'] == 'bmi'
    args = {a['name']: a for a in schema['arguments']}
    assert list(args) == ['weight', 'height']
    assert args['weight']['default'] == '132 lb'
    assert args['weight']['required'] is False
    json.dumps(schema, allow_nan=False)


def test_schema_marks_table_arguments():
    args = {a['name']: a for a in get_schema('production_mix_profit')['arguments']}
    assert args['products']['annotation'] == 'qtbl'
    assert args['products']['default']['__qcalc_type'] == 'table'


def test_run_with_defaults_returns_tagged_quantity():
    out = run_calculator('bmi')
    bmi = out['result']['BMI']
    assert bmi['__qcalc_type'] == 'qty'
    assert bmi['value'] == pytest.approx(21.3, abs=0.2)
    assert out['function'] == 'bmi' and out['mode'] == 'full'


def test_run_accepts_plain_tagged_and_numeric_inputs():
    tagged_height = {'__qcalc_type': 'qty', 'value': 1.75, 'unit': 'm', 'text': '1.75 m'}
    out = run_calculator('bmi', {'weight': '70 kg', 'height': tagged_height})
    assert out['result']['BMI']['value'] == pytest.approx(22.857, abs=0.01)

    out = run_calculator('bmi', {'weight': 70, 'height': '1.75 m'})  # bare number is read in the calculator's unit
    assert out['result']['BMI']['value'] == pytest.approx(22.857, abs=0.01)


def test_unknown_argument_is_rejected_not_ignored():
    err = _err(run_calculator, 'bmi', {'weigth': '70 kg'})
    assert (err.code, err.status, err.field) == ('unknown_argument', 422, 'weigth')


def test_unlisted_or_missing_calculator_is_404():
    assert _err(run_calculator, 'redo').status == 404
    assert _err(run_calculator, 'nope').status == 404
    assert _err(get_schema, 'redo').status == 404


def test_calculator_failure_becomes_calc_error():
    err = _err(run_calculator, 'bmi', {'weight': 'abc'})
    assert (err.code, err.status) == ('calc_error', 422)


def test_bad_mode_and_bad_inputs_object():
    assert _err(run_calculator, 'bmi', {}, 'tiny').code == 'bad_request'
    assert _err(run_calculator, 'bmi', ['x']).code == 'bad_request'


def test_compact_mode_truncates_tables_and_result_is_strict_json():
    out = run_calculator('production_mix_profit', mode='compact')
    assert out['result']['Optimization Status'] == 'Optimal'
    json.dumps(out, allow_nan=False)


def test_decode_inputs_required_and_coercion():
    def sample(a, n=1, x=1.5, flag=False, label='k'):
        return a

    assert _err(decode_inputs, sample, {}).code == 'missing_argument'
    assert decode_inputs(sample, {'a': 1, 'n': '3', 'x': '2.5', 'flag': 'true'}) == {
        'a': 1, 'n': 3, 'x': 2.5, 'flag': True}
    assert decode_inputs(sample, {'a': 1, 'x': '5 m'})['x'] == '5 m'  # 'value unit' text is left for the calculator
    assert decode_inputs(sample, {'a': 1, 'n': 2.0})['n'] == 2
    assert _err(decode_inputs, sample, {'a': 1, 'n': 2.5}).field == 'n'
    assert _err(decode_inputs, sample, {'a': 1, 'n': 'x'}).code == 'invalid_argument'


def test_decode_inputs_tables_and_lists():
    from qcore import qtbl, qtable, qlist

    def sample(t: qtbl = None, df: qtable = None, items: qlist = None):
        return t

    table = {'columns': ['A'], 'data': [[1]]}
    out = decode_inputs(sample, {'t': table, 'df': table, 'items': [1]})
    assert out['t'] == table
    assert list(out['df'].columns) == ['A']
    assert _err(decode_inputs, sample, {'t': [1]}).field == 't'
    assert _err(decode_inputs, sample, {'items': 'x'}).field == 'items'
