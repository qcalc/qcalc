# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha
"""Step2 pipeline and IO helpers.

This module owns:
- compacting calculator IO for Step2 persistence,
- Step2 request handling (`run` and `chart`),
- selector parsing (`specified_args` syntax) and dict mapping support.
"""

import json
import pandas as pd
from django.http import JsonResponse
import qutil as ut
from qcore import Qty, QChart, step2_pack_value, step2_unpack_for_run, step2_unpack_for_cost
from qutil import HtmxHttpRequest, QThread
from calc import QIO
from .mod_qcals import QCals
from qcore import QEncoderBase


def calc_io(_request: HtmxHttpRequest):
    """Return all session-scoped Step2 IO payloads for the active request."""
    io_dict = QIO.getp()
    return JsonResponse(io_dict, encoder=QEncoderBase)


def calc_io_clear(_request: HtmxHttpRequest, cid: str):
    """Delete one Step2 IO payload by calculator id (cid)."""
    cid = (cid or '').strip()
    removed = QIO.delp1(cid) if cid else False
    return JsonResponse({'ok': True, 'cid': cid, 'removed': removed}, encoder=QEncoderBase)


def step2_compact_io_payload(func_id, input_map, output_map, *, pack_value=step2_pack_value):
    """Build compact Step2 payload from function input/output maps."""
    return {
        'function': func_id,
        'input': pack_value(input_map or {}),
        'output': pack_value(output_map or {}),
    }


def cache_step2_io(cid, func_id, input_map, output_map, *, pack_value=step2_pack_value):
    """Pack and store Step2 IO payload for one calculator card (`cid`)."""
    payload = step2_compact_io_payload(
        func_id, input_map, output_map, pack_value=pack_value
    )
    QIO.setp1(cid, payload)
    return payload


def _step2_parse_spec(spec_raw):
    text = (spec_raw or '').strip()
    if text == '':
        return ''
    try:
        return json.loads(text)
    except Exception:
        return text


def _step2_select_keys(mapping, spec, *, empty_spec='*'):
    if not isinstance(mapping, dict):
        return []
    if isinstance(spec, dict):
        return list(mapping.keys())
    return ut.specified_args(list(mapping.keys()), spec, empty_spec=empty_spec)


def _step2_prepare_cost_items(output_map, spec):
    output = output_map.copy() if isinstance(output_map, dict) else {}
    selected_keys = _step2_select_keys(output, spec, empty_spec='*')
    output = {key: output[key] for key in selected_keys if key in output}

    keys = [key for key in output.keys()]
    for key in keys:
        qval = step2_unpack_for_cost(output[key])
        if not isinstance(qval, Qty):
            _ = output.pop(key)
            continue

        output[key] = qval
        dim = qval.unit.dimension
        if 'C' in dim:
            _ = output.pop(key)

    if not output:
        return None

    user_curnc = QThread.get_pref('defa_currency', 'USD')
    ucost = ['1.00 ' + user_curnc + '/' + q.uom for q in output.values()]
    return pd.DataFrame({'Item': output.keys(), 'Quantity': output.values(), 'Unit Cost': ucost})


def q1_step2(request: HtmxHttpRequest, open_func=None):
    """Execute Step2 action for a calculator card."""
    if open_func is None:
        from .views import q1999_func_to_form
        open_func = q1999_func_to_form
    fstep = request.GET.get('step', "").strip().lower()  # run, chart
    fname = request.GET.get('func', "").strip().lower()  # run function name
    fcid = request.GET.get('src_cid', "").strip()  # source cid may not have been used, collected from html
    fspec = _step2_parse_spec(request.GET.get('spec', ''))
    # | spec supports:
    # | 1) run mapping dict: {'dest_arg': 'source_field'}
    # | 2) selector syntax accepted by specified_args(): 'weight,height' / '~skip_this'
    step2_io = QIO.getp1(fcid, {}) if fcid else {}
    if not isinstance(step2_io, dict):
        step2_io = {}
    output = step2_io.get('output', {})
    output = output.copy() if isinstance(output, dict) else {}

    if fstep == 'run':
        ff = QCals.quick_find_func(fname)
        input_ = step2_io.get('input', {})
        input_ = input_ if isinstance(input_, dict) else {}
        run_input = {key: step2_unpack_for_run(val) for key, val in input_.items()}
        run_output = {key: step2_unpack_for_run(val) for key, val in output.items()}
        io = {**run_input, **run_output}
        fargs = {}
        if isinstance(fspec, dict):
            for arg_key, src_key in fspec.items():
                if not isinstance(arg_key, str) or not isinstance(src_key, str):
                    continue
                arg_name = arg_key.strip()
                src_name = src_key.strip()
                if arg_name and src_name in io:
                    fargs[arg_name] = io[src_name]
        else:
            selected_keys = _step2_select_keys(io, fspec, empty_spec='')
            mapped_from = {}
            for src_key in selected_keys:
                arg_key = ut.title_to_variable(src_key)
                if arg_key in fargs and mapped_from[arg_key] != src_key:
                    raise Exception(
                        f"Error (S2): Ambiguous selector maps both '{mapped_from[arg_key]}' and "
                        f"'{src_key}' to argument '{arg_key}'"
                    )
                fargs[arg_key] = io[src_key]
                mapped_from[arg_key] = src_key

        # Allow step='run', func='cost' to use selector filtering + Qty-to-items behavior.
        if ff == 'cost' and 'items' not in fargs:
            items_df = _step2_prepare_cost_items(output, fspec)
            if items_df is None:
                return ut.show_modal(request, "Next Step", 'Error (S2): No suitable Qty found to calculate cost')
            fargs['items'] = items_df

        return open_func(request, fname=ff, fargs=fargs, part='1')

    if output:
        if isinstance(fspec, dict) and 'field' in fspec and isinstance(fspec.get('field'), str):
            selected_keys = ut.specified_args(list(output.keys()), fspec.get('field', ''), empty_spec='')
        else:
            selected_keys = _step2_select_keys(output, fspec, empty_spec='*')
        if fstep == 'chart':
            for key in selected_keys:
                if key not in output:
                    continue
                if isinstance(output[key], QChart):
                    return open_func(request, fname=output[key].chtype, fargs=output[key].data, part='1')
                if isinstance(output[key], dict) and output[key].get('__qcalc_type') == 'chart':
                    chtype = output[key].get('chtype', '')
                    cdata = output[key].get('data', {})
                    if chtype and isinstance(cdata, dict):
                        return open_func(request, fname=chtype, fargs=cdata, part='1')
            msg = f'No data found for Chart'
        else:
            msg = f'Unknown step2 step [{fstep}]'
    else:
        msg = f'Output not found, please recalculate'

    return ut.show_modal(request, "Next Step", f'Error (S2): {msg}')
