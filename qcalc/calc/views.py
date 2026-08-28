# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

import qvars
from qcore import layrow, laycol, qformat, df_formatter, QChart, QMap, QImage, qjson_dumps
from calc import QTemp, QList, QIO, QFav
from django.shortcuts import render
from django.http import HttpResponse
from django.utils.safestring import mark_safe
import catalog.views
from qvars import qfunc_dict_template
from qcore.mod_anno import *
from .mod_ucals import get_uc_list
from .view_form_data import *
from qutil import HtmxHttpRequest, QThread, preprocess_expression, QDateTime, fid2owner
import qutil as ut
import json
from datetime import date, datetime, time as dt_time
import pandas as pd
from qcore import isMeasureQuantity as isPQ
from django.conf import settings
import markdown
import qconst
import logging

logger = logging.getLogger(__name__)


def clear_calcs(request: HtmxHttpRequest):
    template = 'clear.html'
    return render(request, template, {})


def q1119_urlpath_to_func_args(request, dictf):
    kwargs = {}
    sfunc = ''
    if 'fname' in dictf:
        request.recall = True
        request.remember = True
        sfunc = dictf['fname']
    elif 'path' in dictf:
        request.recall = False
        request.remember = True
        spath = dictf['path']
        sfunc = spath.split('/')[0]
        sargs = spath.replace(sfunc + '/', '', 1)
        kwargs = ut.key_val(sargs)

    skip_precheck = False
    if 'fargs' in dictf:
        request.recall = False
        request.remember = True
        request.cmd = 'load'
        skip_precheck = True
        kwargs = dictf['fargs']

    if 'cmd' in dictf:
        request.cmd = dictf['cmd']

    if not q1129_is_func_authorised(request, sfunc):
        raise Exception(f'Error (FTFC): Function ({sfunc}) can be run by an Authorised user only.')

    faddr = QCals.addr(sfunc)
    if not faddr:
        raise Exception(f'Error (FTFC): Function ({sfunc}) not found or you may not be authorised to run the function.')
    params = inspect.signature(faddr).parameters
    fargs = list(params)
    # print('fargs', fargs)
    if '__info' in fargs:
        request.recall = False
        request.remember = False
        if '__info' not in kwargs:
            if request.method == 'GET':
                kwargs['__info'] = params['__info'].default
                # print("GET kwargs['__info']", kwargs['__info'])
            else:
                kwargs['__info'] = request.POST.get('__info')
                # print("POST kwargs['__info']", kwargs['__info'])

    # check if any value need to be erased e.g circle()
    if skip_precheck:
        return sfunc, kwargs

    for key in kwargs:
        kwargs[key] = preprocess_expression(kwargs[key].strip(), disp=True)
    return sfunc, kwargs


def fill_input_data(request, **kwargs):  # not required, not used
    # /scope/fname/varid
    scope = kwargs.get('scope', 'variants')  # | 'variants', 'examples'
    fname = kwargs.get('fname', '')
    variant_id = int(kwargs.get('varid', '0'))
    cal_id, cal_name, cal_owner = fid2owner(fname)
    var_owner = request.user.username if scope == 'variants' else cal_owner
    var_record = QInput.get_variant(fname, variant_id, var_owner)
    fargs = var_record.item['input']
    if scope == 'variants':
        cmd = 'display_var'
        return q1999_func_to_form(request, fargs=fargs, fname=fname, part="1", variant=variant_id, cmd=cmd)
    else:
        cmd = 'display_xmp'
        return q1999_func_to_form(request, fargs=fargs, fname=fname, part="1", example=variant_id, cmd=cmd)


def q1999_func_to_form(request: HtmxHttpRequest, **dictf):  # main view
    def get_template(part):
        return {
            '0': 'gen-calculator.html',
            '1': 'gen-calculator-partial.html',
            '2': 'insert-calculator-form-partial.html'
        }.get(part, 'gen-calculator-partial.html')

    part = '1'
    if request.method == 'GET':
        # | add cal ('1'), browser url ('0'), variant ('2')
        part = request.GET.get('part', dictf.get('part', '0'))
    elif request.method == 'POST':
        # | calculate button ('2'), open json file ('1'), command button ?part=('1'/'2')
        part = request.GET.get('part', dictf.get('part', '2'))

    try:
        q1199_func_to_form_common(request, **dictf)
        return q1_render(request, get_template(part), request.context)
    except Exception as e:
        return q1_render_status(request, str(e), part)


def q1_func_to_form_core(request: HtmxHttpRequest, **dictf):  # main view
    request.recall = False
    request.remember = False
    template = 'gen-calculator-core.html'
    try:
        q1199_func_to_form_common(request, **dictf)
        return q1_render(request, template, request.context)
    except Exception as e:
        return q1_render_status(request, str(e))


def q1129_is_func_authorised(request: HtmxHttpRequest, sfunc):
    node = QCals.calc_root.get_node_by_id(sfunc)
    if sfunc in QCals.qc_user_list:
        return True
    elif node and node.flags != '':
        return node.is_visible(request)
    elif sfunc in get_uc_list():
        return True
    elif request.token:
        return True
    else:
        return True


def q1199_func_to_form_common(request: HtmxHttpRequest, **dictf):  # main view
    ut.q1139_request_init(request)

    cid = ''
    input_id: int = 0
    var_owner = ''
    variant: int = 0
    token = ''
    execute = None
    example = 0
    if request.method == 'GET':
        cid = request.GET.get('cid')
        token = request.GET.get('token', '')
        if token == '': example = int(request.GET.get('example', 0))
        if example == 0:
            variant = int(request.GET.get('variant', dictf.get('variant', 0)))
            var_owner = request.GET.get('var_owner', dictf.get('var_owner', user_name(request)))
        else:
            variant = example
            var_owner = '?'  # wait to determine

        execute = request.GET.get('run')
    elif request.method == 'POST':
        cid = request.POST.get('cid')
        input_id = int(request.POST.get('input_id', 0))
        var_info = QInput.get_var_info(input_id)
        var_owner = var_info.user.username if var_info else qvars.super_user.username
        variant = var_info.variant_id if var_info else 0
        token = var_info.access_token if var_info else ''

    variant = int(variant)
    request.variant = variant
    request.token = token  # required to check authorization inside q1119_urlpath_to_func_args()
    if execute is not None: request.cmd = 'run'

    sfunc, kwargs = q1119_urlpath_to_func_args(request, dictf)

    if token == '' and var_owner == '?':  # determine var_owner now
        if '-' in sfunc:
            var_owner = sfunc.split('-')[-1]
        else:
            var_owner = qvars.super_user.username

    request.var_owner = var_owner

    if cid == '' or cid is None: cid = sfunc + '__' + ut.makeid()
    request.cid = cid

    if request.method == 'GET':
        # | get kwargs from variant/token
        inp_data = None
        if token:  # shared by token
            inp_data = QInput.get_variant_from_token(sfunc, token)
            if inp_data:
                variant = inp_data.variant_id
                request.variant = variant
                var_owner = inp_data.user.username
                request.var_owner = var_owner

                checked = QInput.save_shared_cal(sfunc, token, check_only=True)
                request.token_state = (checked != "0")
        elif variant > 0:  # user variant
            inp_data = QInput.get_variant(sfunc, variant, var_owner)
        elif variant == 0:
            cal_id, cal_name, cal_owner = fid2owner(sfunc)
            cur_user_name = user_name(request)
            if cal_owner and cal_owner != cur_user_name:
                request.token_state = QInput.is_shared_cal(sfunc)

        if inp_data:  # shared input
            inp_kwargs = inp_data.item.get('input', {})
            inp_kwargs.update(kwargs)  # inp_kwargs can be overwritten by kwargs
            kwargs = inp_kwargs
            request.var_title = inp_data.description
            input_id = inp_data.id
        elif token:
            request.success &= False
            raise Exception(f"Error (FTFC) Incorrect Access Token for {sfunc}")
        elif variant > 0:
            request.success &= False
            raise Exception(f"Error (FTFC) Incorrect Variant ({variant}) or Variant Owner {var_owner}")

    request.input_id = input_id
    q11441a_get_user_pref(request)
    request.times['common starts'] = time.time()

    try:
        q1149_func_to_form_context(request, sfunc, cid, kwargs)
    except Exception as e:
        request.success &= False
        e.args = (f"Error (FTFC) {str(e)}",)
        raise e

    request.times['common (ms)'] = int((time.time() - request.times['common starts']) * 1000)
    return


def calc_io(_request: HtmxHttpRequest):
    io_dict = QIO.getp()
    return JsonResponse(io_dict, encoder=QEncoderBase)


def q1_step2(request: HtmxHttpRequest):
    fstep = request.GET.get('step', "").strip().lower()  # run, cost, chart
    fname = request.GET.get('func', "").strip().lower()  # run function name
    # | fcaption = request.GET.get('caption', "").strip().lower() # used in template
    fcid = request.GET.get('src_cid', "").strip()  # source cid may not have been used, collected from html
    fspec = json.loads(request.GET.get('spec', {}))  # spec
    # | print(type(fspec), fspec) # spec can be: 'include, 'exclude', 'field', dict of arg:field
    output = QIO.getp1(fcid, {}).get('output', {})

    if fstep == 'run':
        ff = QCals.quick_find_func(fname)
        input_ = QIO.getp1(fcid, {}).get('input', {})
        io = {**input_, **output}
        fargs = {}
        for arg in fspec:
            if fspec[arg] in io:
                v = io[fspec[arg]]
                fargs[arg] = v
        return q1999_func_to_form(request, fname=ff, fargs=fargs, part='1')

    if output:
        # include and exclude
        if 'include' in fspec:
            if '*' not in fspec['include']:
                # | keys = output.keys() # won't work,
                # | because output size will be changed, and it is a ref
                keys = [key for key in output.keys() if key not in fspec['include']]
                for key in keys:
                    _ = output.pop(key)
        if 'exclude' in fspec:
            keys = [key for key in output.keys() if key in fspec['exclude']]
            for key in keys:
                _ = output.pop(key)

        if fstep == 'cost':
            ff = 'cost'
            # not_cqkeys = []  # | cq = qty having cost
            keys = [key for key in output.keys()]
            for key in keys:
                if not isinstance(output[key], Qty):
                    _ = output.pop(key)
                else:
                    dim = output[key].unit.dimension
                    if 'C' in dim:
                        _ = output.pop(key)

            user_curnc = QThread.get_pref('defa_currency', 'USD')
            if output:
                ucost = ['1.00 ' + user_curnc + '/' + q.uom for q in output.values()]
                df = pd.DataFrame({'Item': output.keys(), 'Quantity': output.values(), 'Unit Cost': ucost})
                return q1999_func_to_form(request, fname=ff, fargs={'items': df}, part='1')
            else:
                msg = f'No suitable Qty found to calculate cost'
        elif fstep == 'chart':
            key = fspec['field']
            if key in output:
                if isinstance(output[key], QChart):
                    return q1999_func_to_form(request, fname=output[key].chtype, fargs=output[key].data, part='1')
            msg = f'No data found for Chart'
        else:
            msg = f'Unknown step2 step [{fstep}]'
    else:
        msg = f'Output not found, please recalculate'

    return ut.show_modal(request, "Next Step", f'Error (S2): {msg}')


def dump(_request: HtmxHttpRequest):
    return JsonResponse(qvars.last_dump, safe=False, encoder=QEncoderBase)


def mems(_request: HtmxHttpRequest):
    return JsonResponse(QMem.getp(), encoder=QEncoderBase)


def lists(_request: HtmxHttpRequest):
    return JsonResponse({'stat': QList.dict_of_stat, 'lists': QList.dict_of_list})


def q2_open_func(request: HtmxHttpRequest, json_str: str, part='1'):
    json_data = json.loads(json_str)
    try:
        sfname = json_data['function']
        ff = QCals.quick_find_func(sfname)
        if ff is not None:
            request.recall = False
            request.remember = True
            fargs = json_data['input']
            return q1999_func_to_form(request, fname=ff, fargs=fargs, part=part)
        else:
            return seek_cal_help(request, sfname, part)
    except Exception as e:
        return q1_render_status(request, str(e), part)


def q1_open_func(request: HtmxHttpRequest):
    json_str = request.GET.get('json', '')
    if json_str:
        part = request.GET.get('part', '0')
        return q2_open_func(request, json_str, part)

    # | if posted in body
    fdata = request.FILES.get('io', None)
    # | if posted as values
    if not fdata:
        fdata = request.POST.get('io', None)

    if fdata:
        qf = QFile('', fdata)
        json_str = qf.text()
        return q2_open_func(request, json_str)
    else:
        return q1_render_status(request, 'Error (OPENF): Browse and select a calculator input file first')


def seek_cal_help(request, sfname, part="1"):
    if '*' in sfname:
        pattern = sfname
    else:
        pattern = f'*{sfname}*'
    return seek_help(request, pattern, scope='c', idonly=True, part=part)


def seek_help(request, sname, scope='cx', idonly=False, part="1"):
    request.GET = request.GET.copy()  # Create a mutable copy of the QueryDict
    request.GET['part'] = part
    request.GET['q'] = sname
    return catalog.views.search_catalog(request, scope, idonly)


def q1_render(request, template, context):
    request.times['render starts'] = time.time()
    try:
        ret = render(request, template, context)
    except Exception as e:
        import traceback
        traceback.print_exc()
        ret = ut.show_modal(request, 'Render', f'Error (R): {e}')
    request.times['render (ms)'] = int((time.time() - request.times['render starts']) * 1000)
    return ret


def q1_render_status(request: HtmxHttpRequest, msg: str, part='1'):
    return ut.show_modal(request, "", msg, part)


def q1_add_func(request: HtmxHttpRequest):
    sfname = request.GET.get('fname', "").strip().lower()
    # | making add func name case-insensitive
    spath = request.GET.get('path', "").strip()
    try:
        if len(sfname) != 0:
            ff = QCals.quick_find_func(sfname)
            if ff is not None:
                request.recall = True
                request.remember = True
                args = request.GET.get('fargs', "").strip()
                if len(args) == 0:
                    return q1999_func_to_form(request, fname=ff, part='1')
                else:
                    request.recall = False
                    return q1999_func_to_form(request, fname=ff, fargs=json.loads(args), part='1')
            else:
                return seek_cal_help(request, sfname, part='1')
        elif len(spath) != 0:
            request.recall = False
            request.remember = True
            # | path func name remains case-sensitive
            return q1999_func_to_form(request, path=spath, part='1')
        else:
            return seek_cal_help(request, sfname, part='1')
    except Exception as e:
        return ut.show_modal(request, "Add Calculator", f'Error (AF): {e}')


def q1_add_func_help(request: HtmxHttpRequest, **kwargs):
    ut.q1139_request_init(request)
    request.is_public = True
    request.token = request.token or request.GET.get('token', '')

    func_id = kwargs.get('fname', '').strip()
    __info = request.GET.get('__info', None)
    template = 'calculator-help-partial.html'

    try:
        context = q1141_read_func_meta(func_id, __info=None)
        dyn_html = get_fhelp(func_id, __info)
        context['dyn_html'] = dyn_html
        help_path = get_help_path(func_id)
        help_exists = help_path.exists()
        if help_exists:
            if help_path.suffix == '.html':
                context['help_html'] = help_path.as_posix()
            else:  # .md
                document_html = markdown.markdown(
                    help_path.read_text(encoding='utf-8'),
                    extensions=qconst.MARKDOWN_EXTENSIONS, output_format='html'
                )
                context['help_html'] = ""
                context['dyn_html'] += document_html
        else:
            context['help_html'] = "" if dyn_html else 'nohelp.html'

        current_user = request.user
        if current_user.is_active and current_user.is_staff:
            context['editable'] = help_exists and help_path.suffix == '.html'
            context['createable'] = not help_exists
    except Exception as e:
        logger.error(f">>> AFH: Unexpected error in q1_add_func_help for function '{func_id}': {e}")
        return ut.show_modal("", f"The function '{func_id}' not be found.")
    context["help_path"] = help_path.as_posix()
    return ut.get_page(request, template, context, page=f'{func_id}_help', as_card=True)


def q1_run_func(request: HtmxHttpRequest, **dictf):
    # request.remember = False
    # request.recall = False
    # ut.q1139_request_init(request) # | called inside q1199_func_to_form_common
    dictf.update({'cmd': 'save_io'})  # | or 'save'
    q1199_func_to_form_common(request, **dictf)
    result = QSave.getp()
    return JsonResponse(result, encoder=QEncoderBase)


def q1141_read_func_meta(func_id, __info=None, scope='qpots'):
    json_doc = {}
    json_doc['help'] = 'y' if get_help_path(func_id).exists() else 'nohelp.html'
    json_doc['clean'] = False  # if form has clean_data or not

    json_doc['info'] = {  # if func__info() exists it should return following dict
        'name': func_id,  # string, auto
        'title': 'Calculate ' + ut.variable_to_title(func_id),  # string
        'desc': '',  # string
        'calculate': 'Calculate',  # calculate button caption
        # 'variant': 0,
        # arg spec
        'schema': {},  # {"arg1":{props}, "arg2":{props}, ... }
        # where props are 'type', 'initial', 'choices', 'attr', 'widget', 'required', 'disabled',
        # 'label', 'label_suffix', 'help_text', 'error_messages', 'validators', 'localize'
        # 'attr':{'size':n, 'readonly':True, ...}
        # input interaction patterns
        'autofill': {},  # {"arg1":{"fields":["autof1","autof2",...], "autofill":{"arg1v1":[v1,v2,...],...}}, ...}
        'related': {},  # v4.21 {"1":{"fields":{"arg1":i1,"arg2":i2,...},"relation":{}},"2":...}
        # 'min_height': '0px',
        'showhide': {},
        # v4.21 {"arg1":{"fields":['shf1','shf2',...], "callback":'fname' or '@ condn' or not mentioned/'' },...}
        'anyof': {},  # v4.21 {"1":{"fields":['aof1','aof2',...]},...}
        # visual aids
        'images': {},  # {'top':['img1',...],'bottom':['img1',...],'left':['img1',...],'right':['img1',...]}
        # layout
        'row': [],  # ['arg1-argN',...]
        'col': [],  # ['arg1-argN',...]
        'newcol': [],  # internal use - auto calculated from row, col spec
        'endcol': [],  # internal use - auto calculated from row, col spec
        'newrow': [],  # internal use - auto calculated from row, col spec, template v4.21
        'inrowb': [],  # internal use - auto calculated from row, col spec, template v4.21
        'inrowe': [],  # internal use - auto calculated from row, col spec, template v4.21
        'endrow': [],  # internal use - auto calculated from row, col spec, template v4.21
        'outcol': [],  # ['chart','table','result','page','image']
        'template': '',  # string e.g. 'v4.21'
        # extra front end logic
        'onsubmit': '',
        'script': '',  # string e.g. 'function cfn(v){return v>100;}'
        # 'quom2': False,
        'qsel2': False, # internal use
        'qlist': False, # internal use
        'table_out': False, # internal use - auto calculated if it is an output table
        'table_in': False,  # internal use - auto calculated if it is an input table
        'kins': '',  # comma separated cal list meant to be sepcified through qfunc_info.json
        'tags': '',  # comma separated tag list meant to be specified through qfunc_info.json
        'xpr': True,
        'url': True,
        'loop': True,
        'step2': [],
        'cost': False, # internal use
        'inserts': {},
    }  # variable_to_title(fn.__name__)

    # run func_info() and then supersede by qfunc_info.json
    # that is higest precedence: 1 __info() < 1.5 qfunc_info.json
    func_info = QCals.run_func_info(func_id, __info, scope)

    for key in [
        'title',
        'desc',
        'calculate',
        # 'variant',
        'schema',
        'autofill',
        'related',
        # 'min_height',
        'showhide',
        'anyof',
        'row',
        'col',
        'newcol',
        'endcol',
        'newrow',
        'inrowb',
        'inrowe',
        'endrow',
        'outcol',
        'template',
        'onsubmit',
        'script',
        'kins',
        'tags',
        # 'beside',
        'xpr',
        'url',
        'loop',
        'step2',
        'cost',
        'inserts',
    ]:
        if key in func_info:
            json_doc['info'][key] = func_info[key]

    if 'images' in func_info:
        images = func_info['images']
        if 'top' in images:
            json_doc['info']['images']['top'] = images['top']
        if 'left' in images:
            json_doc['info']['images']['left'] = images['left']
        if 'right' in images:
            json_doc['info']['images']['right'] = images['right']
        if 'bottom' in images:
            json_doc['info']['images']['bottom'] = images['bottom']

    tmpl = qfunc_dict_template.get(func_id, '')
    if tmpl != '':
        json_doc['info']['template'] = tmpl  # used in sine for test purpose
    if json_doc['info']['template'] == '':
        tmpl = qfunc_dict_template.get('default', '')
        if tmpl != '':
            json_doc['info']['template'] = tmpl  # used in sine for test purpose

    json_doc['name'] = func_id
    # json_doc['id'] = cid

    # prepare list of tags
    tags = json_doc['info']['tags']
    if tags:
        tag_list = ut.css2strs(tags)
        json_doc['info']['tags'] = tag_list
    else:
        json_doc['info']['tags'] = []

    # prepare list of kins
    kins = json_doc['info']['kins']
    if kins:
        cal_list = ut.css2strs(kins)
        json_doc['info']['kins'] = [
            (cal, QCals.calc_root.get_node_by_id(cal).title)
            for cal in cal_list]
    else:
        json_doc['info']['kins'] = []

    return json_doc


def q1143_create_form_layout(request, func_addr):
    fargs = list(request.json_data.keys())
    if 'row' in request.json_doc['info']:
        request.json_doc['info'].update(
            layrow(func_addr, request.json_doc['info']['row'],
                   {'c4f': request.json_c4f, 'fargs': fargs}))
    if 'col' in request.json_doc['info']:
        request.json_doc['info'].update(
            laycol(func_addr, request.json_doc['info']['col'],
                   {'c4f': request.json_c4f, 'fargs': fargs}))


def q1146_result_transfer(request: HtmxHttpRequest, sfunc):
    trans = QMem.getf('trans')
    # from icecream import ic
    if trans:
        df = trans['transfer_queue']
        # ic(sfunc, df['Source Func'], sfunc in df['Source Func'].values)
        rows = df['Source Func'].isin([sfunc])
        # ic(df[rows])
        for index, row in df[rows].iterrows():
            # ic(row)
            srfld = row['Source Field']
            # ic(srfld)
            dsfunc = row['Dest Func']
            dsfld = row['Dest Field']
            # ic(request.ojson_data, srfld)
            dsdict = {dsfld: request.ojson_d4f[srfld]}
            # ic(dsdict)
            QMem.setf(dsfunc, dsdict)


def q1149_func_to_form_context(request: HtmxHttpRequest, func_id, cid, kwargs):
    func_addr = QCals.addr(func_id)
    __info = kwargs.get('__info', None)

    # if request.recall:
    #     # recalling dynamic info is problematic if there are more than one calculator
    #     # on screen, __info can be different, so we shouldn't recall info
    #     # effectively it also mean we should not remember calculation
    #     __info = QMem.getf2(request, sfunc, 'input', '__info')
    #     print('__info from recall', __info, kwargs)
    #     kwargs.update({'__info': __info})
    request.json_doc = q1141_read_func_meta(func_id, __info)
    q11429_func_to_form_schema(request, func_addr, func_id, cid, kwargs)
    q1143_create_form_layout(request, func_addr)
    request.context['input'] = q11469_form_data_create_dynaform_and_fill(
        request, request.json_schema, request.json_data, request.json_s2f,
        request.json_doc, cid, 0)  # data, form, doc[info]
    if request.method == 'POST':
        if not request.json_doc['clean']: request.success &= False

    result = q11449_form_data_postprocess_and_run(request, func_id)  # , cid
    # update ojson_data, ojson_schema
    q1145_result_to_form_schema(request, func_id, cid, result)

    io_dict = {
        'function': func_id,
        'input': request.json_d4f,
        'output': request.ojson_d4f,
        'status': request.ojson_doc,
    }
    if request.cmd == 'save_io':
        QSave.clear()
        QSave.setp(io_dict)

    if request.cmd == '' and request.POST and request.json_doc['info'].get('step2', []):
        # | ---------------------------------
        # | if anything is not serializable (e.g. qreq, beautifulsoup .string) will fail
        QIO.setp({cid: io_dict})
        # | ---------------------------------

    q1146_result_transfer(request, func_id)
    if settings.DEBUG: qvars.last_dump = ut.request_dump(request)
    # print(request.ojson_schema, request.ojson_data, request.ojson_doc)

    request.ojson_doc['name'] = func_id
    request.context['output'] = q11469_form_data_create_dynaform_and_fill(
        request, request.ojson_schema, request.ojson_data, None,
        request.ojson_doc, cid, 1)  # data, form, doc[table|chart]
    input_id = request.input_id
    request.context['func_id'] = func_id
    request.context['input_id'] = input_id
    request.context['fav_state'] = input_id in QFav.getp1(func_id, [])

    # start change@29.07.26
    # Show variants button only when this user has at least one private variant for this calculator
    has_user_variants = False
    if request.user.is_authenticated:
        has_user_variants = QInput.myinputs.filter(
            user=request.user,
            object_id='input',
            item_id=func_id,
            is_example=False,
        ).exists()

    # Show examples button only when calculator owner has created at least one example
    cal_id, cal_name, cal_owner = fid2owner(func_id)
    has_owner_examples = False
    if cal_owner:
        has_owner_examples = QInput.myinputs.filter(
            user__username=cal_owner,
            object_id='input',
            item_id=func_id,
            is_example=True,
        ).exists()

    request.context['has_user_variants'] = has_user_variants
    request.context['has_owner_examples'] = has_owner_examples
    # end change@29.07.26
    return


def get_file(request, sfunc, sfld, value):
    if value:  # QFile
        request.json_d4f[sfld] = value
        content = value.to_dict()  # should not be required to be called explicitly
        QTemp.setp1(sfunc + ':' + sfld, content)
    else:
        content = QTemp.getp1(sfunc + ':' + sfld)
        request.json_d4f[sfld] = QFile.load_content(sfunc, content) if content else None


def q1145_result_to_form_schema(request: HtmxHttpRequest, func_id, cid, result):
    us = request.pref  # User's Request Pref
    request.ojson_schema = []  # schema for form
    request.ojson_data = {}  # data for form
    request.ojson_doc = {
        'table_out': False,
        'recall': request.recall,
        'remember': request.remember,
        'success': request.success,
        'var_owner': request.var_owner,
        'variant': request.variant,
        'token': request.token,
    }  # doc for form
    request.ojson_data_type = []
    request.ojson_keep_dumps = qjson_dumps(keep_format(result)) if func_id != 'collect' else {}

    def rs_item(request, arg_name, value):
        request.ojson_d4f[arg_name] = value
        name = ut.title_to_variable(arg_name, '__r')
        if isPQ(value):  # quantity
            request.json_doc['info']['cost'] = True
            name = name + 'q'
            fv, fuom = qformat(value.val, value.unit, pref=us)
            request.ojson_data[name] = fv
            request.ojson_data_type.append('oval-q')
            request.ojson_data[name + '_uom'] = fuom
            request.ojson_data_type.append('ouom-q')
        elif isinstance(value, pd.DataFrame):  # table
            request.json_doc['info']['loop'] = False
            table_id = f"{cid}_{name}"
            # value.index = np.arange(1, len(value) + 1)  # 0 based index
            # value.index = range(1, len(value) + 1)  # will also do
            value = value.apply(lambda col: col.map(df_formatter))  # apply format for table-out
            request.ojson_data[name] = qhtml(
                value.to_html(
                    table_id=table_id,
                    classes=f'table table-responsive table-out {cid}',
                    na_rep='',
                    # float_format=qformatter().format,
                    index=False
                ))  # datatable-basic {cid}
            # cast using qhtml() to exclude it from output data section
            # ic(request.ojson_data[name])
            request.ojson_data_type.append('html')
            request.ojson_doc['table_out'] = True
        elif str(type(value)).lower().find('chartkick') > -1:
            request.json_doc['info']['loop'] = False
            request.ojson_data[name] = qhtml(value)
            # cast using qhtml() to exclude it from output data section
            request.ojson_data_type.append('html')
        # elif str(type(value)).lower().find('qchart') > -1:
        elif isinstance(value, QChart) or isinstance(value, QMap):
            request.json_doc['info']['loop'] = False
            request.ojson_data[name] = \
                qhtml(wrap_actions(f"<img class='img-plot qhtml' src='data:image/png;base64,{value.chart()}'>"))
            # cast using qhtml() to exclude it from output data section
            request.ojson_data_type.append('html')
        # elif str(type(value)).lower().find('qimage') > -1:
        elif isinstance(value, QImage):
            request.json_doc['info']['loop'] = False
            request.ojson_data[name] = \
                qhtml(wrap_actions(f"<img class='img-plot qhtml' src='data:image/png;base64,{value.image()}'>"))
            # cast using qhtml() to exclude it from output data section
            request.ojson_data_type.append('html')
        elif isinstance(value, qpage):  # page of text
            request.json_doc['info']['loop'] = False
            request.ojson_data[name] = qhtml(f"<pre>{mark_safe(value)}</pre>")
            # cast using qhtml() to exclude it from output data section
            request.ojson_data_type.append('html')
        elif isinstance(value, float):
            name = name + 'f'
            request.ojson_data[name] = qformat(value, pref=us)
            request.ojson_data_type.append('char')
        elif isinstance(value, int):
            name = name + 'i'
            request.ojson_data[name] = qformat(value, pref=us)
            request.ojson_data_type.append('char')
        elif isinstance(value, qvstr):
            request.ojson_data[name] = value
            request.ojson_data_type.append('html')
        elif isinstance(value, qhtml):
            request.json_doc['info']['loop'] = False
            request.ojson_data[name] = mark_safe(value)
            request.ojson_data_type.append('html')
        elif isinstance(value, (date, dt_time)):
            request.ojson_data[name] = value.isoformat()  # no sep
            request.ojson_data_type.append('char')
        elif isinstance(value, datetime):
            request.ojson_data[name] = value.isoformat(sep=' ')
            request.ojson_data_type.append('char')
        elif isinstance(value, QDateTime):
            request.ojson_data[name] = str(value)
            request.ojson_data_type.append('char')
        elif isinstance(value, oqfunc):
            pass
        elif len(str(value)) > 25:  # long text
            request.json_doc['info']['loop'] = False
            request.ojson_data[name] = value
            request.ojson_data_type.append('textarea')
        else:  # str
            request.ojson_data[name] = value
            request.ojson_data_type.append('char')
        return

    def join_title(t1, t2):
        return f"{t1} {t2}"

    def process_result(result, name=''):  # v2
        if isinstance(result, set):
            result = list(result)
        if isinstance(result, tuple) or isinstance(result, list):
            # result can be a list or tuple of values/qts
            if name == '':
                name = 'result'

            lnr = len(result)
            if lnr <= 1:  # output as variables
                i = 0
                for value in result:
                    process_result(value, join_title(name, str(i + 1)) if lnr > 1 else name)
                    i += 1
            elif all(isinstance(v, (float, Qty, int, str, bool, date, datetime, dt_time)) for v in
                     result):  # output as table
                df = pd.DataFrame(
                    {ut.variable_to_title(name): [df_formatter(cell) for cell in result]}  # apply format for result
                )
                rs_item(request, name, df)
            else:  # output as variables
                i = 0
                for value in result:
                    process_result(value, join_title(name, str(i + 1)) if lnr > 1 else name)
                    i += 1
        elif isinstance(result, dict):  # result can be a dictionary of values or quantities
            i = 0
            for name2, value in result.items():
                if name != '':
                    name2 = join_title(name, name2)
                # rs_item(name, value)
                process_result(value, name2)
                i += 1
        else:  # result can be simply a value or quantity
            if name == '':
                name = 'result'
            rs_item(request, name, result)

    process_result(result)
    i = 0
    # print(json_data.items(), json_data)
    for name, value in request.ojson_data.items():
        request.ojson_schema.append({})
        request.ojson_schema[i]["name"] = name
        request.ojson_schema[i]["type"] = request.ojson_data_type[i]  # type(value)
        request.ojson_schema[i]["initial"] = value
        # print (name, value)
        request.ojson_schema[i]["attrs"] = {'readonly': True}

        if request.ojson_data_type[i] == 'oval-q':
            request.ojson_schema[i]["type"] = 'char'
            request.ojson_schema[i]['attrs']['class'] = 'oval-q'
        elif request.ojson_data_type[i] == 'ouom-q':
            request.ojson_schema[i]["type"] = 'char'  # 'uom'
            request.ojson_schema[i]['attrs']['class'] = 'ouom-q'
        elif request.ojson_data_type[i] == 'textarea':
            request.ojson_schema[i]['attrs']['class'] = 'texta'
        elif request.ojson_data_type[i] in ['integer', 'float']:
            request.ojson_schema[i]['attrs']['class'] = 'val'
        elif request.ojson_data_type[i] in ['text']:
            request.ojson_schema[i]['attrs']['class'] = 'inp'
        elif request.ojson_data_type[i] == 'uom':
            request.ojson_schema[i]["type"] = 'char'  # 'uom'
            request.ojson_schema[i]['attrs']['class'] = 'uom'

        i += 1
    # print(request.ojson_data, request.ojson_schema, result, type(result))
    return


def add_to_cart(request):
    keep = request.GET.get('keep', None)
    ut.q1139_request_init(request)
    cnt = 0
    if keep:
        cnt = QKeep.getp1('count', 0) + 1
        QKeep.setp1(cnt, keep)
        QKeep.setp1('count', cnt)
    return HttpResponse(
        f'<span id="cart-count" hx-swap-oob="true" class="badge bg-primary badge-pill ml-auto">'
        f'{cnt}</span>#{cnt} Collected')
