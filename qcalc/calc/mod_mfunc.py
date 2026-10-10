# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

# import qsett
from .mod_qcals import QCals
from qcore import qfunc, qdict
import inspect
from qconst import (
    COMBINE_FINF,
    DICT_CLASS_FUNC,
    DICT_CLASS_PLAIN,
    DICT_KEY_SEP,
    SCRIPT_RUNTIME_VAR,
)
from qvars import qfunc_info
from qutil import thread_with_timeout, run_with_timeout, QThread
from qvars import qc_gpref as gs
import platform
import logging

try:
    from django.conf import settings
except Exception:
    settings = None

logger = logging.getLogger(__name__)


def func_meta(func_addr, func_id, __info=None):
    fargs, fanns, finfs = get_fdef(func_addr, func_id, __info)
    __info = __info or fargs.get('__info', None)  # __info from func args, used to control caching
    flat_fargs = flatten_fargs(fargs)
    flat_fanns = flatten_fargs(fanns)
    flat_finfs = flatten_finfo(finfs)

    # Override flat_fargs with values from 'fargs' in flat_finfs
    if 'fargs' in flat_finfs:
        for fld, value in flat_finfs['fargs'].items():
            if fld in flat_fargs:
                flat_fargs[fld] = value

    return flat_fargs, flat_fanns, flat_finfs


def q0164_execute_qfunc(func_id, unflat_args: dict, timeout, pref, request):
    for arg, val in unflat_args.items():
        if isinstance(val, dict):
            dict_class = next(iter(val))
            if dict_class == DICT_CLASS_FUNC:
                csfunc = val.pop(dict_class)
                unflat_args[arg] = q0164_execute_qfunc(csfunc, val, timeout, pref, request)
            elif dict_class == DICT_CLASS_PLAIN:
                _ = val.pop(dict_class)
                unflat_args[arg] = q0164_execute_qfunc(None, val, timeout, pref, request)
            else:
                unflat_args[arg] = val
    if func_id:
        func_addr = QCals.addr(func_id)
        exec_mode = gs['execution_mode']
        # to avoid another threading when get_req() is called inside a function e.g. pref()
        # get_req() obtain request info from current thread local storage, so should run in current thread
        # print(
        #     f'Exec-mode: {exec_mode}, Platform: {platform.system()}, '
        #     f'Timeout: {timeout}, IsolatedUserCode: {user_code}'
        # )
        special_code = func_id in ['pref', 'gpref', 'mycal']  # exec_mode = "0" and "direct"
        # user_code = _is_dynamic_user_calculation(func_id)
        effective_timeout = None if timeout <= 0 else timeout

        system_name = platform.system()
        is_linux = system_name == 'Linux'  # Linux or not
        # is_sqlite = bool('sqlite' in settings.DB_ENGINE.lower())
        if special_code:
            path = 'direct'
        # elif user_code:
        #     if is_sqlite:
        #         path = 'direct'  # user_code with sqlite better run direct
        #     else:
        #         path = 'thread'  # user_code should be run in thread if possible
        elif exec_mode == '0':
            if is_linux and timeout > 0:
                path = 'linux-signal-or-fallback'  # Linux with timeout enabled, exec_mode == "0"
            else:
                path = 'direct'
        elif exec_mode == "1":
            path = 'thread'
        else:
            path = 'direct'

        logger.debug(
            f"Exec path={path}, exec_mode={exec_mode}, timeout={timeout} func_id=%{func_id}",
        )

        if path == 'thread':
            return thread_with_timeout(func_addr, kwargs=unflat_args, timeout=effective_timeout, pref=pref)
        elif path == 'direct':
            # save preferences to main thread local storage to make it available
            # from within the fn() running in main thread
            QThread.set_pref(pref)
            return func_addr(**unflat_args)
        else:
            return run_with_timeout(func_addr, kwargs=unflat_args, timeout=timeout, pref=pref)

    else:
        return unflat_args
    # return result


def q0162_dictify_fargs(flat_func_args: dict) -> dict:
    unflat_dict = {}
    for arg, val in flat_func_args.items():
        spnames = arg.split(DICT_KEY_SEP)
        n = len(spnames)
        if n >= 2:
            unflat = unflat_dict
            for i in range(0, n - 1, 1):
                sqfunc = spnames[i]
                # print(sqfunc)
                if sqfunc not in unflat:
                    # print(sqfunc, unflat, spnames[n - 2], spnames[n - 1], val)
                    unflat[sqfunc] = {}
                unflat = unflat[sqfunc]
            unflat[spnames[n - 1]] = val
        else:
            unflat_dict[arg] = val
    return unflat_dict


def flatten_fargs(func_args: dict, prefix='') -> dict:
    flat_dict = {}
    for arg, val in func_args.items():
        # | only qfunc/qdict chained args are sentinel-tagged by get_fdef() and
        # | meant to be split into subfields here - a plain dict (e.g. a qtbl default) must
        # | stay a single opaque field value
        if isinstance(val, dict) and next(iter(val), None) in (DICT_CLASS_FUNC, DICT_CLASS_PLAIN):
            sqfunc = arg if prefix == '' else prefix + DICT_KEY_SEP + arg
            flat_dict.update(flatten_fargs(val, prefix=sqfunc))
        else:
            if prefix == '':
                flat_dict[arg] = val
            else:
                flat_dict[prefix + DICT_KEY_SEP + arg] = val
    return flat_dict


def flatten_finfo(func_args: dict, prefix='') -> dict:
    flat_dict: dict = {}
    for arg, val in func_args.items():
        if isinstance(val, dict) or isinstance(val, list):
            at = next(iter(val))
            if at != DICT_CLASS_FUNC:
                if arg in COMBINE_FINF:
                    if prefix != '':
                        if isinstance(val, dict):
                            keylist = list(val.keys())
                            for key in keylist:
                                val[prefix + DICT_KEY_SEP + key] = val.pop(key, None)
                        else:  # list
                            val = [prefix + DICT_KEY_SEP + key for key in val]  # @28.09.24

                    flat_dict[arg] = val

                    if prefix != '':
                        if arg == 'schema':  # val is dict of fields
                            pass
                        elif arg == 'related':  # val is dict of fields
                            for key in flat_dict[arg]:
                                fields = flat_dict[arg][key]['fields']
                                fields = {prefix + DICT_KEY_SEP + field: val for field, val in fields.items()}
                                flat_dict[arg][key]['fields'] = fields
                        elif arg in ['showhide', 'autofill', 'anyof']:  # val is dict of fields
                            for key in flat_dict[arg]:
                                fields = flat_dict[arg][key]['fields']
                                fields = [prefix + DICT_KEY_SEP + field for field in fields]
                                flat_dict[arg][key]['fields'] = fields
                else:
                    if prefix == '':
                        flat_dict[arg] = val
                    else:
                        flat_dict[prefix + DICT_KEY_SEP + arg] = val
            elif at == DICT_CLASS_FUNC and isinstance(val, dict):
                sqfunc = arg if prefix == '' else prefix + DICT_KEY_SEP + arg
                _ = val.pop(DICT_CLASS_FUNC)
                child_flat_dict = flatten_finfo(val, prefix=sqfunc)
                for key in child_flat_dict:
                    if key in flat_dict:
                        flat_dict[key].update(child_flat_dict[key])
                    else:
                        flat_dict[key] = child_flat_dict[key]
        elif arg == 'script':
            if prefix == '':
                flat_dict[arg] = val.replace(SCRIPT_RUNTIME_VAR, '')
            else:
                flat_dict[arg] = val.replace(SCRIPT_RUNTIME_VAR, prefix + DICT_KEY_SEP)

    return flat_dict


def get_fdef(func_addr, func_id, __info=None):
    def get_fargs(func_addr):  # arguements
        arg_names = inspect.getfullargspec(func_addr).args
        defaults = inspect.getfullargspec(func_addr).defaults
        if defaults is None:
            defaults = [None] * len(arg_names)
        else:
            defaults = [None] * (len(arg_names) - len(defaults)) + list(defaults)
        kwargs = dict(zip(arg_names, defaults))
        return kwargs

    def get_fanns(func_addr):  # annotations
        params = list(inspect.signature(func_addr).parameters.values())
        anns = {v.name: None if v.annotation == inspect._empty else v.annotation
                for v in params}
        return anns

    def get_finf(func_id, __info):  # info
        # sfunc = func_addr.__name__
        func_info_from_func_def = {}
        try:
            # | start callback point __info (q11429, mod_mfunc.py, line 166)
            # | func__info([__info])
            # | information for form design and initial default input values
            fninfo = QCals.addr(func_id + '__info')
            args_count = len(inspect.signature(fninfo).parameters)

            if args_count == 0:
                func_info_from_func_def = fninfo()
            elif args_count == 1:
                func_info_from_func_def = fninfo(__info)
            # | end exit point
        except:
            pass

        func_info_from_jsonfile = qfunc_info.get(func_id, {})
        func_info_from_func_def.update(func_info_from_jsonfile)

        # delete __info keys not to be combined
        if func_info_from_func_def:
            for key in set(func_info_from_func_def) - COMBINE_FINF:
                del func_info_from_func_def[key]
        return func_info_from_func_def

    qargs = get_fargs(func_addr)
    annos = get_fanns(func_addr)
    infs = get_finf(func_id, __info)

    for arg, ann in annos.items():
        if ann is not None and ann == qfunc:
            fadr_or_id = qargs[arg]
            if isinstance(fadr_or_id, str):
                fid = fadr_or_id
                fadr = QCals.addr(fid)
            else:
                fid = fadr_or_id.__name__
                fadr = fadr_or_id
            fk, fa, fi = get_fdef(fadr, fid)
            qargs[arg] = {DICT_CLASS_FUNC: fid, **fk}
            annos[arg] = {DICT_CLASS_FUNC: fid, **fa}
            infs[arg] = {DICT_CLASS_FUNC: fid, **fi}
        elif ann is not None and ann == qdict:
            fk = flatten_fargs(qargs[arg])
            qargs[arg] = {DICT_CLASS_PLAIN: arg, **fk}
            annos[arg] = {DICT_CLASS_PLAIN: arg}
            infs[arg] = {DICT_CLASS_PLAIN: arg}
    # kwargs = {'func': func, 'kwargs': kwargs}
    return qargs, annos, infs

# Test helpers moved to qcalc/tests/test_mod_mfunc_helpers.py
# See qcalc/tests/test_mod_mfunc_helpers.py for pytest-based tests.
