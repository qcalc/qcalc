# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha
# Tests generated with AI assistance. Reviewed and validated by the author.

from types import SimpleNamespace

import qsett

qsett.init()

import json

import pandas as pd
import pytest

import calc.views_form_data as vfd
from calc.views_form_data import (
    _has_large_dataframe,
    q11426_form_data_qty_unit_fields,
    q11440b_get_saved_io,
    q11441_data_for_function,
    q11442_func_call_by_name,
    q11449_form_data_postprocess_and_run,
    schema_type_initial_class,
)
from qcore import qerror, qinfo, qwarn


# large dataframe guard -------------------------------------------------------------------------------------------

def test_a_dataframe_above_the_limit_is_large_and_one_at_the_limit_is_not():
    df = pd.DataFrame({'a': [1, 2], 'b': [3, 4]})  # 4 cells

    assert _has_large_dataframe({'t': df}, 3)
    assert not _has_large_dataframe({'t': df}, 4)


def test_a_qtbl_dict_counts_its_data_cells():
    table = {'columns': ['a', 'b'], 'data': [[1, 2], [3, 4], [5, 6]]}

    assert _has_large_dataframe({'t': table}, 5)
    assert not _has_large_dataframe({'t': table}, 6)


def test_tables_nested_in_dicts_and_lists_are_found():
    df = pd.DataFrame({'a': range(10)})

    assert _has_large_dataframe({'x': {'y': [1, {'z': df}]}}, 5)
    assert _has_large_dataframe([(1, df)], 5)


def test_data_without_tables_is_never_large():
    assert not _has_large_dataframe({'a': 1, 'b': 'text', 'c': [1, 2, 3], 'd': {}}, 0)


# schema_type_initial_class ---------------------------------------------------------------------------------------

def _info_request(schema):
    return SimpleNamespace(json_doc={'info': {'schema': schema}})


def test_schema_type_initial_and_class_are_read_from_the_info_schema():
    request = _info_request({'x': {'type': 'integer', 'initial': 5, 'attrs': {'class': 'wide'}}})

    assert schema_type_initial_class(request, 'x') == ('integer', 5, 'wide')


def test_schema_entry_without_keys_gives_defaults():
    assert schema_type_initial_class(_info_request({'x': {}}), 'x') == (None, None, '')


def test_a_field_not_in_the_info_schema_gives_defaults():
    assert schema_type_initial_class(_info_request({'x': {'type': 'text'}}), 'y') == (None, None, '')


# quantity unit fields --------------------------------------------------------------------------------------------

def test_unit_fields_of_a_quantity_are_found_by_name():
    schema = [
        {'name': 'mass', 'type': 'float'},
        {'name': 'mass' + vfd.TOK_UOM, 'type': 'uom'},
        {'name': 'mass' + vfd.TOK_INDEX_SEP + '2' + vfd.TOK_PART_UOM, 'type': 'uomx'},
        {'name': 'masses' + vfd.TOK_UOM, 'type': 'uom'},  # | other field that merely starts with the name
        {'name': 'mass_other', 'type': 'text'},
    ]
    request = SimpleNamespace(json_schema=schema)

    names = [f['name'] for f in q11426_form_data_qty_unit_fields(request, 'mass')]

    assert 'mass' + vfd.TOK_UOM in names
    assert 'mass' + vfd.TOK_INDEX_SEP + '2' + vfd.TOK_PART_UOM in names
    assert 'mass_other' not in names
    assert 'mass' not in names


def test_a_field_without_unit_fields_gives_an_empty_list():
    request = SimpleNamespace(json_schema=[{'name': 'a', 'type': 'text'}])

    assert q11426_form_data_qty_unit_fields(request, 'a') == []


# data for function -----------------------------------------------------------------------------------------------

def _d4f_request(data, s2f, schema=None):
    return SimpleNamespace(json_data=data, json_s2f=s2f, json_schema=schema or [{'type': s['type']} for s in s2f])


def test_plain_fields_are_copied_to_the_function_data():
    request = _d4f_request({'a': 1, 'b': 'x'}, [{'type': ''}, {'type': ''}])

    q11441_data_for_function(request)

    assert request.json_d4f == {'a': 1, 'b': 'x'}


def test_a_quantity_is_joined_with_its_unit():
    request = _d4f_request({'mass': 3, 'mass_uom': 'kg'}, [{'type': 'qty', 'parts': 1}, {'type': 'uom'}])

    q11441_data_for_function(request)

    assert request.json_d4f == {'mass': '3 kg'}


def test_a_multi_part_quantity_is_joined_in_all_parts():
    data = {'t': 1, 't_uom': 'hr', 't2': 30, 't2_uom': 'min'}
    s2f = [{'type': 'qty', 'parts': 2}, {'type': 'uom'}, {'type': 'qty'}, {'type': 'uom'}]
    request = _d4f_request(data, s2f)

    q11441_data_for_function(request)

    assert request.json_d4f == {'t': '1 hr, 30 min'}


def test_a_composite_quantity_is_joined_pair_by_pair():
    request = _d4f_request({'q': [1, 'm', 2, 'cm']}, [{'type': 'c'}], schema=[{'type': 'qty'}])

    q11441_data_for_function(request)

    assert request.json_d4f == {'q': '1 m, 2 cm'}


def test_list_items_are_gathered_under_the_list_name():
    sep = vfd.TOK_INDEX_SEP
    data = {'items': 1, f'items{sep}2': 2, f'items{sep}3': 3, 'after': 'x'}
    s2f = [{'type': 'qlist'}, {'type': 'x'}, {'type': 'x'}, {'type': ''}]
    request = _d4f_request(data, s2f)

    q11441_data_for_function(request)

    assert request.json_d4f == {'items': [1, 2, 3], 'after': 'x'}


def test_a_table_json_text_becomes_a_dataframe():
    payload = json.dumps({'columns': ['a', 'b'], 'data': [[1, 2], [3, 4]]})
    request = _d4f_request({'t': payload}, [{'type': 'table'}])

    q11441_data_for_function(request)

    df = request.json_d4f['t']
    assert list(df.columns) == ['a', 'b']
    assert df.values.tolist() == [[1, 2], [3, 4]]


def test_a_dataframe_is_kept_as_it_is():
    df = pd.DataFrame({'a': [1]})
    request = _d4f_request({'t': df}, [{'type': 'table'}])

    q11441_data_for_function(request)

    assert request.json_d4f['t'] is df


@pytest.mark.parametrize('value', ['', 'null', 'None', '  ', 'not json'])
def test_an_empty_or_invalid_table_text_becomes_an_empty_dataframe(value):
    request = _d4f_request({'t': value}, [{'type': 'table'}])

    q11441_data_for_function(request)

    assert request.json_d4f['t'].empty


def test_a_missing_table_stays_none():
    request = _d4f_request({'t': None}, [{'type': 'table'}])

    q11441_data_for_function(request)

    assert request.json_d4f['t'] is None


def test_a_qtbl_stays_a_plain_dict():
    table = {'columns': ['a'], 'data': [[1]]}
    request = _d4f_request({'t': json.dumps(table), 'u': table, 'v': None}, [{'type': 'tbl'}] * 3)

    q11441_data_for_function(request)

    assert request.json_d4f['t'] == table
    assert request.json_d4f['u'] is table
    assert request.json_d4f['v'] is None


@pytest.mark.parametrize('value', ['', 'null', 'bad json', '[1, 2]'])
def test_an_empty_invalid_or_non_dict_qtbl_text_becomes_an_empty_table_dict(value):
    request = _d4f_request({'t': value}, [{'type': 'tbl'}])

    q11441_data_for_function(request)

    assert request.json_d4f['t'] == {'columns': [], 'data': []}


def test_file_fields_are_passed_on_and_unknown_types_are_omitted():
    request = _d4f_request({'f': 'file-obj', 'i': 'img-obj', 'z': 1}, [{'type': 'file'}, {'type': 'image'}, {'type': 'zzz'}])

    q11441_data_for_function(request)

    assert request.json_d4f == {'f': 'file-obj', 'i': 'img-obj'}


# post-processing and run -----------------------------------------------------------------------------------------

class _Form:
    def __init__(self, errors):
        self.errors = errors


def _post_request(cmd='', method='POST', clean=True, data=None, info=None, **extra):
    base_info = {'related': {}, 'xpr': False, 'url': False, 'loop': False}
    base_info.update(info or {})
    request = SimpleNamespace(
        method=method, cmd=cmd, extra={}, success=True, FILES={},
        json_doc={'clean': clean, 'info': base_info},
        json_data={}, json_schema=[], json_d4f={},
        context={'input': {'data': data if data is not None else {}, 'form': None}},
        pref={}, variant=0, token=None, token_state=False, var_owner='', var_title='', times={})
    for key, value in extra.items():
        setattr(request, key, value)
    return request


def test_an_invalid_post_reports_the_form_errors_and_fails():
    request = _post_request(clean=False)
    request.context['input']['form'] = _Form({'a': ['Required'], '__all__': ['Bad combination']})

    result = q11449_form_data_postprocess_and_run(request, 'f')

    assert result.startswith('Error (VLD): Input validation failed: ')
    assert 'a: Required' in result
    assert 'Form: Bad combination' in result
    assert request.success is False


def test_an_invalid_post_without_form_errors_gets_the_generic_message():
    request = _post_request(cmd='run', clean=False)

    result = q11449_form_data_postprocess_and_run(request, 'f')

    assert result == 'Error (VLD): Input validation failed. Please review the highlighted input fields.'
    assert request.success is False


def test_a_get_without_command_does_nothing():
    request = _post_request(method='GET', clean=False)

    assert q11449_form_data_postprocess_and_run(request, 'f') == ''
    assert request.success is True


def test_a_clean_post_without_command_runs_the_function(monkeypatch):
    calls = []

    def fake_call(request, func_id, arg_dict):
        calls.append((func_id, dict(arg_dict)))
        return arg_dict, 'RESULT'

    monkeypatch.setattr(vfd, 'q11442_func_call_by_name', fake_call)
    monkeypatch.setattr(vfd, 'user_name', lambda request: 'tester')
    monkeypatch.setattr(vfd, 'user_ip', lambda request: '127.0.0.1')
    request = _post_request(data={'a': 1})
    request.json_s2f = [{'type': ''}]

    result = q11449_form_data_postprocess_and_run(request, 'f')

    assert result == 'RESULT'
    assert calls == [('f', {'a': 1})]
    assert request.json_doc['fxpr'] == ''
    assert request.success is True


def test_the_related_fields_take_the_cleaned_values():
    request = _post_request(
        cmd='open', data={'a': 5}, info={'related': {'r': {'fields': {'a': None}}}})

    q11449_form_data_postprocess_and_run(request, 'f')

    assert request.json_doc['info']['related']['r']['fields']['a'] == 5


@pytest.mark.parametrize('cmd,text', [
    ('open', 'Input data is entered from file'),
    ('display_var', 'Input data is entered from variant'),
    ('display_xmp', 'Input data is entered from example'),
    ('__modify', 'Input section updated'),
    ('unknown', 'Input section updated'),
])
def test_informational_commands_return_an_info_message(cmd, text):
    request = _post_request(cmd=cmd)

    result = q11449_form_data_postprocess_and_run(request, 'f')

    assert isinstance(result, qinfo)
    assert text in str(result)


def test_modify_returns_the_message_of_the_hook():
    message = qwarn('check the value')
    request = _post_request(cmd='__modify', _modify_message=message)

    assert q11449_form_data_postprocess_and_run(request, 'f') is message


def test_a_reload_trigger_reports_nothing():
    request = _post_request(cmd='__modify')
    request.extra = {'reload': True}

    assert q11449_form_data_postprocess_and_run(request, 'f') == ''


def test_a_post_that_is_not_clean_fails_the_request_even_for_modify():
    request = _post_request(cmd='__modify', clean=False)

    q11449_form_data_postprocess_and_run(request, 'f')

    assert request.success is False


def test_save_input_stores_the_input_for_download(monkeypatch):
    saved = {}
    monkeypatch.setattr(vfd.QSave, 'clear', lambda: saved.clear())
    monkeypatch.setattr(vfd.QSave, 'setp', lambda value: saved.update(value))
    request = _post_request(cmd='save_input', data={'a': 1})
    request.json_data = {'a': 1}
    request.json_s2f = [{'type': ''}]

    result = q11449_form_data_postprocess_and_run(request, 'f')

    assert saved == {'function': 'f', 'input': {'a': 1}}
    assert isinstance(result, qinfo)


def test_command_hook_receives_the_context_and_the_function_kwargs(monkeypatch):
    seen = []

    def hook(ctx, kwargs):
        seen.append((ctx, kwargs))
        return 'DONE'

    monkeypatch.setattr(vfd.QCals, 'func_exists', lambda name: name == 'f__command')
    monkeypatch.setattr(vfd.QCals, 'addr', lambda name: hook)
    request = _post_request(cmd='__command', data={'a': 1}, hook_ctx='CTX')
    request.json_data = {'a': 1}
    request.json_s2f = [{'type': ''}]

    result = q11449_form_data_postprocess_and_run(request, 'f')

    assert result == 'DONE'
    assert seen == [('CTX', {'a': 1})]


def test_a_missing_command_hook_is_an_error(monkeypatch):
    monkeypatch.setattr(vfd.QCals, 'func_exists', lambda name: False)
    request = _post_request(cmd='__command')

    result = q11449_form_data_postprocess_and_run(request, 'f')

    assert isinstance(result, qerror)
    assert 'f__command: not found' in str(result)
    assert request.success is False


def test_an_exception_while_processing_becomes_an_error():
    request = _post_request(cmd='open')
    request.context = {}  # | no 'input' key

    result = q11449_form_data_postprocess_and_run(request, 'f')

    assert isinstance(result, qerror)
    assert 'Error (POSTP)' in str(result)
    assert request.success is False


# function call ---------------------------------------------------------------------------------------------------

def _call_request(memory_allowed=True, remember=True):
    return SimpleNamespace(
        times={}, pref={'memory': 7 if memory_allowed else 0}, success=True, remember=remember,
        json_doc={'info': {'remember': True}})


@pytest.fixture
def func_env(monkeypatch):
    env = SimpleNamespace(executed=[], remembered=[])
    monkeypatch.setattr(vfd, 'q11441b_update_req_pref', lambda request: None)

    def execute(func_id, args, timeout, pref, request):
        env.executed.append((func_id, args, timeout))
        return 'OK'

    monkeypatch.setattr(vfd, 'q0164_execute_qfunc', execute)
    monkeypatch.setattr(vfd.QMem, 'setf', lambda func_id, data: env.remembered.append((func_id, data)))
    return env


def test_the_function_is_executed_with_the_unflattened_arguments(func_env):
    request = _call_request()

    arg_dict, result = q11442_func_call_by_name(request, 'f', {'a': 1, 'b__c': 2})

    assert result == 'OK'
    assert arg_dict == {'a': 1, 'b__c': 2}
    assert func_env.executed[0][0] == 'f'
    assert 'func (ms)' in request.times


def test_the_input_is_remembered_after_a_run(func_env):
    request = _call_request()

    q11442_func_call_by_name(request, 'f', {'a': 1})

    assert func_env.remembered == [('f', {'a': 1})]


def test_the_input_is_not_remembered_when_memory_is_off_or_the_calculator_opts_out(func_env):
    off = _call_request(memory_allowed=False)
    opted_out = _call_request()
    opted_out.json_doc['info']['remember'] = False
    not_asked = _call_request(remember=False)

    for request in (off, opted_out, not_asked):
        q11442_func_call_by_name(request, 'f', {'a': 1})

    assert func_env.remembered == []


@pytest.mark.parametrize('configured,expected', [
    (5000, 900), (0, 1), (-3, 1), ('30', 30), ('bad', 60), (None, 60), (12.7, 12)])
def test_the_execution_timeout_is_clamped_to_a_valid_range(func_env, configured, expected):
    request = _call_request()
    request.pref['execution_timeout'] = configured

    q11442_func_call_by_name(request, 'f', {})

    assert func_env.executed[0][2] == expected


def test_a_failing_function_call_becomes_an_error_result(monkeypatch, func_env):
    def boom(*args, **kwargs):
        raise RuntimeError('boom')

    monkeypatch.setattr(vfd, 'q0164_execute_qfunc', boom)
    request = _call_request()

    arg_dict, result = q11442_func_call_by_name(request, 'f', {'a': 1})

    assert isinstance(result, qerror)
    assert 'Error (FCBN): boom' in str(result)
    assert request.success is False
    assert arg_dict == {'a': 1}


def test_missing_arguments_are_treated_as_empty(func_env):
    request = _call_request()

    arg_dict, result = q11442_func_call_by_name(request, 'f')

    assert arg_dict == {}
    assert result == 'OK'


# saved input -----------------------------------------------------------------------------------------------------

def test_the_saved_input_is_returned_as_json(monkeypatch):
    monkeypatch.setattr(vfd.QSave, 'getp', lambda: {'function': 'f', 'input': {'a': 1}})

    response = q11440b_get_saved_io(None)

    assert json.loads(response.content) == {'function': 'f', 'input': {'a': 1}}
