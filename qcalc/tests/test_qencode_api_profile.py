import datetime
import decimal
import json

import numpy as np
import pandas as pd
import qsett

qsett.init()

from qcore import Qty, QChart, qerror, qwarn, qhtml
from qcore import mod_qencode as enc


def _dumps(value):
    # allow_nan=False proves the packed value is strict JSON
    return json.dumps(value, allow_nan=False)


def test_qty_keeps_value_and_unit_separately():
    packed = enc.api_pack_value(Qty('2 kg'))
    assert packed['__qcalc_type'] == 'qty'
    assert packed['value'] == 2.0
    assert packed['unit'] == 'kg'
    assert packed['text'].endswith(' kg')


def test_float_noise_trimmed_and_nan_inf_become_none():
    assert enc.api_pack_value(36133.33350000001) == 36133.3335
    assert enc.api_pack_value(float('nan')) is None
    assert enc.api_pack_value(float('inf')) is None
    assert enc.api_pack_value(np.float64(1.5)) == 1.5
    assert enc.api_pack_value(decimal.Decimal('2.5')) == 2.5


def test_table_cells_are_packed_for_dataframe_and_qtbl_dict():
    cells = [[Qty('2 kg'), 1], [Qty('3 kg'), 2]]
    df = pd.DataFrame(cells, columns=['mass', 'n'])
    from_df = enc.api_pack_value(df)
    from_dict = enc.api_pack_value({'columns': ['mass', 'n'], 'data': cells})

    for packed in (from_df, from_dict):
        assert packed['__qcalc_type'] == 'table'
        assert packed['columns'] == ['mass', 'n']
        assert packed['data'][0][0]['__qcalc_type'] == 'qty'
        assert packed['data'][1][1] == 2
        _dumps(packed)


def test_compact_mode_truncates_tables_and_omits_chart_data():
    rows = [[i] for i in range(50)]
    packed = enc.api_pack_value({'columns': ['i'], 'data': rows}, compact=True, max_rows=5)
    assert len(packed['data']) == 5
    assert packed['truncated'] is True
    assert packed['total_rows'] == 50

    chart = QChart()
    chart.save_data({'xvals': [1, 2], 'labels': ['s1']}, 'lines')
    full = enc.api_pack_value(chart)
    assert full['data'] == {'xvals': [1, 2], 'labels': ['s1']}
    assert enc.api_pack_value(chart, compact=True) == {
        '__qcalc_type': 'chart', 'chtype': 'lines', 'omitted': True}


def test_messages_are_tagged_not_plain_strings():
    assert enc.api_pack_value(qerror('boom')) == {'__qcalc_type': 'error', 'text': 'boom'}
    assert enc.api_pack_value(qwarn('careful'))['__qcalc_type'] == 'warning'
    assert enc.api_pack_value(qhtml('<b>x</b>'))['__qcalc_type'] == 'html'
    assert enc.api_pack_value('plain') == 'plain'


def test_dates_timedelta_and_unknown_objects():
    assert '2026' in enc.api_pack_value(datetime.date(2026, 1, 2))
    assert enc.api_pack_value(datetime.timedelta(minutes=2)) == 120.0
    assert isinstance(enc.api_pack_value(object()), str)


def test_cycles_are_broken_and_shared_references_kept():
    cyclic = {'name': 'x'}
    cyclic['self'] = cyclic
    assert enc.api_pack_value(cyclic) == {'name': 'x', 'self': None}

    shared = [1, 2]
    assert enc.api_pack_value({'a': shared, 'b': shared}) == {'a': [1, 2], 'b': [1, 2]}


def test_serialize_value_api_profile_delegates():
    assert enc.serialize_value({'x': 1.0}, profile='api') == {'x': 1.0}
    assert enc.deserialize_value({'__qcalc_type': 'qty', 'value': 2.0, 'unit': 'kg'}, profile='api') == '2.0 kg'


def test_api_unpack_round_trips_inputs():
    payload = {
        'mass': {'__qcalc_type': 'qty', 'value': 2.0, 'unit': 'kg', 'text': '2.0 kg'},
        'tbl': {'__qcalc_type': 'table', 'columns': ['A'],
                'data': [[{'__qcalc_type': 'qty', 'value': 1, 'unit': 'm'}], [3]]},
        'plain': [1, 'x'],
    }
    out = enc.api_unpack_value(payload)
    assert out['mass'] == '2.0 kg'
    assert out['tbl'] == {'columns': ['A'], 'data': [['1 m'], [3]]}
    assert out['plain'] == [1, 'x']
