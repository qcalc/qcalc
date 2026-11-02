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
from qcore import Qty, qt


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
    ctx = HookContext.from_request(request, 'conv2', 'conv2__abc', kwargs.get('var_url_kwargs', {}))
    return ctx.with_resolved(kwargs['resolved']) if 'resolved' in kwargs else ctx


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


def test_posted_as_converts_the_posted_text_to_the_type():
    ctx = _ctx(_request('post', {'n': '5', 'x': '2.5', 'name': 'abc', 'flag': 'on', 'bad': 'abc', 'empty': ''}))

    assert ctx.posted_as('n', int) == 5 and isinstance(ctx.posted_as('n', int), int)
    assert ctx.posted_as('x', float) == 2.5
    assert ctx.posted_as('name', str) == 'abc'
    assert ctx.posted_as('flag', bool) is True
    assert ctx.posted_as('empty', str) == ''


def test_posted_as_gives_the_default_when_not_posted_or_not_convertible():
    ctx = _ctx(_request('post', {'bad': 'abc', 'empty': '', 'decimal': '2.5'}))

    assert ctx.posted_as('missing', float) is None
    assert ctx.posted_as('missing', float, 7.0) == 7.0
    assert ctx.posted_as('bad', float, 1.0) == 1.0
    assert ctx.posted_as('empty', float, 1.0) == 1.0
    assert ctx.posted_as('decimal', int, 3) == 3  # | the text is not an integer, it is not silently rounded
    assert _ctx(_request('get')).posted_as('x', float, 4.0) == 4.0  # | nothing is posted on the first open


def test_posted_as_does_not_change_what_posted_returns():
    ctx = _ctx(_request('post', {'x': '2.5'}))

    ctx.posted_as('x', float)

    assert ctx.posted('x') == '2.5' and ctx.posted_kwargs == {'x': '2.5'}


def test_posted_as_joins_a_quantity_from_its_value_and_unit():
    ctx = _ctx(_request('post', {'mass': '2', 'mass_uom': 'kg', 'empty': '', 'empty_uom': 'kg', 'nounit': '2'}))

    assert ctx.posted_as('mass', qt) == Qty('2 kg')
    assert ctx.posted_as('empty', qt, 'dflt') == 'dflt'  # | no value
    assert ctx.posted_as('nounit', qt, 'dflt') == 'dflt'  # | a value without its unit input is not a quantity
    assert ctx.posted_as('missing', qt, 'dflt') == 'dflt'


def test_posted_as_joins_a_multi_part_quantity():
    ctx = _ctx(_request('post', {'t': '1', 't_part_uom': 'hr', 't__2_part': '30', 't__2_part_uom': 'min'}))

    assert ctx.posted_as('t', qt) == Qty('1 hr, 30 min')


def test_posted_as_gives_the_default_for_a_multi_part_quantity_with_an_empty_part():
    ctx = _ctx(_request('post', {'t': '1', 't_part_uom': 'hr', 't__2_part': '', 't__2_part_uom': 'min'}))

    assert ctx.posted_as('t', qt, 'dflt') == 'dflt'


def test_posted_as_takes_a_quantity_posted_as_one_text():
    assert _ctx(_request('post', {'mass': '2 kg'})).posted_as('mass', qt) == Qty('2 kg')


def test_value_is_the_posted_value_converted():
    ctx = _ctx(_request('post', {'x': '5'}), resolved={'x': '1.5'})

    assert ctx.value('x', float) == 5.0 and isinstance(ctx.value('x', float), float)


def test_value_falls_back_to_the_resolved_value_when_nothing_is_posted():
    ctx = _ctx(_request('get'), resolved={'x': '1.5', 'n': 3, 'mass': '2 kg'})

    assert ctx.value('x', float) == 1.5  # | resolved text is converted
    assert ctx.value('n', int) == 3
    assert ctx.value('mass', qt) == Qty('2 kg')


def test_value_falls_back_to_the_resolved_value_when_the_posted_one_is_not_valid():
    ctx = _ctx(_request('post', {'x': 'abc', 'e': ''}), resolved={'x': '1.5', 'e': '2'})

    assert ctx.value('x', float) == 1.5
    assert ctx.value('e', float) == 2.0


def test_value_returns_a_resolved_value_that_is_not_text_as_it_is():
    table = {'columns': ['a'], 'data': [[1]]}
    quantity = Qty('2 kg')
    ctx = _ctx(_request('get'), resolved={'t': table, 'mass': quantity})

    assert ctx.value('t', dict) is table
    assert ctx.value('mass', qt) is quantity


def test_value_gives_the_default_when_there_is_no_usable_value():
    ctx = _ctx(_request('post', {'bad': 'abc'}), resolved={'bad': '', 'blank': '', 'text': 'abc'})

    assert ctx.value('missing', float) is None
    assert ctx.value('missing', float, 7.0) == 7.0
    assert ctx.value('bad', float, 7.0) == 7.0  # | posted text and resolved '' are both not numbers
    assert ctx.value('blank', float, 7.0) == 7.0
    assert ctx.value('text', float, 7.0) == 7.0


def test_value_joins_a_posted_quantity_and_keeps_the_resolved_one_otherwise():
    posted = _ctx(_request('post', {'mass': '3', 'mass_uom': 'kg'}), resolved={'mass': '2 kg'})
    first_open = _ctx(_request('get'), resolved={'mass': '2 kg'})

    assert posted.value('mass', qt) == Qty('3 kg')
    assert first_open.value('mass', qt) == Qty('2 kg')


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
    ctx = _ctx(_request(), var_url_kwargs={'quantity': 'M'}, resolved={'quantity': 'L', 'from_unit': ['ft']})

    assert ctx.var_url('quantity') == 'M'
    assert ctx.var_url('missing') is None
    assert ctx.var_url('missing', 'dflt') == 'dflt'
    assert ctx.var_url_kwargs == {'quantity': 'M'}
    assert ctx.resolved('quantity') == 'L'
    assert ctx.resolved('from_unit') == ['ft']
    assert ctx.resolved('missing', 'dflt') == 'dflt'
    assert ctx.resolved_kwargs == {'quantity': 'L', 'from_unit': ['ft']}


def test_kwargs_properties_return_copies():
    ctx = _ctx(_request('post', {'quantity': 'M'}), var_url_kwargs={'quantity': 'M'}, resolved={'quantity': 'L'})

    ctx.var_url_kwargs['quantity'] = 'T'
    ctx.resolved_kwargs['quantity'] = 'T'
    ctx.posted_kwargs['quantity'] = 'T'

    assert ctx.var_url('quantity') == 'M'
    assert ctx.resolved('quantity') == 'L'
    assert ctx.posted('quantity') == 'M'


def test_values_that_are_not_text_are_kept():
    marker = object()
    ctx = _ctx(_request(), var_url_kwargs={'items': marker}, resolved={'items': marker})

    assert ctx.var_url('items') is marker
    assert ctx.var_url_kwargs['items'] is marker
    assert ctx.resolved('items') is marker
    assert ctx.resolved_kwargs['items'] is marker


def test_a_resolved_field_without_a_value_is_not_replaced_by_the_default():
    ctx = _ctx(_request(), resolved={'upload_csv': None})

    assert ctx.resolved('upload_csv', 'dflt') is None
    assert ctx.resolved('missing', 'dflt') == 'dflt'


def test_with_resolved_returns_a_copy_and_keeps_everything_else():
    extra = {'cmd': '__modify', 'args': ['a'], 'kwargs': {}}
    req = _request('post', {'quantity': 'M', 'extra': json.dumps(extra)}, recall=True)
    ctx = _ctx(req, var_url_kwargs={'quantity': 'L'}, resolved={'quantity': 'T'})

    other = ctx.with_resolved({'quantity': 'F'})

    assert other is not ctx
    assert ctx.resolved('quantity') == 'T' and other.resolved('quantity') == 'F'
    assert (other.func_id, other.cid, other.user, other.is_post, other.recall, other.cmd) == (
        ctx.func_id, ctx.cid, ctx.user, ctx.is_post, ctx.recall, ctx.cmd)
    assert other.posted_kwargs == ctx.posted_kwargs == {'quantity': 'M'}
    assert other.var_url_kwargs == {'quantity': 'L'}
    assert other.extra == ctx.extra == extra


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
    assert ctx.var_url_kwargs == {} and ctx.resolved_kwargs == {} and ctx.posted_kwargs == {}
    assert ctx.var_url('x') is None and ctx.resolved('x') is None
    assert ctx.posted('x') is None and ctx.posted_list('x') == []


# conv2 hooks ------------------------------------------------------------------------------------------------------

def _choice_values(schema, field):
    return [value for value, _label in schema[field]['choices']]


def test_conv2_schema_uses_the_posted_quantity_on_submit():
    ctx = HookContext(is_post=True, posted={'quantity': ['M']}, resolved={'quantity': 'L'})

    schema = cal_conv.conv2__schema(ctx)

    assert 'amu' in _choice_values(schema, 'from_unit')
    assert 'ft' not in _choice_values(schema, 'from_unit')


def test_conv2_schema_uses_the_resolved_quantity_when_nothing_is_posted():
    schema = cal_conv.conv2__schema(HookContext(resolved={'quantity': 'm'}))

    assert 'amu' in _choice_values(schema, 'to_units')


def test_conv2_schema_uses_the_resolved_quantity_on_a_post_without_a_posted_quantity():
    # | e.g. the quantity is reset by a 'reload' trigger, the form then starts with the resolved value
    schema = cal_conv.conv2__schema(HookContext(is_post=True, posted={'value': ['5']}, resolved={'quantity': 'M'}))

    assert 'amu' in _choice_values(schema, 'from_unit')


@pytest.mark.parametrize('quantity', ['', None, 'zzz'])
def test_conv2_falls_back_to_length_for_missing_or_invalid_quantity(quantity):
    schema = cal_conv.conv2__schema(HookContext(resolved={'quantity': quantity}))

    assert 'ft' in _choice_values(schema, 'from_unit')


def test_conv2_dimension_without_units_offers_base_and_secondary_unit():
    schema = cal_conv.conv2__schema(HookContext(resolved={'quantity': 'LT'}))

    assert _choice_values(schema, 'from_unit') == ['m*s', 'ft*min']
    assert list(schema['mode']['choices']) == ['u2u']


def test_conv2_input_defaults_are_valid_for_the_quantity():
    assert cal_conv.conv2__input(HookContext(resolved={'quantity': 'L'}))['from_unit'] == ['ft']

    inp = cal_conv.conv2__input(HookContext(resolved={'quantity': 'LT'}))

    assert inp['from_unit'] == ['m*s']
    assert inp['to_units'] == ['ft*min']


def test_conv2_short_catalog_lists_only_quantities_with_more_than_two_units():
    full = _choice_values(cal_conv.conv2__schema(HookContext()), 'quantity')
    short = _choice_values(cal_conv.conv2__schema(HookContext(resolved={'catalog': 'short'})), 'quantity')

    assert 'LT' in full and 'LT' not in short
    assert 0 < len(short) < len(full)
    assert all(len(cal_conv.lmt2ulist(q)) > 2 for q in short)


def test_conv2_short_catalog_has_only_the_unit_to_unit_mode():
    schema = cal_conv.conv2__schema(HookContext(resolved={'catalog': 'short'}))

    assert list(schema['mode']['choices']) == ['u2u']
    assert len(cal_conv.conv2__schema(HookContext())['mode']['choices']) == 4


def test_conv2_short_catalog_falls_back_to_length_for_a_quantity_not_in_the_catalog():
    ctx = HookContext(resolved={'catalog': 'short', 'quantity': 'LT'})

    assert 'ft' in _choice_values(cal_conv.conv2__schema(ctx), 'from_unit')


def test_conv2_posted_catalog_wins_over_the_resolved_catalog():
    ctx = HookContext(is_post=True, posted={'catalog': ['full']}, resolved={'catalog': 'short', 'quantity': 'LT'})

    assert 'm*s' in _choice_values(cal_conv.conv2__schema(ctx), 'from_unit')


def test_conv2_short_catalog_converts_unit_to_unit_whatever_the_mode():
    result = cal_conv.conv2(catalog='short', mode='q2q', value='1', from_unit=['ft'], to_units=['inch'])

    assert 'ft' in str(result['Converting from'])


def test_conv2_short_catalog_ignores_the_unit_cost():
    result = cal_conv.conv2(catalog='short', value='2', from_unit=['ft'], to_units=['inch'], unit_cost='5 USD/ft')

    assert 'Total Cost' not in result


def test_conv2_omits_the_total_cost_without_a_unit_cost():
    result = cal_conv.conv2(value='2', from_unit=['ft'], to_units=['inch'])

    assert 'Total Cost' not in result
