# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha
# Tests generated with AI assistance. Reviewed and validated by the author.

import json
from types import SimpleNamespace

import qsett

qsett.init()

import pytest
from django.http import QueryDict

from calc.mod_hookctx import HookContext
from calc.views_form_data import (
    q11421_get_extra_form_data_posted,
    q11423_form_data_apply_posted,
    q11424_form_data_add_reload_triggers,
)
from calculators.all.general.author.mod_mycal_validation import INFO_VALIDATOR


def _fld(name, ftype, initial=None, **extra):
    return {'name': name, 'type': ftype, 'initial': initial, 'attrs': {'class': 'inp'}, **extra}


def _post(fields):
    data = QueryDict(mutable=True)
    for key, value in fields.items():
        data.setlist(key, value if isinstance(value, list) else [value])
    return data


# trigger attributes ----------------------------------------------------------------------------------------------

def _trigger_attrs(reload):
    fld = _fld('quantity', 'choice', 'L', reload=reload)
    request = SimpleNamespace(json_schema=[fld, _fld('other', 'text')])

    q11424_form_data_add_reload_triggers(request, 'conv2')

    return fld['attrs'], request.json_schema[1]['attrs']


def test_a_field_with_a_reload_list_gets_the_trigger_attributes():
    attrs, other = _trigger_attrs(['from_unit', 'to_units'])

    assert attrs['hx-post'] == '/calc/conv2/?part=2'
    assert attrs['hx-trigger'] == 'change'
    assert attrs['hx-target'] == 'closest form'
    assert attrs['hx-swap'] == 'innerHTML'
    assert attrs['data-interactive-ignore'] == 'true'
    assert attrs['class'] == 'inp'  # existing attributes are kept
    assert other == {'class': 'inp'}  # other fields are not touched


def test_the_trigger_posts_a_structural_modify_command_with_the_fields_to_reset():
    attrs, _ = _trigger_attrs(['from_unit', 'to_units'])

    vals = json.loads(attrs['hx-vals'])

    assert vals['qcalc_structural_cmd'] == '1'
    assert vals['extra'] == {'cmd': '__modify', 'args': [], 'kwargs': {}, 'reload': True,
                             'reset': ['from_unit', 'to_units']}


def test_reload_true_resets_nothing_and_reload_false_or_missing_adds_no_trigger():
    attrs, _ = _trigger_attrs(True)
    assert json.loads(attrs['hx-vals'])['extra']['reset'] == []

    assert 'hx-post' not in _trigger_attrs(False)[0]
    assert 'hx-post' not in _trigger_attrs(None)[0]


def test_the_unit_input_of_a_quantity_gets_the_same_trigger_as_its_value_input():
    value = _fld('mass', 'float', 2.0, reload=['total'])
    unit = _fld('mass_uom', 'uom2-q', 'kg')
    other_unit = _fld('weight_uom', 'uom2-q', 'kg')
    other = _fld('massive', 'float', 1.0)
    request = SimpleNamespace(json_schema=[value, unit, other_unit, other])

    q11424_form_data_add_reload_triggers(request, 'conv2')

    assert unit['attrs']['hx-vals'] == value['attrs']['hx-vals']
    assert unit['attrs']['hx-trigger'] == 'change'
    assert 'hx-post' not in other_unit['attrs'] and 'hx-post' not in other['attrs']


# what the server does with the posted command ----------------------------------------------------------------------

def _request(fields, extra):
    post = _post({**fields, 'extra': json.dumps(extra)})
    return SimpleNamespace(method='POST', GET=QueryDict(), POST=post, cmd='', extra={})


def test_posted_values_of_the_reset_fields_are_dropped_and_the_others_are_kept():
    request = _request({'quantity': 'M', 'from_unit': 'ft', 'to_units': 'm', 'value': '99'},
                       {'cmd': '__modify', 'args': [], 'kwargs': {}, 'reload': True, 'reset': ['from_unit', 'to_units']})

    q11421_get_extra_form_data_posted(request)

    assert request.cmd == '__modify'
    assert 'from_unit' not in request.POST and 'to_units' not in request.POST
    assert request.POST['quantity'] == 'M' and request.POST['value'] == '99'


def test_a_post_without_a_reset_list_keeps_all_posted_values():
    request = _request({'from_unit': 'ft'}, {'cmd': '__modify', 'args': ['x'], 'kwargs': {}})

    q11421_get_extra_form_data_posted(request)

    assert request.POST['from_unit'] == 'ft'


def test_posted_values_of_the_reset_fields_are_not_seen_by_the_hooks():
    request = SimpleNamespace(
        method='POST', GET=QueryDict(), cmd='', recall=False, user=SimpleNamespace(is_authenticated=False),
        session={'hash': 'h'},
        POST=_post({'quantity': 'M', 'value': '7',
                    'extra': json.dumps({'cmd': '__modify', 'reload': True, 'reset': ['quantity']})}))

    ctx = HookContext.from_request(request, 'conv2', 'c1', {})

    assert ctx.posted_kwargs == {'value': '7'}


def test_the_fields_to_reset_are_not_replaced_by_their_posted_value():
    schema = [_fld('quantity', 'choice', 'L', choices={'L': 'Length', 'M': 'Mass'}),
              _fld('value', 'float', 1.0), _fld('from_unit', 'text', 'amu')]
    request = SimpleNamespace(
        method='POST', cmd='__modify', POST=_post({'quantity': 'M', 'value': '99', 'from_unit': 'ft'}), FILES={},
        extra={'cmd': '__modify', 'args': [], 'kwargs': {}, 'reload': True, 'reset': ['from_unit']},
        json_schema=schema, json_data={f['name']: f['initial'] for f in schema})

    q11423_form_data_apply_posted(request)

    assert request.json_data == {'quantity': 'M', 'value': 99.0, 'from_unit': 'amu'}


# frontend calculator validation ---------------------------------------------------------------------------------

def _info_errors(reload):
    info = {'title': 'T', 'schema': {'quantity': {'type': 'choice', 'reload': reload}}}
    return list(INFO_VALIDATOR.iter_errors(info))


@pytest.mark.parametrize('reload', [['from_unit', 'to_units'], True, False, []])
def test_the_validation_of_frontend_calculators_accepts_a_reload_key(reload):
    assert _info_errors(reload) == []


@pytest.mark.parametrize('reload', ['from_unit', 5, [1, 2], {'a': 1}])
def test_the_validation_of_frontend_calculators_rejects_a_malformed_reload_key(reload):
    assert _info_errors(reload)
