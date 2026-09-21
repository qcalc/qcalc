import datetime
import decimal

import pandas as pd
import pytest
import qsett

qsett.init()

from calc import views
from qcore import Qty
from qcore import mod_qencode as enc
from qutil import QDateTime


def test_qencoderbase_default_uses_shared_serialize_value(monkeypatch):
    marker = object()

    def _fake_serialize(_obj, profile='json', _seen=None):
        assert profile == 'json'
        return marker

    monkeypatch.setattr(enc, 'serialize_value', _fake_serialize)

    out = enc.QEncoderBase().default(object())
    assert out is marker


def test_serialize_value_step2_profile_delegates_to_step2_packer(monkeypatch):
    marker = {'ok': True}

    def _fake_pack(value, _seen=None):
        assert value == {'x': 1}
        return marker

    monkeypatch.setattr(enc, 'step2_pack_value', _fake_pack)

    out = enc.serialize_value({'x': 1}, profile='step2')
    assert out is marker


def test_step2_pack_value_handles_qty_datetime_and_dataframe():
    packed_qty = enc.step2_pack_value(Qty('2 kg'))
    assert packed_qty['__qcalc_type'] == 'qty'
    assert packed_qty['value'].endswith(' kg')

    packed_dt = enc.step2_pack_value(datetime.date(2026, 1, 2))
    assert isinstance(packed_dt, str)
    assert '2026' in packed_dt

    df = pd.DataFrame({'A': [1, 2], 'B': [3, 4]})
    packed_df = enc.step2_pack_value(df)
    assert packed_df['__qcalc_type'] == 'table'
    assert packed_df['columns'] == ['A', 'B']
    assert packed_df['data'] == [[1, 3], [2, 4]]


def test_step2_unpack_for_run_unpacks_compact_markers():
    payload = {
        'mass': {'__qcalc_type': 'qty', 'value': '2 kg'},
        'tbl': {'__qcalc_type': 'table', 'columns': ['A'], 'data': [[1], [2]]},
        'chart': {
            '__qcalc_type': 'chart',
            'chtype': 'lines',
            'data': {'xvals': [1, 2], 'yvals2d': [[3, 4]], 'labels': ['s1']},
        },
    }

    out = enc.step2_unpack_for_run(payload)
    assert out['mass'] == '2 kg'
    assert out['tbl'] == {'columns': ['A'], 'data': [[1], [2]]}
    assert out['chart'] == {'xvals': [1, 2], 'yvals2d': [[3, 4]], 'labels': ['s1']}


def test_views_step2_compact_payload_uses_direct_shared_helpers(monkeypatch):
    monkeypatch.setattr(views, 'step2_pack_value', lambda value, _seen=None: {'packed': value})

    out = views._step2_compact_io_payload('demo', {'a': 1}, {'b': 2})
    assert out == {
        'function': 'demo',
        'input': {'packed': {'a': 1}},
        'output': {'packed': {'b': 2}},
    }


def test_prepare_for_json_uses_variant_profile(monkeypatch):
    marker = {'ok': 1}

    def _fake_serialize(value, profile='json', _seen=None):
        assert value == {'x': 1}
        assert profile == 'variant'
        return marker

    monkeypatch.setattr(enc, 'serialize_value', _fake_serialize)

    assert enc.prepare_for_json({'x': 1}) is marker


def test_prepare_for_json_variant_common_conversions():
    payload = {
        'when': datetime.date(2026, 1, 2),
        'qdt': QDateTime('2026-01-02 03:04:05'),
        'price': decimal.Decimal('2.5'),
        'elapsed': datetime.timedelta(minutes=2),
        'qty': Qty('2 kg'),
        'table': pd.DataFrame({'A': [1], 'B': [2]}),
        'items': [decimal.Decimal('3.5')],
    }

    out = enc.prepare_for_json(payload)
    assert isinstance(out['when'], str)
    assert isinstance(out['qdt'], str)
    assert '2026' in out['qdt']
    assert out['price'] == 2.5
    assert out['elapsed'] == 120.0
    assert isinstance(out['qty'], str)
    assert out['qty'].endswith(' kg')
    assert out['table'] == [{'A': 1, 'B': 2}]
    assert out['items'] == [3.5]


def test_reverse_prepare_for_json_uses_variant_deserialize(monkeypatch):
    marker = {'ok': 1}

    def _fake_deserialize(value, profile='variant'):
        assert value == {'x': 1}
        assert profile == 'variant'
        return marker

    monkeypatch.setattr(enc, 'deserialize_value', _fake_deserialize)

    assert enc.reverse_prepare_for_json({'x': 1}) is marker


def test_deserialize_value_step2_profile_delegates_to_step2_unpack(monkeypatch):
    marker = {'run': 1}

    def _fake_unpack(value):
        assert value == {'x': 1}
        return marker

    monkeypatch.setattr(enc, 'step2_unpack_for_run', _fake_unpack)
    out = enc.deserialize_value({'x': 1}, profile='step2')
    assert out is marker


def test_prepare_for_json_variant_detects_cycles():
    payload = {}
    payload['self'] = payload

    with pytest.raises(ValueError, match='Cyclic reference detected'):
        enc.prepare_for_json(payload)


def test_reverse_prepare_for_json_does_not_coerce_nested_list_dicts_to_dataframe():
    payload = [{'row': {'a': 1}}, {'row': {'a': 2}}]
    out = enc.reverse_prepare_for_json(payload)

    assert isinstance(out, list)
    assert out == payload
