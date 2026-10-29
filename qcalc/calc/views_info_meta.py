# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

import qconst
import qutil as ut
from qvars import qfunc_dict_layout

from .mod_cutil import get_help_path
from .mod_layout_dynamic import has_dynamic_layout
from .mod_prefs import declared_prefs
from .mod_qcals import QCals
from qutil.mod_info_keys import INFO_OVERRIDE_KEYS


_STATIC_SIDES = {
    'input': ('input_columns', 'inp1'),
    'output': ('output_columns', 'out1'),
}


def template_name(layout, input_columns, output_columns):
    icol = '2' if input_columns == 2 else ''
    ocol = '2' if output_columns == 2 else ''
    template = f't{icol}b{ocol}' if layout == 'tb' else f'l{icol}r{ocol}'
    return template


def side_columns(columns, group1, all_fields=None):
    """Column count (1 or 2) of one side of a static template.

    An explicit 1 or 2 wins. Otherwise two columns are needed only when some field is left out of
    the first group. Without the field list (all_fields is None) the spec itself decides.
    """
    if columns in (1, 2):
        return columns
    if all_fields is None or isinstance(group1, str):
        return 1 if group1 == '*' else 2
    return 2 if set(all_fields) - set(group1 or []) else 1


def static_template_name(info):
    return template_name(
        info.get('layout', 'lr'),
        side_columns(info.get('input_columns'), info.get('inp1', '*')),
        side_columns(info.get('output_columns'), info.get('out1', '*')),
    )


def refresh_template(info):
    # | derive the template from the effective layout and columns
    info['template'] = 'dynamic' if has_dynamic_layout(info) else static_template_name(info)


def resolve_static_side(info, side, all_fields):
    """Fix the column count of a side of a static template once its resolved field list is known.

    info['inp1'] / info['out1'] must already hold the resolved field list. Two explicit columns
    with a group that covers every field get the fields split in half, so column 2 is not empty.
    """
    columns_key, group_key = _STATIC_SIDES[side]
    group1 = list(info.get(group_key) or [])
    columns = side_columns(info.get(columns_key), group1, all_fields)
    if columns == 2 and not set(all_fields) - set(group1):
        info[group_key] = list(all_fields)[:(len(all_fields) + 1) // 2]
    info[columns_key] = columns
    info['template'] = static_template_name(info)


def _normalize_layout_blocks(blocks, spec_source):
    if not isinstance(blocks, list):
        return blocks

    result = []
    for block in blocks:
        if not isinstance(block, dict):
            continue

        block = dict(block)
        kind_value = block.get('kind')
        if kind_value is None:
            kind_value = 'tabs' if block.get('tabs') else 'fields'
        kind = str(kind_value).strip().lower()

        if kind == 'tabs':
            block['kind'] = 'tabs'
            block['tabs'] = [
                {**tab, 'fields': ut.specified_args(spec_source, tab.get('fields', []), empty_spec='')}
                for tab in block.get('tabs', [])
                if isinstance(tab, dict)
            ]
        else:
            block['kind'] = 'fields'
            block['fields'] = ut.specified_args(spec_source, block.get('fields', []), empty_spec='')

        result.append(block)

    return result


def q1141_read_func_meta(func_id, scope='qpots'):
    json_doc = {}
    json_doc['help'] = 'y' if get_help_path(func_id).exists() else 'nohelp.html'  # internal
    json_doc['clean'] = False  # if form has clean_data or not # internal

    json_doc['info'] = {  # func__info() should return following dict
        'name': func_id,  # internal, string, auto
        'title': 'Calculate ' + ut.variable_to_title(func_id),  # string
        'desc': '',  # string
        'calculate': 'Calculate',  # calculate button caption
        'schema': {},  # {"arg1":{props}, "arg2":{props}, ... }
        # where props are 'type', 'initial', 'choices', 'attr', 'widget', 'required', 'disabled',
        # 'label', 'label_suffix', 'help_text', 'error_messages', 'validators', 'localize'
        # 'attr':{'size':n, 'readonly':True, ...}
        # input interaction patterns
        'interactive': False,  # effective value is resolved per request (mod_prefs.resolve_effective_prefs)
        'autofill': {},  # {"arg1":{"fields":["autof1","autof2",...], "autofill":{"arg1v1":[v1,v2,...],...}}, ...}
        'related': {},  # v4.21 {"1":{"fields":{"arg1":i1,"arg2":i2,...},"relation":{}},"2":...}
        'showhide': {},
        # v4.21 {"arg1":{"fields":['shf1','shf2',...], "callback":'fname' or '@ condn' or not mentioned/'' },...}
        'anyof': {},  # v4.21 {"1":{"fields":['aof1','aof2',...]},...}
        # visual aids
        'images': {},  # {'top':['img1',...],'bottom':['img1',...],left and right not supported}
        # layout
        'row': [],  # ['arg1-argN',...] #legacy
        'col': [],  # number or ['arg1-argN',...] # legacy
        'layout': 'lr',  # 'lr' or 'tb', effective value is resolved per request (mod_prefs)
        'inp1': '*',  # array or css string, parameter filtering
        'out1': '*',  # array or css string, parameter filtering
        'input_columns': None,  # 1 or 2; the explicit count is authoritative for both dynamic and static
        # templates. None: dynamic infers it from blocks, static from whether inp1 covers all fields
        'output_columns': None,  # 1 or 2, same rules as input_columns, using out1
        'input_blocks': [],  # ordered block layout for input side
        'output_blocks': [],  # ordered block layout for output side
        'template': 'lr',  # internal
        # extra front end logic
        'onsubmit': '',
        'script': '',  # string e.g. 'function cfn(v){return v>100;}'
        'qsel2': False,  # internal
        'qlist': False,  # internal
        'table_out': False,  # internal - auto calculated if it is an output table
        'table_in': False,  # internal - auto calculated if it is an input table
        'kins': '',  # comma separated cal list meant to be sepcified through qfunc_info.json
        'tags': '',  # comma separated tag list meant to be specified through qfunc_info.json
        'xpr': True,  # internal
        'url': True,  # internal
        'loop': False,  # internal, True,
        'step2': [],
        'cost': False,  # internal
        'single_instance': False,  # internal
        'single_instance_key': '',  # internal
        'provides_data': {},
        'consumes_data': {},
        'inserts': {},
        'table_out_all': False,  # True shows all rows of output tables (no pagination)
        # comma separated list of words with proper case that needs to be unchanged
        # during title case conversion for this calculator function
        'proper': '',
        'remember': True,
    }

    # run func_info() and then supersede by qfunc_info.json
    # that is higest precedence: 1 __info() < 1.5 qfunc_info.json
    # func_info = QCals.run_func_info(func_id, __info, scope)
    func_info = QCals.run_func_info(func_id, scope)
    for key in INFO_OVERRIDE_KEYS:
        if key in func_info:
            json_doc['info'][key] = func_info[key]

    # preferences defined at the calculator level, the resolver gives them precedence over the session level
    declared = set(declared_prefs(func_info))
    if json_doc['info']['layout'] not in qconst.QCALC_LAYOUTS:
        json_doc['info']['layout'] = 'lr'
        declared.discard('layout')

    if has_dynamic_layout(json_doc['info']):
        json_doc['info']['template'] = 'dynamic'
    else:
        json_doc['info']['template'] = static_template_name(json_doc['info'])

    if 'images' in func_info:
        images = func_info['images']
        if 'top' in images:
            json_doc['info']['images']['top'] = images['top']
        if 'bottom' in images:
            json_doc['info']['images']['bottom'] = images['bottom']

    tmpl = qfunc_dict_layout.get(func_id, '')
    if tmpl != '':
        json_doc['info']['layout'] = tmpl
        declared.add('layout')
    if json_doc['info']['layout'] == '':
        tmpl = qfunc_dict_layout.get('default', '')
        if tmpl != '':
            json_doc['info']['layout'] = tmpl

    json_doc['declared'] = sorted(declared)
    json_doc['name'] = func_id

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

    proper = json_doc['info']['proper']
    json_doc['info']['proper'] = ut.css2proper_dict(proper)

    return json_doc
