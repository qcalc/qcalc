# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha
# Tests generated with AI assistance. Reviewed and validated by the author.

from types import SimpleNamespace

import qsett

qsett.init()

import pytest
from django.http import QueryDict

import calc.views_form_data as vfd
from calc.mod_hookctx import HookContext
from calc.views_form_data import q11422_form_data_modify_after_post, q11423_form_data_apply_posted
from qcore import Qty, qt


def _fld(name, ftype, initial=None, **extra):
    return {'name': name, 'type': ftype, 'initial': initial, **extra}


def _request(post, schema, method='POST', cmd='__modify', extra=None):
    data = QueryDict(mutable=True)
    for key, value in post.items():
        data.setlist(key, value if isinstance(value, list) else [value])
    if extra is None:  # | a button post carries its command in extra
        extra = {'cmd': cmd} if cmd else {}
    return SimpleNamespace(
        method=method, cmd=cmd, extra=extra, POST=data, FILES={},
        json_schema=schema, json_data={f['name']: f['initial'] for f in schema})


def _initial(request, name):
    fld = next(f for f in request.json_schema if f['name'] == name)
    assert request.json_data[name] == fld['initial']
    return fld['initial']


# the value that __modify() receives ------------------------------------------------------------------------------

def _modify(monkeypatch, post, arg_name, sig_type):
    # | runs q11422 for a '__modify' button that lists arg_name, returns what the hook was given
    seen = []

    def hook(ctx, name, value, action):
        seen.append(value)
        return value

    monkeypatch.setattr(vfd.QCals, 'func_exists', lambda name: name == 'f__modify')
    monkeypatch.setattr(vfd.QCals, 'addr', lambda name: hook)
    data = QueryDict(mutable=True)
    for key, value in post.items():
        data.setlist(key, [value])
    ctx = HookContext(func_id='f', posted={key: [value] for key, value in post.items()})
    request = SimpleNamespace(method='POST', cmd='__modify', POST=data, hook_ctx=ctx,
                              extra={'cmd': '__modify', 'args': [arg_name], 'kwargs': {}})

    q11422_form_data_modify_after_post(request, 'f', sig_type, arg_name, None)

    assert len(seen) == 1
    return seen[0]


def test_modify_gets_a_quantity_joined_from_its_value_and_unit(monkeypatch):
    value = _modify(monkeypatch, {'mass': '3', 'mass_uom': 'kg'}, 'mass', qt)

    assert value == Qty('3 kg')


def test_modify_gets_a_multi_part_quantity(monkeypatch):
    post = {'t': '1', 't_part_uom': 'hr', 't__2_part': '30', 't__2_part_uom': 'min'}

    assert _modify(monkeypatch, post, 't', qt) == Qty('1 hr, 30 min')


def test_modify_gets_the_posted_text_for_a_quantity_without_a_unit_instead_of_failing(monkeypatch):
    assert _modify(monkeypatch, {'mass': '3'}, 'mass', qt) == '3'
    assert _modify(monkeypatch, {'mass': '', 'mass_uom': 'kg'}, 'mass', qt) == ''


def test_modify_gets_numbers_converted_and_invalid_numbers_as_text(monkeypatch):
    assert _modify(monkeypatch, {'n': '5'}, 'n', int) == 5
    assert _modify(monkeypatch, {'x': '2.5'}, 'x', float) == 2.5
    assert _modify(monkeypatch, {'x': 'abc'}, 'x', float) == 'abc'


def test_modify_gets_false_for_a_checkbox_that_was_not_posted(monkeypatch):
    assert _modify(monkeypatch, {'other': 'x'}, 'flag', bool) is False


def test_posted_text_and_number_values_replace_the_defaults():
    req = _request({'x': '99', 'y': '2.5', 'note': 'hello', 'code': 'a = 1', 'n': ''},
                   [_fld('x', 'integer', 3), _fld('y', 'float', 1.0), _fld('note', 'text', 'Hi'),
                    _fld('code', 'codeedit', ''), _fld('n', 'integer', 7)])

    q11423_form_data_apply_posted(req)

    assert _initial(req, 'x') == 99
    assert _initial(req, 'y') == 2.5
    assert _initial(req, 'note') == 'hello'
    assert _initial(req, 'code') == 'a = 1'
    assert _initial(req, 'n') is None  # cleared by the user


def test_invalid_number_keeps_the_current_value():
    req = _request({'x': 'abc'}, [_fld('x', 'integer', 3)])

    q11423_form_data_apply_posted(req)

    assert _initial(req, 'x') == 3


def test_fields_missing_from_the_post_keep_their_values():
    req = _request({'x': '5'}, [_fld('x', 'integer', 3), _fld('note', 'text', 'Hi')])

    q11423_form_data_apply_posted(req)

    assert _initial(req, 'x') == 5
    assert _initial(req, 'note') == 'Hi'


@pytest.mark.parametrize('ftype', ['checkbox', 'boolean'])
def test_unchecked_checkbox_is_false_because_browsers_do_not_post_it(ftype):
    unchecked = _request({'other': '1'}, [_fld('flag', ftype, True)])
    checked = _request({'flag': 'on'}, [_fld('flag', ftype, False)])

    q11423_form_data_apply_posted(unchecked)
    q11423_form_data_apply_posted(checked)

    assert _initial(unchecked, 'flag') is False
    assert _initial(checked, 'flag') is True


def test_multiple_select_keeps_offered_values_only_and_empty_means_nothing_selected():
    schema = [_fld('units', 'multiplechoice', ['ft'], choices=[('m', 'meter'), ('km', 'kilometer')])]
    some = _request({'units': ['m', 'ft', 'km']}, schema)
    none = _request({'other': '1'}, [dict(schema[0])])

    q11423_form_data_apply_posted(some)
    q11423_form_data_apply_posted(none)

    assert _initial(some, 'units') == ['m', 'km']
    assert _initial(none, 'units') == []


@pytest.mark.parametrize('ftype', ['choice', 'radio'])
def test_single_choice_uses_posted_value_only_when_still_offered(ftype):
    choices = {'u2u': 'Unit', 'q2u': 'Quantity'}
    offered = _request({'mode': 'q2u'}, [_fld('mode', ftype, 'u2u', choices=choices)])
    stale = _request({'mode': 'q2q'}, [_fld('mode', ftype, 'u2u', choices=choices)])

    q11423_form_data_apply_posted(offered)
    q11423_form_data_apply_posted(stale)

    assert _initial(offered, 'mode') == 'q2u'
    assert _initial(stale, 'mode') == 'u2u'


@pytest.mark.parametrize('ftype', ['choice', 'radio'])
@pytest.mark.parametrize('current', ['q2q', None, ''])
def test_single_choice_falls_back_to_the_first_offered_when_posted_and_current_values_are_gone(ftype, current):
    # | e.g. the posted mode and the remembered mode are both 'q2q', but the new quantity offers 'u2u' only
    req = _request({'mode': 'q2q'}, [_fld('mode', ftype, current, choices={'u2u': 'Unit'})])

    q11423_form_data_apply_posted(req)

    assert _initial(req, 'mode') == 'u2u'


def test_a_choice_without_offered_values_is_left_alone():
    req = _request({'mode': 'q2q'}, [_fld('mode', 'choice', 'q2q', choices=[])])

    q11423_form_data_apply_posted(req)

    assert _initial(req, 'mode') == 'q2q'


def test_fields_modified_by_the_command_are_left_to_the_hook():
    req = _request({'y': '10', 'code': 'typed', 'x': '5'},
                   [_fld('y', 'integer', 100), _fld('code', 'codeedit', 'formatted'), _fld('x', 'integer', 3)],
                   extra={'cmd': '__modify', 'args': ['y'], 'kwargs': {'code': 'format'}})

    q11423_form_data_apply_posted(req)

    assert _initial(req, 'y') == 100
    assert _initial(req, 'code') == 'formatted'
    assert _initial(req, 'x') == 5


def test_disabled_and_complex_fields_are_not_touched():
    req = _request({'locked': 'new', 'tbl': '{"columns": []}', 'upload': 'x', 'q': 'M', 'flag': 'on'},
                   [_fld('locked', 'text', 'old', disabled=True), _fld('tbl', 'table', 'old'),
                    _fld('upload', 'file', None), _fld('q', 'select2', 'L')])

    q11423_form_data_apply_posted(req)

    assert _initial(req, 'locked') == 'old'
    assert _initial(req, 'tbl') == 'old'
    assert _initial(req, 'upload') is None
    assert _initial(req, 'q') == 'L'


@pytest.mark.parametrize('method, cmd', [('GET', '__modify'), ('POST', ''), ('POST', '__command'), ('POST', 'run')])
def test_only_a_posted_modify_or_load_button_is_affected(method, cmd):
    req = _request({'x': '99'}, [_fld('x', 'integer', 3)], method=method, cmd=cmd)

    q11423_form_data_apply_posted(req)

    assert _initial(req, 'x') == 3


LOAD_EXTRA = {'cmd': 'load', 'from': 'upload_csv', 'to': 'csv_table', 'url': 'csv_url',
              'delimiter': 'delimiter', 'quoting': 'quoting'}


def test_load_button_keeps_the_other_typed_values_and_leaves_the_loaded_table_alone():
    schema = [_fld('delimiter', 'char', ','), _fld('csv_url', 'url', 'http://default'),
              _fld('normalize_units', 'checkbox', True), _fld('csv_table', 'table', 'loaded table'),
              _fld('upload_csv', 'file', None)]
    req = _request({'delimiter': '|', 'csv_url': '', 'csv_table': 'old text', 'other': '1'}, schema,
                   cmd='load', extra=dict(LOAD_EXTRA))

    q11423_form_data_apply_posted(req)

    assert _initial(req, 'delimiter') == '|'
    assert _initial(req, 'csv_url') == ''
    assert _initial(req, 'normalize_units') is False  # unchecked by the user
    assert _initial(req, 'csv_table') == 'loaded table'
    assert _initial(req, 'upload_csv') is None


def test_the_target_field_of_a_load_is_never_replaced_by_the_posted_value():
    req = _request({'data': 'posted text'}, [_fld('data', 'text', 'loaded')], cmd='load',
                   extra={'cmd': 'load', 'from': 'data', 'to': 'data'})

    q11423_form_data_apply_posted(req)

    assert _initial(req, 'data') == 'loaded'


def test_opening_a_saved_input_file_is_not_affected():
    # | the open-file post is a 'load' post without any button data, the loaded values must stay
    schema = [_fld('normalize_units', 'checkbox', True), _fld('units', 'multiplechoice', ['m'], choices=['m', 'ft']),
              _fld('delimiter', 'char', ';')]
    req = _request({}, schema, cmd='load', extra={})

    q11423_form_data_apply_posted(req)

    assert _initial(req, 'normalize_units') is True
    assert _initial(req, 'units') == ['m']
    assert _initial(req, 'delimiter') == ';'
