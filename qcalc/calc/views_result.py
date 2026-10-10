# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

import logging
from datetime import date, datetime, time as dt_time

import pandas as pd
from django.utils.safestring import mark_safe

import qconst
import qutil as ut
from calc.templatetags.qfilter import field_root
from qcore import (
    QChart,
    QImage,
    QMap,
    Qty,
    df_formatter,
    is_qtbl,
    oqfunc,
    qformat,
    qhtml,
    qjson_dumps,
    qpage,
    qvstr,
    wrap_actions,
)
from qutil import QDateTime

from .mod_cache import QMem
from .mod_cutil import keep_format
from .mod_result import df2normalized
from .views_info_meta import _normalize_layout_blocks

logger = logging.getLogger(__name__)


def q1146_result_transfer(request, sfunc):
    trans = QMem.getf('trans')
    if trans:
        df = trans['transfer_queue']
        rows = df['Source Func'].isin([sfunc])
        for _index, row in df[rows].iterrows():
            srfld = row['Source Field']
            dsfunc = row['Dest Func']
            dsfld = row['Dest Field']
            dsdict = {dsfld: request.ojson_d4f[srfld]}
            QMem.setf(dsfunc, dsdict)


def q1145_result_to_form_schema(request, func_id, cid, result, proper_dict):
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
        'message_text': '',
        'message_kind': '',
        'message_only': False,
    }  # doc for form
    request.ojson_data_type = []
    request.ojson_keep_dumps = qjson_dumps(keep_format(result)) if func_id != 'collect' else {}

    def classify_outcome_message(cmd, success, value):
        if not isinstance(value, str):
            return False, '', ''

        txt = value.strip()
        if txt == '':
            return False, '', ''

        if txt.startswith('Error ('):
            return True, 'error', txt
        if txt.startswith('Warning (') or txt.startswith('Warn ('):
            return True, 'warning', txt

        if cmd not in ['', 'run']:
            return True, 'info' if success else 'error', txt

        return False, '', ''

    is_message_only, message_kind, message_text = classify_outcome_message(
        request.cmd,
        request.success,
        result,
    )
    if is_message_only:
        request.ojson_doc['message_only'] = True
        request.ojson_doc['message_kind'] = message_kind
        request.ojson_doc['message_text'] = message_text
        request.json_doc['info']['output_blocks'] = []
        request.json_doc['info']['out1'] = '*'
        return

    def rs_item(request, arg_name, value):
        request.ojson_d4f[arg_name] = value
        name = ut.title_to_variable(arg_name, qconst.TOK_RESULT_SUFFIX)
        if isinstance(value, Qty):
            request.json_doc['info']['cost'] = True
            fv, fuom = qformat(value.val, value.unit, pref=us)
            request.ojson_data[name] = fv
            request.ojson_data_type.append('oval-q')
            request.ojson_data[name + '_uom'] = fuom
            request.ojson_data_type.append('ouom-q')
            request.json_doc['info']['loop'] = True
        elif isinstance(value, pd.DataFrame):
            request.json_doc['info']['loop'] = True
            table_id = f"{cid}_{name}"
            value = df2normalized(value, do_format=True)
            table_html = value.to_html(
                table_id=table_id,
                classes=f'table table-responsive table-out {cid}',
                na_rep='None',
                index=False
            )
            if request.json_doc['info'].get('table_out_all'):
                table_html = table_html.replace('<table ', '<table data-page-all="true" ', 1)
            request.ojson_data[name] = qhtml(wrap_actions(table_html, 'table-wrap'))
            request.ojson_data_type.append('html')
            request.ojson_doc['table_out'] = True
        elif isinstance(value, QChart) or isinstance(value, QMap):
            request.ojson_data[name] = qhtml(
                wrap_actions(f"<img class='img-plot qhtml' src='data:image/png;base64,{value.chart()}'>")
            )
            request.ojson_data_type.append('html')
        elif isinstance(value, QImage):
            request.ojson_data[name] = qhtml(
                wrap_actions(f"<img class='img-plot qhtml' src='data:image/png;base64,{value.image()}'>")
            )
            request.ojson_data_type.append('html')
        elif isinstance(value, qpage):
            request.ojson_data[name] = qhtml(f"<pre>{mark_safe(value)}</pre>")
            request.ojson_data_type.append('html')
        elif isinstance(value, float):
            request.ojson_data[name] = qformat(value, pref=us)
            request.ojson_data_type.append('char')
            request.json_doc['info']['loop'] = True
        elif isinstance(value, int):
            request.ojson_data[name] = qformat(value, pref=us)
            request.ojson_data_type.append('char')
            request.json_doc['info']['loop'] = True
        elif isinstance(value, qvstr):
            request.ojson_data[name] = value
            request.ojson_data_type.append('html')
        elif isinstance(value, qhtml):
            request.ojson_data[name] = mark_safe(value)
            request.ojson_data_type.append('html')
        elif isinstance(value, (date, dt_time)):
            request.ojson_data[name] = value.isoformat()
            request.ojson_data_type.append('char')
        elif isinstance(value, datetime):
            request.ojson_data[name] = value.isoformat(sep=' ')
            request.ojson_data_type.append('char')
        elif isinstance(value, QDateTime):
            request.ojson_data[name] = str(value)
            request.ojson_data_type.append('char')
        elif isinstance(value, oqfunc):
            pass
        elif len(str(value)) > 25:
            request.ojson_data[name] = value
            request.ojson_data_type.append('textarea')
        else:
            request.ojson_data[name] = value
            request.ojson_data_type.append('char')

    def join_title(t1, t2):
        return f"{t1} {t2}"

    def process_result(result, name=''):
        if isinstance(result, set):
            result = list(result)
        if isinstance(result, tuple) or isinstance(result, list):
            if name == '':
                name = 'result'

            lnr = len(result)
            if lnr <= 1:
                i = 0
                for value in result:
                    process_result(value, join_title(name, str(i + 1)) if lnr > 1 else name)
                    i += 1
            elif all(isinstance(v, (float, Qty, int, str, bool, date, datetime, dt_time)) for v in result):
                df = pd.DataFrame({ut.variable_to_title(name, proper_dict): [df_formatter(cell) for cell in result]})
                rs_item(request, name, df)
            else:
                i = 0
                for value in result:
                    process_result(value, join_title(name, str(i + 1)) if lnr > 1 else name)
                    i += 1
        elif is_qtbl(result):
            if name == '':
                name = 'result'
            df = pd.DataFrame(
                data=result["data"],
                columns=result["columns"],
                index=result.get("index"),
            )
            rs_item(request, name, df)
        elif isinstance(result, dict):
            i = 0
            for name2, value in result.items():
                if name != '':
                    name2 = join_title(name, name2)
                process_result(value, name2)
                i += 1
        else:
            if name == '':
                name = 'result'
            rs_item(request, name, result)

    process_result(result)
    i = 0
    for name, value in request.ojson_data.items():
        request.ojson_schema.append({})
        request.ojson_schema[i]["name"] = name
        request.ojson_schema[i]["type"] = request.ojson_data_type[i]
        request.ojson_schema[i]["initial"] = value
        request.ojson_schema[i]["attrs"] = {'readonly': True}

        if request.ojson_data_type[i] == 'oval-q':
            request.ojson_schema[i]["type"] = 'char'
            request.ojson_schema[i]['attrs']['class'] = 'oval-q'
        elif request.ojson_data_type[i] == 'ouom-q':
            request.ojson_schema[i]["type"] = 'char'
            request.ojson_schema[i]['attrs']['class'] = 'ouom-q'
        elif request.ojson_data_type[i] == 'textarea':
            request.ojson_schema[i]['attrs']['class'] = 'texta'
        elif request.ojson_data_type[i] in ['integer', 'float']:
            request.ojson_schema[i]['attrs']['class'] = 'val'
        elif request.ojson_data_type[i] in ['text']:
            request.ojson_schema[i]['attrs']['class'] = 'inp'
        elif request.ojson_data_type[i] == 'uom':
            request.ojson_schema[i]["type"] = 'char'
            request.ojson_schema[i]['attrs']['class'] = 'uom'

        i += 1

    try:
        result_list = list(request.ojson_data.keys())
        logical_result_list = []
        seen_roots = set()
        for name in result_list:
            root = field_root(name)
            if root not in seen_roots:
                logical_result_list.append(root)
                seen_roots.add(root)

        specified_labels = ut.specified_args(logical_result_list, request.json_doc['info']['out1'], empty_spec='')
        request.json_doc['info']['out1'] = specified_labels
        request.json_doc['info']['output_blocks'] = _normalize_layout_blocks(
            request.json_doc['info'].get('output_blocks', []),
            logical_result_list,
        )
    except Exception as e:
        logger.note(e)
    return
