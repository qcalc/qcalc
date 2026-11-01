# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha
# Tests generated with AI assistance. Reviewed and validated by the author.

import json

import qsett

qsett.init()

import pytest
from django.contrib.auth.models import AnonymousUser
from django.contrib.sessions.middleware import SessionMiddleware
from django.test import RequestFactory

from calc.mod_hookctx import HookContext
from calculators.all.general import cal_conv


def _request(method='get', data=None, cmd='', recall=False):
    rf = RequestFactory()
    req = rf.post('/calc/conv2/', data=data or {}) if method == 'post' else rf.get('/calc/conv2/', data=data or {})
    SessionMiddleware(lambda r: None).process_request(req)
    req.session['hash'] = 'anon-hash'
    req.session.save()
    req.user = AnonymousUser()
    req.cmd = cmd
    req.recall = recall
    return req


def _ctx(request, **kwargs):
    return HookContext.from_request(
        request, 'conv2', 'conv2__abc', kwargs.get('var_url_kwargs', {}), kwargs.get('remembered'))


def test_posted_values_are_text_and_transport_keys_are_excluded():
    req = _request('post', {
        'quantity': 'M', 'from_unit': ['amu', 'ana'], 'csrfmiddlewaretoken': 'x',
        'cid': 'conv2__abc', 'input_id': '0', 'qcalc_structural_cmd': '1', 'extra': '{}',
    })
    ctx = _ctx(req)

    assert ctx.is_post
    assert ctx.posted('quantity') == 'M'
    assert ctx.posted('from_unit') == 'ana'
    assert ctx.posted_list('from_unit') == ['amu', 'ana']
    assert ctx.posted('missing') is None
    assert ctx.posted('missing', 'dflt') == 'dflt'
    assert ctx.posted_list('missing') == []
    for key in ('csrfmiddlewaretoken', 'cid', 'input_id', 'qcalc_structural_cmd', 'extra'):
        assert ctx.posted(key) is None


def test_posted_list_returns_a_copy():
    ctx = _ctx(_request('post', {'from_unit': ['amu', 'ana']}))

    ctx.posted_list('from_unit').append('x')

    assert ctx.posted_list('from_unit') == ['amu', 'ana']


def test_posted_kwargs_holds_the_last_text_value_of_each_field():
    ctx = _ctx(_request('post', {
        'quantity': 'M', 'from_unit': ['amu', 'ana'], 'csrfmiddlewaretoken': 'x', 'extra': '{}',
    }))

    assert ctx.posted_kwargs == {'quantity': 'M', 'from_unit': 'ana'}
    assert ctx.posted_kwargs.get('quantity') == ctx.posted('quantity')


def test_get_request_has_no_posted_values():
    ctx = _ctx(_request('get', {'quantity': 'M'}), var_url_kwargs={'quantity': 'M'})

    assert not ctx.is_post
    assert ctx.posted('quantity') is None
    assert ctx.posted_kwargs == {}
    assert ctx.var_url('quantity') == 'M'


def test_command_and_extra_come_from_the_posted_extra():
    extra = {'cmd': '__Modify', 'args': ['a'], 'kwargs': {'code': 'format'}}
    ctx = _ctx(_request('post', {'extra': json.dumps(extra)}, cmd='run'))

    assert ctx.cmd == '__modify'
    assert ctx.extra['args'] == ['a']
    assert ctx.extra['kwargs'] == {'code': 'format'}


def test_extra_is_a_copy():
    ctx = _ctx(_request('post', {'extra': json.dumps({'cmd': '__command', 'args': ['a']})}))

    ctx.extra['args'].append('b')

    assert ctx.extra['args'] == ['a']


def test_command_falls_back_to_request_command_without_extra():
    assert _ctx(_request('get', cmd='load')).cmd == 'load'
    assert _ctx(_request('post', {'quantity': 'M'}, cmd='run')).cmd == 'run'


@pytest.mark.parametrize('extra', ['{}', 'not json', '[1]'])
def test_empty_or_invalid_extra_means_no_command(extra):
    ctx = _ctx(_request('post', {'extra': extra}, cmd='run'))

    assert ctx.cmd == ''
    assert ctx.extra == {}


def test_value_methods_and_kwargs_properties_agree_for_each_source():
    ctx = _ctx(_request(), var_url_kwargs={'quantity': 'M'}, remembered={'quantity': 'L', 'from_unit': ['ft']})

    assert ctx.var_url('quantity') == 'M'
    assert ctx.var_url('missing') is None
    assert ctx.var_url('missing', 'dflt') == 'dflt'
    assert ctx.var_url_kwargs == {'quantity': 'M'}
    assert ctx.remembered('quantity') == 'L'
    assert ctx.remembered('from_unit') == ['ft']
    assert ctx.remembered('missing', 'dflt') == 'dflt'
    assert ctx.remembered_kwargs == {'quantity': 'L', 'from_unit': ['ft']}


def test_kwargs_properties_return_copies():
    ctx = _ctx(_request('post', {'quantity': 'M'}), var_url_kwargs={'quantity': 'M'}, remembered={'quantity': 'L'})

    ctx.var_url_kwargs['quantity'] = 'T'
    ctx.remembered_kwargs['quantity'] = 'T'
    ctx.posted_kwargs['quantity'] = 'T'

    assert ctx.var_url('quantity') == 'M'
    assert ctx.remembered('quantity') == 'L'
    assert ctx.posted('quantity') == 'M'


def test_values_that_are_not_text_are_kept():
    marker = object()
    ctx = _ctx(_request(), var_url_kwargs={'items': marker}, remembered={'items': marker})

    assert ctx.var_url('items') is marker
    assert ctx.var_url_kwargs['items'] is marker
    assert ctx.remembered('items') is marker


def test_context_holds_no_request_and_cannot_be_extended():
    req = _request()
    ctx = _ctx(req)

    assert not any(getattr(ctx, name, None) is req for name in HookContext.__slots__)
    assert not hasattr(ctx, 'request')
    assert not hasattr(ctx, '__dict__')
    with pytest.raises(AttributeError):
        ctx.session = req.session


def test_user_cid_func_id_and_recall():
    ctx = _ctx(_request(recall=True))

    assert ctx.func_id == 'conv2'
    assert ctx.cid == 'conv2__abc'
    assert ctx.recall
    assert not ctx.is_loggedin
    assert ctx.user == 'anon-hash'


def test_default_context_is_empty():
    ctx = HookContext()

    assert not ctx.is_post and not ctx.recall
    assert ctx.cmd == '' and ctx.extra == {}
    assert ctx.var_url_kwargs == {} and ctx.remembered_kwargs == {} and ctx.posted_kwargs == {}
    assert ctx.var_url('x') is None and ctx.remembered('x') is None
    assert ctx.posted('x') is None and ctx.posted_list('x') == []


# conv2 hooks ------------------------------------------------------------------------------------------------------

def _choice_values(schema, field):
    return [value for value, _label in schema[field]['choices']]


def test_conv2_schema_uses_the_posted_quantity_on_submit():
    ctx = HookContext(is_post=True, posted={'quantity': ['M']}, var_url_kwargs={'quantity': 'L'})

    schema = cal_conv.conv2__schema(ctx)

    assert 'amu' in _choice_values(schema, 'from_unit')
    assert 'ft' not in _choice_values(schema, 'from_unit')


def test_conv2_schema_uses_the_url_quantity_on_load():
    schema = cal_conv.conv2__schema(HookContext(var_url_kwargs={'quantity': 'm'}))

    assert 'amu' in _choice_values(schema, 'to_units')


def test_conv2_schema_uses_the_remembered_quantity_when_url_has_none():
    schema = cal_conv.conv2__schema(HookContext(var_url_kwargs={'quantity': '-'}, remembered={'quantity': 'M'}))

    assert 'amu' in _choice_values(schema, 'from_unit')


def test_conv2_url_quantity_wins_over_remembered_quantity():
    schema = cal_conv.conv2__schema(HookContext(var_url_kwargs={'quantity': 'L'}, remembered={'quantity': 'M'}))

    assert 'ft' in _choice_values(schema, 'from_unit')


@pytest.mark.parametrize('quantity', ['', '-', '--', 'zzz'])
def test_conv2_falls_back_to_length_for_missing_or_invalid_quantity(quantity):
    schema = cal_conv.conv2__schema(HookContext(var_url_kwargs={'quantity': quantity}))

    assert 'ft' in _choice_values(schema, 'from_unit')


def test_conv2_dimension_without_units_offers_base_and_secondary_unit():
    schema = cal_conv.conv2__schema(HookContext(var_url_kwargs={'quantity': 'LT'}))

    assert _choice_values(schema, 'from_unit') == ['m*s', 'ft*min']
    assert list(schema['mode']['choices']) == ['u2u']


def test_conv2_input_defaults_are_valid_for_the_quantity():
    assert cal_conv.conv2__input(HookContext(var_url_kwargs={'quantity': 'L'}))['from_unit'] == ['ft']

    inp = cal_conv.conv2__input(HookContext(var_url_kwargs={'quantity': 'LT'}))

    assert inp['from_unit'] == ['m*s']
    assert inp['to_units'] == ['ft*min']
