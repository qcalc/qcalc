# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

import qvars
from calc import QTemp, QList, QFav, QCalAlias
from django.shortcuts import render
from django.http import HttpResponse
import catalog.views
from .mod_ucals import get_uc_list
from .views_form_data import *
from .mod_layout_dynamic import has_dynamic_layout, build_layout_plan
from .views_info_meta import q1141_read_func_meta, template_name, _normalize_layout_blocks
from .views_result import q1145_result_to_form_schema, q1146_result_transfer
from .views_step2 import cache_step2_io
from qutil import HtmxHttpRequest, preprocess_expression, fid2owner
import qutil as ut
import json
from django.conf import settings
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
            '0': 'gen-calculator.html',  # full page e.g. browser url
            '1': 'gen-calculator-partial.html',  # calculator partial e.g. add cal, open json, command button
            '2': 'insert-calculator-form-partial.html',  # form partial e.g. variant, command button, structural
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

        # Ordinary POST → output only.
        # Structural POST → re-render the requested form/calculator part.
        structural = (
            getattr(request, 'cmd', '') in {
            'load', 'resize', 'edit', 'display', '__modify',
        }
            or request.headers.get('X-QCalc-Structural-Cmd') == '1'
            or request.POST.get('qcalc_structural_cmd') == '1'
        )
        if request.method == 'POST' and not structural:
            template = request.json_doc['info'].get('template', '')
            if template == 'dynamic':
                template = 'layout-output-dynamic-section.html'
            elif template == '':
                template = 'layout-output-1-section.html'
            elif template in ['l2r', 'lr', 't2b', 'tb']:
                template = 'layout-output-1-section.html'
            else:  # layout in ['l2r2', 'lr2', 't2b2', 'tb2']
                template = 'layout-output-2-section.html'
        else:
            template = get_template(part)

        return q1_render(request, template, request.context)
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
        # printable mode parameter: 'layout' (default) or 'flat'
        request.print_mode = (request.GET.get('print') or '').strip().lower() if request.method == 'GET' else ''
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
        # propagate print mode into context and json_doc.info for templates
        request.context['print_mode'] = getattr(request, 'print_mode', '')
        try:
            if hasattr(request, 'json_doc') and isinstance(request.json_doc, dict):
                request.json_doc.setdefault('info', {})['print_mode'] = getattr(request, 'print_mode', '')
        except Exception:
            pass

        # Server-side flat printable view: prefer static (non-dynamic) tb layout
        # Use initial values (None or empty lists) so the template selection
        # falls back to static template logic (template_name) rather than dynamic renderer.
        if getattr(request, 'print_mode', '') == 'flat':
            try:
                info = request.json_doc.setdefault('info', {})
                # Force top-to-bottom preference for reading order
                info['layout'] = 'tb'
                # Set columns to None to prefer template's static resolution
                info['input_columns'] = None
                info['output_columns'] = None
                # Empty block lists ensure has_dynamic_layout() is False
                info['input_blocks'] = []
                info['output_blocks'] = []
                # Ensure simple split keys include all fields (static templates rely on inp1/out1)
                info['inp1'] = '*'
                info['out1'] = '*'
                # Flag for client-side Tabulator initializers to render all rows
                info['tabulator_print_all'] = True
                request.context['tabulator_print_all'] = True

                # Recompute template choice so gen-calculator-core will render using
                # static top-to-bottom template (not dynamic) in flat printable mode.
                try:
                    if has_dynamic_layout(info):
                        info['template'] = 'dynamic'
                    else:
                        info['template'] = template_name(info.get('layout', 'lr'), info.get('inp1', '*'),
                                                         info.get('out1', '*'))
                except Exception:
                    # ignore and fall back to whatever template was earlier
                    pass

                # Ensure any already-built context entries reflect the modified info
                try:
                    if isinstance(request.context.get('input'), dict):
                        doc = request.context['input'].get('doc')
                        if isinstance(doc, dict):
                            doc['info'] = info
                    if isinstance(request.context.get('output'), dict):
                        doc = request.context['output'].get('doc')
                        if isinstance(doc, dict):
                            doc['info'] = info
                except Exception:
                    pass
            except Exception:
                # Keep minimal failure surface: do nothing if any step fails
                pass
    except Exception as e:
        request.success &= False
        if settings.DEBUG:
            traceback.print_exc()
        e.args = (f"Error (FTFC) {str(e)}",)
        raise e

    request.times['common (ms)'] = int((time.time() - request.times['common starts']) * 1000)
    return


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
            if ff is None:
                # Personal aliases are intentionally supported only in "add calculator" flow.
                alias_target = QCalAlias.getp1(sfname, '')
                if isinstance(alias_target, str):
                    alias_target = alias_target.strip().lower()
                else:
                    alias_target = ''
                if alias_target:
                    ff = QCals.quick_find_func(alias_target)
                    if ff is None:
                        raise Exception(
                            f"Error (AF): Alias '{sfname}' points to missing calculator '{alias_target}'")
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
        context = q1141_read_func_meta(func_id, __info=__info)
        dyn_html = '' # get_fhelp(func_id, __info)
        context['dyn_html'] = dyn_html
        help_path = get_help_path(func_id)
        help_exists = help_path.exists()
        doc_context = ut.read_doc_content(help_path)
        if doc_context:
            if help_path.suffix == '.md':
                context['help_html'] = ""
                context['dyn_html'] += doc_context['dyn_html']
            else:
                context['help_html'] = doc_context['help_html']
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
    request.json_doc['info']['help'] = get_fhelp(func_id, __info)
    request.json_doc['info']['inp1'] = ut.specified_args(func_addr, request.json_doc['info']['inp1'], empty_spec='')
    request.json_doc['info']['input_blocks'] = _normalize_layout_blocks(
        request.json_doc['info'].get('input_blocks', []),
        func_addr,
    )
    # print('|', request.json_doc['info']['input_blocks'])
    q11429_func_to_form_schema(request, func_addr, func_id, cid, kwargs)
    request.context['input'] = q11469_form_data_create_dynaform_and_fill(
        request, request.json_schema, request.json_data, request.json_s2f,
        request.json_doc, cid, 0)  # data, form, doc[info]
    if request.method == 'POST':
        if not request.json_doc['clean']: request.success &= False
    # print('|',request.json_s2f, request.json_c4f)

    result = q11449_form_data_postprocess_and_run(request, func_id)  # , cid
    # update ojson_data, ojson_schema
    proper_dict = request.json_doc['info']['proper']
    q1145_result_to_form_schema(request, func_id, cid, result, proper_dict)

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
        cache_step2_io(
            cid, func_id, request.json_d4f, request.ojson_d4f
        )

    q1146_result_transfer(request, func_id)
    if settings.DEBUG: qvars.last_dump = ut.request_dump(request)

    request.ojson_doc['name'] = func_id
    request.ojson_doc.update({'info': {'proper': proper_dict}})
    request.context['output'] = q11469_form_data_create_dynaform_and_fill(
        request, request.ojson_schema, request.ojson_data, None,
        request.ojson_doc, cid, 1)  # data, form, doc[table|chart]
    if request.json_doc['info'].get('template') == 'dynamic':
        input_ctx = request.context['input']
        output_ctx = request.context['output']
        input_form = input_ctx.get('form') if isinstance(input_ctx, dict) else getattr(input_ctx, 'form', None)
        output_form = output_ctx.get('form') if isinstance(output_ctx, dict) else getattr(output_ctx, 'form', None)
        request.context['layout_plan'] = build_layout_plan(
            request.json_doc['info'],
            input_form,
            output_form,
        )
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
