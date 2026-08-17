# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

from calc import QMem, QPref, QCache, QKeep, QSave, QInput
from .mod_cutil import *
from qutil import HtmxHttpRequest, to_df, user_name, is_loggedin
from qcore import qhidex, qtable, qtbl, QFile, qlist_types, QFieldHandler, QEncoderBase, QJField, convert_to_type
import json
from .mod_mfunc import *
import pandas as pd
from qvars import qc_gpref as gs
from django.forms import forms
from django.http import JsonResponse
import time
import logging

logger = logging.getLogger(__name__)


def q11429_func_to_form_schema(request: HtmxHttpRequest, func_addr, func_id, cid, kwargs):  # req
    cache_def = QCache.get_data(func_id) if gs['schema_cache'] else None

    if cache_def is None:
        __info = kwargs.get('__info', None)  # | __info from url path, used to call func__info(__info)
        fargs, fanns, finfs = func_meta(func_addr, func_id, __info)
        cache_def = {'fargs': fargs, 'fanns': fanns, 'finfs': finfs}
        if __info is None:  # | __info means some form elements data are dynamically populated e.g. choices
            if gs['schema_cache']:
                QCache.set_data(func_id, cache_def)  # | save only if form elements data are static
                if 'upload_image' in fargs:
                    assert fargs['upload_image'] is None
    else:
        fargs = cache_def['fargs']
        fanns = cache_def['fanns']
        finfs = cache_def['finfs']
        if 'upload_image' in fargs:
            assert fargs['upload_image'] is None

    # | start callback point __input (q11429, view_form_data.py, line 37)
    # | func__input(request, func url parameters)
    # | modify initial input values
    if QCals.func_exists(func_id + '__input'):
        fn = QCals.addr(func_id + '__input')
        defa_input = fn(kwargs)
        # kwargs.update(defa_input) @ 10.09.24 commented
        if defa_input:  # | precedence: 1. __info < 2 .json (q1141_read_func_meta) < 3. __input
            fargs.update(defa_input)
    # | end exit point

    if request.recall and QPref.getp1('memory') > 0:  # | recall and request is not None
        prev_input = QMem.getf(func_id)  # | get from memory, user's previous input
        if prev_input:  # | precedence: 1. __info < 2 .json < 3. __input < 4. memory
            fargs.update(prev_input)

    for key in COMBINE_FINF:
        if key in finfs:
            if key in request.json_doc['info']:
                if isinstance(request.json_doc['info'][key], dict):
                    request.json_doc['info'][key].update(finfs[key])
                else:
                    request.json_doc['info'][key] = finfs[key]
            else:
                request.json_doc['info'][key] = finfs[key]

    # print(fargs, fanns, finfs,request.json_doc['info'])
    request.json_schema = []  # schema for form
    request.json_data = {}  # data for form
    request.json_s2f = []  # schema to function

    q11421_get_extra_form_data_posted(request)

    id_prefix = 'id_' + cid + '_'
    i = 0  # | field, can be greater than arguement
    iarg = 0  # | arguement
    for arg_name, arg_value in fargs.items():
        # | arg_name by default has the default value
        # | name = arg_name
        # | --------------------------------------------
        # | static initial value or initial empty value
        if arg_name in kwargs:  # | precedence: 1. __info < 2 .json < 3. __input < 4. memory < 5. kwargs < 6. url args
            v = kwargs[arg_name]
            if isinstance(v, str):
                # | value is specified in url so assign it instead of default arg value
                if v == '-':
                    # | value is - so keep the default arg value
                    pass
                elif v == '--':
                    # | value is -- so assign empty value
                    arg_value = ''
                else:  # | specified value
                    arg_value = v
            else:
                arg_value = v
        elif '---' in kwargs:
            # | if a key is --- in url, assign empty value instead of default arg value
            arg_value = ''
        # | --------------------------------------------
        # sig_type = params[iarg].annotation
        if arg_name.endswith('--@'):
            sig_type = qfunc  # | qhide w/o s2f='x' dont ignore - has to run func()
        elif arg_name.endswith('--#'):
            sig_type = qhidex  # | qhide but s2f='x' ignore
        else:
            sig_type = fanns.get(arg_name, '')
        # | --------------------------------------------
        arg_value = q11422_form_data_modify_after_post(
            request, func_id, sig_type, arg_name, arg_value)
        # | assign type to determine the behavior
        inf_type, inf_initial, inf_class = schema_type_initial_class(request, arg_name)
        # | __info/initial gets less precedence
        # | precedence: 1. __info < 2 .json < 3. __input < 4. memory < 5. kwargs < 6. url args < 7. posted value
        arg_type = sig_type if sig_type else inf_type
        arg_value = arg_value if arg_value is not None else inf_initial
        if arg_type in [qtable, 'qtable', qtbl, 'qtbl']:
            if request.cmd == 'edit':
                inf_class = 'table-in'
            elif request.cmd == 'display':
                inf_class = 'table-out'
        parent_index = i
        qjf = QJField(arg_name, arg_type, arg_value, id_prefix, False, inf_class)
        if qjf.s2f['type'] != 'c':  # not composite field
            request.json_schema.append(qjf.jf)
            request.json_s2f.append(qjf.s2f)
            request.json_c4f.update(qjf.c4f)
            request.json_doc['info'].update(qjf.doc_info)
            request.json_data[qjf.name] = request.json_schema[i]['initial']  # same as qjf.jf['initial']
            for qjf in qjf.jf_ex:
                i += 1
                request.json_schema.append(qjf.jf)
                request.json_s2f.append(qjf.s2f)
                request.json_doc['info'].update(qjf.doc_info)
                request.json_data[qjf.name] = request.json_schema[i]['initial']
        else:
            qjc = {}
            request.json_schema.append(qjf.jf)
            request.json_s2f.append(qjf.s2f)
            request.json_c4f.update(qjf.c4f)
            request.json_doc['info'].update(qjf.doc_info)
            request.json_data[qjf.name] = qjf.jf['initial']
            for qjf in qjf.jf_ex:
                qjc[qjf.name] = qjf.jf
            request.json_schema[parent_index]['comp'] = qjc

        if arg_name in request.json_doc['info']['schema']:
            for key in request.json_doc['info']['schema'][arg_name]:
                if key not in ['attrs', 'type', 'initial']:
                    request.json_schema[parent_index][key] = request.json_doc['info']['schema'][arg_name][key]
                elif key == 'attrs':
                    for attr in request.json_doc['info']['schema'][arg_name]['attrs']:
                        if attr != 'class':  # class already handled
                            request.json_schema[parent_index]['attrs'][attr] = \
                                request.json_doc['info']['schema'][arg_name]['attrs'][attr]
                # | else:
                # |    # 'type' and 'initial' are already considered
                # |    pass

        # related - initial values
        for key in request.json_doc['info']['related']:
            rdata = request.json_doc['info']['related'][key]
            if 'fields' in rdata:
                if arg_name in rdata['fields']:
                    request.json_schema[parent_index]['type'] = 'rchoice'
                    rdata['fields'][arg_name] = request.json_data[arg_name]

        i += 1  # field
        iarg += 1  # argument
    return


def q11422_form_data_modify_after_post(request, func_id, sig_type, arg_name, arg_value):
    if request.method == 'POST':
        # | process qlist fields data into an array
        # | number of list items will determine number of fields required
        if sig_type in qlist_types and request.cmd not in ['load']:
            # | not loading list from json input file
            new_arg_value = []
            for arg in request.POST.keys():
                if arg.startswith(arg_name + '_') or arg == arg_name:
                    new_arg_value.append(request.POST.get(arg))
            arg_value = new_arg_value
            if func_id == 'collect':
                QKeep.setp1('count', len(arg_value))
        elif sig_type in (qtable, qtbl) and request.cmd == 'load' and arg_name == request.extra.get('to', ''):
            # | loading table from csv file
            from_fld = request.extra['from']
            delimiter_fld = request.extra.get('delimiter', 'delimeter')
            quoting_fld = request.extra.get('quoting', 'quoting')
            url_fld = request.extra.get('url', 'url')
            delimiter = request.POST.get(delimiter_fld, ',')
            quoting = request.POST.get(quoting_fld, '1')
            url = request.POST.get(url_fld, ',')
            if request.FILES and from_fld in request.FILES:
                fdata = request.FILES[from_fld]
                qf = QFile(from_fld, fdata)
                df = to_df(qf.txt_buf(), delimiter, quoting)
            elif url:
                df = to_df(url, delimiter, quoting)
            else:
                df = None
            if df is not None:
                # | qtbl never receives the DataFrame itself, only plain column/data
                arg_value = df if sig_type == qtable else {'columns': df.columns.tolist(), 'data': df.values.tolist()}
        elif request.cmd == '__modify' and (
            arg_name in request.extra.get('args', []) or arg_name in request.extra.get('kwargs', {})):
            # | start callback point __modify (q11422, view_form_data.py, line 197)
            # | func__modify(request, argname, argvalue, action), request.POST[] available
            # | modify input value of a specific arguement after posting
            cfunc = func_id + '__modify'
            if QCals.func_exists(cfunc):
                modify_callback = QCals.addr(cfunc)
                new_arg_value = convert_to_type(request.POST.get(arg_name), sig_type)
                action = request.extra.get('kwargs', {}).get(arg_name, '')
                try:
                    arg_value = modify_callback(arg_name, new_arg_value, action)
                except Exception as e:
                    logger.exception(f"Exception occurred: {e}")
                    arg_value = new_arg_value
                    # | end exit point
    # return modified arg_value
    return arg_value


def q11421_get_extra_form_data_posted(request):
    if not request.POST:
        return
    extra = json.loads(request.POST.get('extra'))
    if not extra:
        request.cmd = ''
        request.extra = {}
    else:
        request.cmd = extra.get('cmd', '').lower()
        request.extra = extra
        request.POST._mutable = True
        request.POST['extra'] = ""  # reset the extras
    return


def q11440b_get_saved_io(_request):
    result = QSave.getp()  # Saving: STEP 2 of 2 (return json_d4f to javascript)
    return JsonResponse(result, encoder=QEncoderBase)


def q11449_form_data_postprocess_and_run(request, func_id):  # cid
    result = ''
    if ((request.method == 'POST' and request.json_doc['clean']) or
        request.cmd in ['run', 'save_io',
                        'save_input', 'save_var', 'create_var', 'display_var', 'display_xmp']):
        try:
            # replace json_data with cleaned data
            request.json_data = request.context['input']['data']

            # related - update values from input
            for key in request.json_doc['info']['related']:
                rdata = request.json_doc['info']['related'][key]
                for name in rdata['fields']:
                    rdata['fields'][name] = request.json_data[name]

            # at this point context data and json_data both are same cleaned data
            if request.FILES:
                for ffld, fdata in request.FILES.items():
                    request.json_data[ffld] = QFile(ffld, fdata)

            if request.cmd in ['', 'run', 'save_io']:  # | POST: Usually excute the function and calculate
                q11441_data_for_function(request)
                # ic('before', request.json_d4f)
                arg_dict, result = q11442_func_call_by_name(request, func_id, request.json_d4f)
                json_data_type = {fld['name']: fld['type'] for fld in request.json_schema}
                # print('json_data_type', json_data_type)
                if request.cmd in ['', 'run']:
                    if request.json_doc['info']['xpr']:
                        request.json_doc['fxpr'] = fxpr_from_json(func_id, request.json_d4f, json_data_type)
                    if request.json_doc['info']['url']:
                        request.json_doc['furl'] = furl_from_json(func_id, request.json_d4f, json_data_type)
                    if request.json_doc['info']['loop']:
                        request.json_doc['floop'] = floop_from_json(func_id, request.json_d4f, json_data_type)
                    logger.note("CAL: Calculate clicked | user=%s | func=%s", user_name(request), func_id)
            elif request.cmd == 'save_input':
                # | POST/GET: Save input
                q11441_data_for_function(request)
                QSave.clear()
                QSave.setp({'function': func_id, 'input': request.json_d4f})
                # | Saving: STEP 1 of 2 (save json_d4f to server)
                result = 'Input data can be saved to file'
            elif request.cmd in ['save_var', 'create_var']:
                # | POST/GET: Save input in DB
                q11441_data_for_function(request)
                # | Saving: STEP 1 of 2 (save json_d4f to server)
                json = {'function': func_id, 'input': request.json_d4f, 'description': request.var_title}
                # | if current variant is owned by the current user then save to same variant
                # | else create a new variant even if cmd is 'save_var'
                cur_user_name = user_name(request)
                var_id = request.variant if request.cmd == 'save_var' and cur_user_name == request.var_owner else 0
                if is_loggedin(request) and request.token and cur_user_name != request.var_owner:
                    if not request.token_state:
                        QInput.save_shared_cal(func_id, request.token, check_only=False)
                request.variant = QInput.set_variant(func_id, var_id, json)
                result = (f"Input variant #{request.variant} is "
                          f"{'saved' if var_id > 0 else 'created, click on [Display variants] to refresh the list'}")
            elif request.cmd == 'open':
                # | POST: data from file
                result = 'Input data is entered from file'
            elif request.cmd == 'display_var':
                # | GET: data from variant
                result = 'Input data is entered from variant'
            elif request.cmd == 'display_xmp':
                # | GET: data from example
                result = 'Input data is entered from example'
            elif request.cmd == '__command':
                # | start callback point __command (q11449, view_form_data.py, line 279)
                # | func__command(request, fkwargs, extra:dict), request.POST[] available
                # | perform action or validate input values after posting
                cfunc = func_id + '__command'
                if QCals.func_exists(cfunc):
                    command_callback = QCals.addr(cfunc)
                    q11441_data_for_function(request)
                    arg_dict2run = request.json_d4f.copy()
                    unflat_args = q0162_dictify_fargs(arg_dict2run)
                    result = command_callback(unflat_args, request.extra)
                else:
                    result = f'{cfunc}: not found'
                    request.success &= False
            else:
                # | POST: Update input section
                result = f'{request.cmd.upper().replace('__', '')}: Input section updated'

            if request.method == 'POST':
                request.success &= request.json_doc['clean']
        except Exception as e:
            request.success &= False
            result = f'Error (POSTP): {e}'
    else:  # | GET and no cmd
        pass
    return result


def q11469_form_data_create_dynaform_and_fill(request, json_schema, json_data, json_s2f, json_doc, cid, mode=0):
    # | Generate html form for the created "DynaForm" from json_schema
    # | mode 0=input,1=output
    sname = json_doc['name']
    post_data = request.POST.dict() if request.method == 'POST' and mode == 0 else {}
    # print('json_schema, cid, json_data', json_schema, cid, json_data)
    form_class = q11461_create_dynaform_class(sname, json_schema, cid, json_s2f, post_data)
    form_class.required_css_class = 'required'
    data = json_data
    form = None
    if request.method == 'POST' and request.cmd not in ['load', '__modify']:
        # ['', 'resize', 'display', 'edit', 'save']:
        if mode == 0:  # post, input
            form = form_class(request.POST)
            if form.is_valid():
                data = form.cleaned_data
                json_doc['clean'] = True
                # ic(json_data, data, request.POST.dict())
            else:  # deb@13.09.23
                # | calculation will continue with previous cleaned data
                json_doc['clean'] = False
        elif mode == 1:  # post, output
            form = form_class(data)
    elif request.method == 'POST' and request.cmd in ['load', '__modify']:
        form = form_class(data)
    else:  # get, input
        form = form_class(data)
    # # print(form)
    context = {
        'data': data,
        'form': form,
        'doc': json_doc,
        'cid': cid,
        'extra': {},  # json.dumps(extra)
    }
    return context


def q11461_create_dynaform_class(sname, json_schema, cid, json_s2f, post_data):
    # | Create "DynaForm" from database stored json_schema
    fh = QFieldHandler(sname, json_schema, cid, json_s2f, post_data)
    return type('DynaForm', (forms.Form,), fh.formfields)


def schema_type_initial_class(request, arg_name):
    type_ = None
    initial = None
    class_ = ''
    if arg_name in request.json_doc['info']['schema']:
        type_ = request.json_doc['info']['schema'][arg_name].get('type', None)
        initial = request.json_doc['info']['schema'][arg_name].get('initial', None)
        class_ = request.json_doc['info']['schema'][arg_name].get('attrs', {}).get('class', '')
    return type_, initial, class_


def q11441_data_for_function(request: HtmxHttpRequest):  # , kwargs):
    """
    Prepare function kwargs from json_data() dict of field values
    In particular it combines data from qty and unit from single and multilevel
    quanity fields to form function parameter value
    """
    request.json_d4f = {}
    json_data_list = [(key, value) for key, value in request.json_data.items()]
    # print('json_data_list', json_data_list)
    i = 0

    while i < len(json_data_list):
        name = json_data_list[i][0]
        # print(name, request.json_s2f[i]['type'])
        value = json_data_list[i][1]  # take default value
        if request.json_s2f[i]['type'] == '':
            request.json_d4f[name] = value
        elif request.json_s2f[i]['type'] == 'qlist':
            arr = [value]
            fname = name
            for name, value in json_data_list:
                if name.startswith(fname + '_'):
                    i += 1
                    arr.append(value)
            request.json_d4f[fname] = arr
        elif request.json_s2f[i]['type'] == 'table':
            # print('value', value)
            if value is not None:
                if isinstance(value, pd.DataFrame):
                    request.json_d4f[name] = value
                else:
                    value = json.loads(value)
                    # print('d4f value', value['data'], value['columns'])
                    request.json_d4f[name] = pd.DataFrame(data=value['data'], columns=value['columns'])
            else:
                request.json_d4f[name] = None
        elif request.json_s2f[i]['type'] == 'tbl':
            # | qtbl: keep as plain dict, never build a DataFrame
            if value is not None:
                request.json_d4f[name] = value if isinstance(value, dict) else json.loads(value)
            else:
                request.json_d4f[name] = None
        elif request.json_s2f[i]['type'] == 'c' and request.json_schema[i]['type'] == 'qty':
            ln = len(value)
            parts = []
            for j in range(0, ln, 2):
                parts.append(f"{value[j]} {value[j + 1]}")
            request.json_d4f[name] = ', '.join(parts)
        elif request.json_s2f[i]['type'] == 'qty' and request.json_s2f[i]['parts'] == 1:
            value = str(value) + ' ' + json_data_list[i + 1][1]
            request.json_d4f[name] = str(value)
            i += 1
        elif request.json_s2f[i]['type'] == 'qty' and request.json_s2f[i]['parts'] > 1:  # multi part qty, e.g. hr min s
            skip_to = i + request.json_s2f[i]['parts'] * 2 - 1
            # print('data_list_i',i,json_data_list[i])
            strq = f'{json_data_list[i][1]} {json_data_list[i + 1][1]}'
            for j in range(i + 2, skip_to + 1, 2):
                strq += f', {json_data_list[j][1]} {json_data_list[j + 1][1]}'
            request.json_d4f[name] = strq  # str(valq)
            i = skip_to
        elif request.json_s2f[i]['type'] in ['file', 'image']:
            # get_file(request, sfunc, name, value)
            request.json_d4f[name] = value
            # print('type-file', value)
        else:  # x ommit
            pass
        i += 1
    # print(json_d4f)
    return


def q11441a_get_user_pref(request: HtmxHttpRequest):
    # | import user preferences into the current request
    us = QPref.getp().copy()  # User Session Preference, Defaults for the user
    request.pref.update(us)  # User Request Preference, Defaults for this request of the user
    # print('user pref', request.pref)


def q11441b_update_req_pref(request: HtmxHttpRequest):
    # | update current request preferences with user's request specific values posted
    us = request.pref  # QPref.getp(request).copy()
    us_idec = us['ignore_decimal_format']
    xt_idec = request.extra.get('ignoredec', '')  # '0', '1' or ''
    ca_idec = us_idec if xt_idec == '' else (xt_idec == '1')
    us['ignore_decimal_format'] = ca_idec
    request.pref.update(us)  # User Request Preference, Defaults for this request of the user


def q11442_func_call_by_name(request: HtmxHttpRequest, func_id, arg_dict=None):  # req
    request.times['execution mode'] = gs['execution_mode']
    request.times['func starts'] = time.time()
    if arg_dict is None:
        arg_dict = {}
    # arg_dict = kwargs
    # | https://yizhiyue.me/2022/03/27/call-functions-with-dynamic-parameters-in-python
    # | check if first argument is a request or not
    arg_dict2run = arg_dict.copy()
    if len(arg_dict) > 0:
        rky = list(arg_dict.keys())[0]
        req = list(arg_dict.values())[0]
        if isinstance(req, str) and req == '__req__':
            arg_dict2run[rky] = request

    try:
        unflat_args = q0162_dictify_fargs(arg_dict2run)
        # *******
        q11441b_update_req_pref(request)
        # QPref.getp(request) is Session Pref
        pref = request.pref  # Request Pref
        # *******
        # timeout1 = QThread.get_pref('execution_timeout', 60)
        timeout = pref.get('execution_timeout', 60)
        try:
            timeout = float(timeout)
        except (TypeError, ValueError):
            timeout = 60
        timeout = min(900, max(1, int(timeout)))
        # print('1', timeout1, type(timeout1), '2', timeout, type(timeout))
        result = q0164_execute_qfunc(func_id, unflat_args, timeout=timeout, pref=pref, request=request)
        if request.remember and pref.get('memory', 7) > 0:
            QMem.setf(func_id, arg_dict)  # save to memory
    except Exception as e:
        request.success &= False
        result = f'Error (FCBN): {e}'
    request.times['func (ms)'] = int((time.time() - request.times['func starts']) * 1000)
    return arg_dict, result  # better deb@17.10.2023
