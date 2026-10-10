# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

import qconst
import qutil as ut
from qvars import qfunc_dict_layout

from .mod_cutil import get_help_path
from .mod_layout_dynamic import has_dynamic_layout
from .mod_qcals import QCals


def template_name(layout, inp1, out1):
    icol = '' if inp1 == '*' else '2'
    ocol = '' if out1 == '*' else '2'
    template = f't{icol}b{ocol}' if layout == 'tb' else f'l{icol}r{ocol}'
    return template


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


def q1141_read_func_meta(func_id, __info=None, scope='qpots'):  # __info__
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
        'interactive': False,
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
        'layout': 'lr',  # 'lr' or 'tb'
        'inp1': '*',  # array or css string, parameter filtering
        'out1': '*',  # array or css string, parameter filtering
        'input_columns': None,  # 1 or 2, used by dynamic renderer, optional, inference from blocks is the default,
        # but the explicit column count is authoritative
        'output_columns': None,  # 1 or 2, used by dynamic renderer, optional, inference from blocks is the default,
        # but the explicit column count is authoritative
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
    }

    # run func_info() and then supersede by qfunc_info.json
    # that is higest precedence: 1 __info() < 1.5 qfunc_info.json
    func_info = QCals.run_func_info(func_id, __info, scope)
    for key in [
        'title',
        'desc',
        'calculate',
        'schema',
        'interactive',
        'autofill',
        'related',
        'showhide',
        'anyof',
        # 'images',
        'row',  # obsolete
        'col',  # obsolete
        'layout',
        'inp1',
        'out1',
        'input_columns',
        'output_columns',
        'input_blocks',
        'output_blocks',
        # 'template', # internal
        'onsubmit',
        'script',
        'kins',
        'tags',
        'xpr',  # internal
        'url',  # internal
        'loop',  # internal
        'step2',
        'cost',  # internal
        'single_instance',
        'single_instance_key',
        'provides_data',
        'consumes_data',
        'inserts',
        'table_out_all',
        'proper',
    ]:
        if key in func_info:
            json_doc['info'][key] = func_info[key]

    if json_doc['info']['layout'] not in qconst.QCALC_LAYOUTS:
        json_doc['info']['layout'] = 'lr'

    if has_dynamic_layout(json_doc['info']):
        json_doc['info']['template'] = 'dynamic'
    else:
        json_doc['info']['template'] = template_name(
            json_doc['info']['layout'], json_doc['info']['inp1'], json_doc['info']['out1'])

    if 'images' in func_info:
        images = func_info['images']
        if 'top' in images:
            json_doc['info']['images']['top'] = images['top']
        if 'bottom' in images:
            json_doc['info']['images']['bottom'] = images['bottom']

    tmpl = qfunc_dict_layout.get(func_id, '')
    if tmpl != '':
        json_doc['info']['layout'] = tmpl
    if json_doc['info']['layout'] == '':
        tmpl = qfunc_dict_layout.get('default', '')
        if tmpl != '':
            json_doc['info']['layout'] = tmpl

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
