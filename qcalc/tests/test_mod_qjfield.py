# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha
# Tests generated with AI assistance. Reviewed and validated by the author.

import datetime

import qsett

qsett.init()

import pandas as pd
import pytest

from qconst import TOK_UOM, TOK_PART, TOK_PART_UOM, TOK_INDEX_SEP
from qcore.mod_anno import (
    qchar, qcode, qdict, qfunc, qhide, qhidex, qlist, qtable, qtbl, qtexta, qhtml,
)
from qcore.mod_qjfield import QJField
import qcore.mod_qjfield as mqj


def _jf(name='x', arg_type=None, value=None, inf_class='', **kw):
    return QJField(name, arg_type, value, 'id_c_', kw.pop('required', False), inf_class, **kw)


# defaults --------------------------------------------------------------------------------------------------------

def test_a_new_field_has_the_id_prefix_name_and_default_structure():
    qjf = _jf('speed', float, 1.5, required=True)

    assert qjf.jf['name'] == 'speed'
    assert qjf.jf['attrs']['id'] == 'id_c_speed'
    assert qjf.jf['required'] is True
    assert qjf.jf['sufx'] == ''
    assert qjf.c4f == {'speed': 1}
    assert qjf.s2f == {'type': ''}
    assert qjf.jf_ex == []


def test_the_info_class_is_appended_to_the_class_of_the_type():
    assert _jf('x', float, 1.0, inf_class='wide').jf['attrs']['class'] == 'val wide'
    assert _jf('x', float, 1.0).jf['attrs']['class'] == 'val'


def test_the_value_class_of_a_part_field_is_the_part_class():
    qjf = _jf('x' + TOK_PART, 'text', 'abc')

    assert qjf.jf['attrs']['class'] == 'val-pp'  # | 'inp' becomes 'val-pp' for a part field


def test_an_unknown_annotation_raises():
    with pytest.raises(Exception, match='Unknown type'):
        _jf('x', 'no-such-type', 1)


# annotation to type ----------------------------------------------------------------------------------------------

@pytest.mark.parametrize('arg_type,jtype,cls', [
    (bool, 'boolean', ''),
    ('bool', 'boolean', ''),
    (qchar, 'char', 'chr'),
    ('date', 'date', ''),
    ('time', 'time', ''),
    ('datetime', 'datetime', ''),
    ('email', 'email', 'inp'),
    ('qfl', 'float', 'val-p'),
    ('qin', 'integer', 'val-p'),
    (float, 'float', 'val'),
    (int, 'integer', 'val'),
    ('qread', 'read', 'chr'),
    ('regex', 'regex', 'inp'),
    (str, 'text', 'inp'),
    ('qtext', 'text', 'inp'),
    ('select2', 'select2', 'select2 inp'),
    (qtexta, 'textarea', 'texta'),
    ('textedit', 'textedit', 'texte'),
    ('url', 'url', 'inp'),
    ('float-q', 'float', 'val-q'),
    ('float-pq', 'float', 'val-pq'),
    ('integer-q', 'integer', 'val-q'),
    ('integer-pq', 'integer', 'val-pq'),
    ('uom-q', 'uom', 'uom-q'),
    ('uomx-pq', 'uomx', 'uom-pq'),
    ('uom2-q', 'uom2', 'select2 uom-q'),
    ('uom2-pq', 'uom2', 'select2 uom-pq'),
    ('choice', 'choice', 'inp'),
    ('checkboxselectmultiple', 'checkboxselectmultiple', 'mcheck'),
    ('radio', 'radio', 'radio'),
    ('range', 'range', 'inp'),
    ('slug', 'slug', ''),
])
def test_an_annotation_selects_the_field_type_and_class(arg_type, jtype, cls):
    qjf = _jf('x', arg_type, None)

    assert qjf.jf['type'] == jtype
    assert qjf.jf['attrs']['class'] == cls
    assert qjf.s2f == {'type': ''}


def test_the_select2_annotation_is_recorded_in_the_document_info():
    assert _jf('x', 'select2', '').doc_info == {'qsel2': True}


@pytest.mark.parametrize('arg_type', ['file', 'image'])
def test_file_fields_validate_the_size_and_pass_to_the_function(arg_type):
    qjf = _jf('x', arg_type)

    assert qjf.jf['type'] == arg_type
    assert qjf.s2f == {'type': arg_type}
    assert qjf.jf['attrs']['onchange'] == 'validateFileSize(this)'


def test_hidden_fields_are_passed_to_the_function_unless_they_are_hidden_extras():
    assert _jf('x', qhide, 1).jf['type'] == 'hidden'
    assert _jf('x', qfunc, 1).s2f == {'type': ''}
    hidex = _jf('x', qhidex, 1)
    assert hidex.jf['type'] == 'hidden'
    assert hidex.s2f == {'type': 'x'}


def test_a_code_field_is_required_and_a_checkbox_is_not():
    assert _jf('x', qcode, '').jf['required'] is True
    assert _jf('x', 'checkbox', True, required=True).jf['required'] is False


def test_a_button_and_an_html_field_are_not_passed_to_the_function():
    button = _jf('x', 'btn:1', 'Go')
    html = _jf('x', 'html', '<b>x</b>')

    assert button.jf['type'] == 'btn:1'
    assert button.s2f == {'type': 'x'}
    assert html.jf['type'] == 'html'
    assert html.s2f == {'type': 'x'}


# value to type ---------------------------------------------------------------------------------------------------

@pytest.mark.parametrize('value,jtype,cls', [
    (None, 'float', 'unknown'),
    (1.5, 'float', 'val'),
    (3, 'integer', 'val'),
    (True, 'checkbox', ''),
    (False, 'checkbox', ''),
    ([1, 2], 'multiplechoice', 'unknown'),
])
def test_a_value_without_annotation_selects_the_field_type(value, jtype, cls):
    qjf = _jf('x', None, value)

    assert qjf.jf['type'] == jtype
    assert qjf.jf['attrs']['class'] == cls


def test_a_bool_is_a_checkbox_and_not_an_integer():
    assert _jf('x', None, True).jf['type'] == 'checkbox'


def test_date_time_and_datetime_values_are_told_apart():
    assert _jf('x', None, datetime.date(2026, 1, 2)).jf['type'] == 'date'
    assert _jf('x', None, datetime.time(1, 2)).jf['type'] == 'time'
    assert _jf('x', None, datetime.datetime(2026, 1, 2, 3, 4)).jf['type'] == 'datetime'


def test_an_unsupported_value_raises():
    with pytest.raises(TypeError, match='not supported'):
        _jf('x', None, {1, 2})


def test_a_dataframe_value_becomes_a_table():
    qjf = _jf('x', None, pd.DataFrame({'a': [1]}))

    assert qjf.jf['type'] == 'table'
    assert qjf.s2f == {'type': 'table'}


def test_a_qhtml_value_is_a_display_only_field():
    qjf = _jf('x', None, qhtml('<p>hi</p>'))

    assert qjf.jf['type'] == 'html'
    assert qjf.s2f == {'type': 'x'}


# string values ---------------------------------------------------------------------------------------------------

def test_a_short_or_long_plain_string_is_text():
    short = _jf('x', None, 'ab')
    long = _jf('x', None, 'a' * 40)

    for qjf, value in ((short, 'ab'), (long, 'a' * 40)):
        assert qjf.jf['type'] == 'text'
        assert qjf.jf['attrs']['class'] == 'unknown'
        assert qjf.jf['initial'] == value


def test_a_string_that_is_not_a_date_is_text():
    qjf = _jf('x', None, 'hello world')

    assert qjf.jf['type'] == 'text'
    assert qjf.jf['initial'] == 'hello world'


@pytest.mark.parametrize('value,jtype', [
    ('2026-01-02', 'date'),
    ('2026-01-02T03:04:05', 'datetime'),
])
def test_an_iso_date_string_is_a_date_or_datetime_field(value, jtype):
    qjf = _jf('x', None, value)

    assert qjf.jf['type'] == jtype
    assert qjf.jf['initial'] == value


def test_a_string_is_stripped_before_its_type_is_decided():
    assert _jf('x', None, '   2026-01-02  ').jf['initial'] == '2026-01-02'


@pytest.mark.parametrize('uom_v2,jtype', [(True, 'uom2'), (False, 'uom')])
def test_a_unit_string_follows_the_uom_interface_setting(monkeypatch, uom_v2, jtype):
    monkeypatch.setitem(mqj.gs, 'uom_v2', uom_v2)

    qjf = _jf('x', None, 'kg')

    assert qjf.jf['type'] == jtype
    assert qjf.jf['initial'] == 'kg'


# units -----------------------------------------------------------------------------------------------------------

@pytest.mark.parametrize('arg_type,uom_v2,jtype,cls', [
    ('uom', False, 'uom', 'uom'),
    ('uom', True, 'uom2', 'select2 uom'),
    ('uomx', False, 'uom', 'uom'),
    ('uom2', False, 'uom2', 'select2 uom'),
])
def test_a_unit_field_takes_the_stripped_value_as_initial(monkeypatch, arg_type, uom_v2, jtype, cls):
    monkeypatch.setitem(mqj.gs, 'uom_v2', uom_v2)

    qjf = _jf('x', arg_type, '  m  ')

    assert qjf.jf['type'] == jtype
    assert qjf.jf['initial'] == 'm'
    assert qjf.jf['attrs']['class'] == cls


def test_a_unit_field_without_a_value_starts_empty():
    assert _jf('x', 'uom', None).jf['initial'] == ''


# quantities ------------------------------------------------------------------------------------------------------

def test_a_quantity_is_a_value_field_and_a_unit_field():
    qjf = _jf('mass', 'qt', '3 kg')

    assert qjf.jf['type'] == 'float'
    assert qjf.jf['initial'] == 3
    assert qjf.jf['attrs']['class'] == 'val-q'
    assert qjf.s2f == {'type': 'qty', 'parts': 1}
    assert qjf.c4f == {'mass': 2}
    assert [c.name for c in qjf.jf_ex] == ['mass' + TOK_UOM]
    assert qjf.jf_ex[0].jf['initial'] == 'kg'
    assert qjf.jf_ex[0].jf['required'] is True


def test_the_quantity_interface_can_be_chosen_by_the_annotation():
    for arg_type, jtype in (('qtx', 'uomx'), ('qt2', 'uom2')):
        unit = _jf('m', arg_type, '3 kg').jf_ex[0]
        assert unit.jf['type'] == jtype
        assert unit.jf['attrs']['class'].endswith('uom-q')


def test_a_multi_part_quantity_has_a_value_and_a_unit_for_each_part():
    qjf = _jf('t', 'qt', '1 hr, 30 min')

    assert qjf.s2f == {'type': 'qty', 'parts': 2}
    assert qjf.c4f == {'t': 4}
    assert qjf.jf['type'] == 'integer'
    assert qjf.jf['initial'] == 1
    assert qjf.jf['attrs']['class'] == 'val-pq'
    names = [c.name for c in qjf.jf_ex]
    assert names == [
        't' + TOK_PART_UOM,
        't' + TOK_INDEX_SEP + '2' + TOK_PART,
        't' + TOK_INDEX_SEP + '2' + TOK_PART_UOM,
    ]
    assert [c.jf['initial'] for c in qjf.jf_ex] == ['hr', 30, 'min']
    assert qjf.jf_ex[1].jf['type'] == 'float'


def test_a_quantity_string_without_an_annotation_is_a_quantity():
    qjf = _jf('mass', None, '3 kg')

    assert qjf.s2f['type'] == 'qty'
    assert qjf.jf_ex[0].name == 'mass' + TOK_UOM


def test_a_composite_quantity_keeps_its_children_apart():
    qjf = _jf('t', 'qtc', '1 hr, 30 min')

    assert qjf.s2f == {'type': 'c'}
    assert qjf.jf['type'] == 'qty'
    assert qjf.jf['initial'] is None
    names = [c.name for c in qjf.jf_ex]
    assert names == [
        't',
        't' + TOK_PART_UOM,
        't' + TOK_INDEX_SEP + '2' + TOK_PART,
        't' + TOK_INDEX_SEP + '2' + TOK_PART_UOM,
    ]
    assert [c.jf['sufx'] for c in qjf.jf_ex] == [
        '', 'part_uom', '2' + TOK_PART, '2' + TOK_PART_UOM]


def test_a_single_composite_quantity_has_one_value_and_one_unit():
    qjf = _jf('m', 'qtc', '3 kg')

    assert [c.name for c in qjf.jf_ex] == ['m', 'm' + TOK_UOM]
    assert qjf.jf_ex[1].jf['sufx'] == 'uom'


# lists -----------------------------------------------------------------------------------------------------------

def test_a_list_gets_a_field_per_item_and_add_and_remove_buttons():
    qjf = _jf('v', qlist[float], [1.0, 2.0, 3.0])

    assert qjf.s2f == {'type': 'qlist'}
    assert qjf.c4f == {'v': 3}
    assert qjf.doc_info == {'qlist': True}
    assert qjf.jf['type'] == 'float'
    assert qjf.jf['initial'] == 1.0
    assert [c.name for c in qjf.jf_ex] == [
        'v' + TOK_INDEX_SEP + '1', 'v' + TOK_INDEX_SEP + '2', 'list_add_v', 'list_del_v']
    assert [c.jf['initial'] for c in qjf.jf_ex[:2]] == [2.0, 3.0]
    assert all(c.jf['attrs']['class'] == 'val' for c in qjf.jf_ex[:2])
    assert all(c.s2f == {'type': 'x'} for c in qjf.jf_ex[2:])
    assert [c.jf['initial'] for c in qjf.jf_ex[2:]] == ['+', '-']


def test_an_empty_list_starts_with_one_empty_item():
    qjf = _jf('v', qlist[qchar], [])

    assert qjf.c4f == {'v': 1}
    assert qjf.jf['type'] == 'char'
    assert qjf.jf['initial'] == ''
    assert [c.name for c in qjf.jf_ex] == ['list_add_v', 'list_del_v']


# dict and tables -------------------------------------------------------------------------------------------------

def test_a_dict_counts_its_items_as_fields():
    qjf = _jf('d', qdict, {'a': 1, 'b': 2})

    assert qjf.c4f == {'d': 2}


def test_a_table_is_a_table_field_that_reports_the_table_input():
    qjf = _jf('t', qtable, pd.DataFrame({'a': [1]}), inf_class='table-in')

    assert qjf.jf['type'] == 'table'
    assert qjf.s2f == {'type': 'table'}
    assert qjf.jf['attrs']['class'] == 'table-in'
    assert qjf.doc_info == {'url': False, 'table_in': True}


def test_a_qtbl_is_a_plain_table_field():
    qjf = _jf('t', qtbl, {'columns': ['a'], 'data': [[1]]})

    assert qjf.jf['type'] == 'table'
    assert qjf.s2f == {'type': 'tbl'}
    assert qjf.doc_info['table_in'] is True
    assert qjf.jf['attrs']['class'] == ''
