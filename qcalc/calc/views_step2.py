# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha
"""Step2 pipeline and IO helpers.

This module owns:
- compacting calculator IO for Step2 persistence,
- Step2 request handling (`run` and `chart`),
- selector parsing (`specified_args` syntax) and dict mapping support.
"""

import json
from django.http import JsonResponse
import qutil as ut
from qcore import QChart, step2_pack_value, step2_unpack_for_run
from qutil import HtmxHttpRequest
from calc import QIO
from .qcatalog.mod_qcals import QCals
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


class QBridge:
    """Cross-calculator action helpers for mapping input/output data and dispatching actions."""

    @staticmethod
    def parse_spec(spec_raw):
        text = (spec_raw or '').strip()
        if text == '':
            return ''
        try:
            return json.loads(text)
        except Exception:
            return text

    @staticmethod
    def select_keys(mapping, spec, *, empty_spec='*'):
        if not isinstance(mapping, dict):
            return []
        if isinstance(spec, dict):
            return list(mapping.keys())
        return ut.specified_args(list(mapping.keys()), spec, empty_spec=empty_spec)

    @staticmethod
    def source_map(step2_io, source='both'):
        source = (source or 'both').strip().lower()
        step2_io = step2_io if isinstance(step2_io, dict) else {}
        input_ = step2_io.get('input', {})
        output = step2_io.get('output', {})
        input_ = input_ if isinstance(input_, dict) else {}
        output = output if isinstance(output, dict) else {}
        run_input = {key: step2_unpack_for_run(val) for key, val in input_.items()}
        run_output = {key: step2_unpack_for_run(val) for key, val in output.items()}
        if source == 'input':
            return run_input
        if source == 'output':
            return run_output
        return {**run_input, **run_output}

    @staticmethod
    def map_args(mapping, spec):
        if not isinstance(mapping, dict):
            return {}
        fargs = {}
        if isinstance(spec, dict):
            for arg_key, src_key in spec.items():
                if not isinstance(arg_key, str) or not isinstance(src_key, str):
                    continue
                arg_name = arg_key.strip()
                src_name = src_key.strip()
                if arg_name and src_name in mapping:
                    fargs[arg_name] = mapping[src_name]
            return fargs

        selected_keys = QBridge.select_keys(mapping, spec, empty_spec='')
        mapped_from = {}
        for src_key in selected_keys:
            arg_key = ut.title_to_variable(src_key)
            if arg_key in fargs and mapped_from[arg_key] != src_key:
                raise Exception(
                    f"Error (S2): Ambiguous selector maps both '{mapped_from[arg_key]}' and "
                    f"'{src_key}' to argument '{arg_key}'"
                )
            fargs[arg_key] = mapping[src_key]
            mapped_from[arg_key] = src_key
        return fargs


def q1_step2(request: HtmxHttpRequest, open_func=None):
    """Execute Step2 action for a calculator card."""
    if open_func is None:
        from .views import q1999_func_to_form
        open_func = q1999_func_to_form
    data = request.POST if request.method == 'POST' else request.GET
    fstep = data.get('step', "").strip().lower()  # run, open, chart
    fname = data.get('func', "").strip().lower()
    fcid = (data.get('src_cid', "") or data.get('cid', "")).strip()
    fsource = data.get('source', 'both')
    fspec = QBridge.parse_spec(data.get('spec', ''))
    # | spec supports:
    # | 1) run mapping dict: {'dest_arg': 'source_field'}
    # | 2) selector syntax accepted by specified_args(): 'weight,height' / '~skip_this'
    step2_io = QIO.getp1(fcid, {}) if fcid else {}
    step2_io = step2_io if isinstance(step2_io, dict) else {}
    output = step2_io.get('output', {})
    output = output.copy() if isinstance(output, dict) else {}

    if fstep in ('run', 'open'):
        ff = QCals.quick_find_func(fname)
        source_map = QBridge.source_map(step2_io, source=fsource)
        fargs = QBridge.map_args(source_map, fspec)
        return open_func(request, fname=ff, fargs=fargs, part='1')

    if output:
        if isinstance(fspec, dict) and 'field' in fspec and isinstance(fspec.get('field'), str):
            selected_keys = ut.specified_args(list(output.keys()), fspec.get('field', ''), empty_spec='')
        else:
            selected_keys = QBridge.select_keys(output, fspec, empty_spec='*')
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
