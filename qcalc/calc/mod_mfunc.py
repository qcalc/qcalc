# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

from .qcatalog.mod_qcals import QCals
from qcore import qfunc, qdict
import copy
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


def func_meta(func_addr, func_id):
    fargs, fanns, finfs = get_fdef(func_addr, func_id)
    flat_fargs = QFuncArgs(fargs).flat
    flat_fanns = QFuncArgs(fanns).flat
    flat_finfs = QFuncInfo(finfs).flat

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
        effective_timeout = None if timeout <= 0 else timeout

        system_name = platform.system()
        is_linux = system_name == 'Linux'  # Linux or not
        if special_code:
            path = 'direct'
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


class QFuncArgs:
    """A function's arguments in both shapes: `.nested` (chained qfunc/qdict args as sub-dicts)
    and `.flat` (one level, keys joined by DICT_KEY_SEP). Each is derived lazily from the other."""

    def __init__(self, nested: dict = None, *, flat: dict = None):
        self._nested = nested
        self._flat = flat

    @property
    def nested(self) -> dict:
        if self._nested is None:
            self._nested = self._unflatten(self._flat)
        return self._nested

    @property
    def flat(self) -> dict:
        if self._flat is None:
            self._flat = self._flatten(self._nested)
        return self._flat

    @staticmethod
    def _unflatten(flat: dict) -> dict:
        nested = {}
        for arg, val in flat.items():
            *parents, name = arg.split(DICT_KEY_SEP)
            node = nested
            for parent in parents:
                node = node.setdefault(parent, {})
            node[name] = val
        return nested

    def _flatten(self, nested: dict, prefix='') -> dict:
        flat = {}
        for arg, val in nested.items():
            # | only qfunc/qdict chained args are sentinel-tagged by get_fdef() and
            # | meant to be split into subfields here - a plain dict (e.g. a qtbl default) must
            # | stay a single opaque field value
            if isinstance(val, dict) and next(iter(val), None) in (DICT_CLASS_FUNC, DICT_CLASS_PLAIN):
                flat.update(self._flatten(val, prefix=prefix + arg + DICT_KEY_SEP))
            else:
                flat[prefix + arg] = val
        return flat


class QFuncInfo(QFuncArgs):
    """`__info()` metadata of a function and its chained qfuncs, `.flat` has every child's field names
    prefixed. Unlike QFuncArgs, this is not reversible: `.nested` is only the given input."""

    def __init__(self, nested: dict):
        super().__init__(copy.deepcopy(nested))  # flattening edits the dicts it walks

    @staticmethod
    def _unflatten(flat: dict) -> dict:
        raise NotImplementedError('flattened function info cannot be nested again')

    def _flatten(self, nested: dict, prefix='') -> dict:
        flat_dict: dict = {}
        for arg, val in nested.items():
            if isinstance(val, dict) or isinstance(val, list):
                at = next(iter(val))
                if at != DICT_CLASS_FUNC:
                    if arg in COMBINE_FINF:
                        if prefix != '':
                            if isinstance(val, dict):
                                keylist = list(val.keys())
                                for key in keylist:
                                    val[prefix + key] = val.pop(key, None)
                            else:  # list
                                val = [prefix + key for key in val]  # @28.09.24

                        flat_dict[arg] = val

                        if prefix != '':
                            if arg == 'schema':  # val is dict of fields
                                pass
                            elif arg == 'related':  # val is dict of fields
                                for key in flat_dict[arg]:
                                    fields = flat_dict[arg][key]['fields']
                                    fields = {prefix + field: val for field, val in fields.items()}
                                    flat_dict[arg][key]['fields'] = fields
                            elif arg in ['showhide', 'autofill', 'anyof', 'reload']:  # val is dict of fields
                                for key in flat_dict[arg]:
                                    fields = flat_dict[arg][key]['fields']
                                    fields = [prefix + field for field in fields]
                                    flat_dict[arg][key]['fields'] = fields
                    else:
                        flat_dict[prefix + arg] = val
                elif at == DICT_CLASS_FUNC and isinstance(val, dict):
                    val.pop(DICT_CLASS_FUNC)
                    child_flat_dict = self._flatten(val, prefix=prefix + arg + DICT_KEY_SEP)
                    for key in child_flat_dict:
                        if key in flat_dict:
                            flat_dict[key].update(child_flat_dict[key])
                        else:
                            flat_dict[key] = child_flat_dict[key]
            elif arg == 'script':
                flat_dict[arg] = val.replace(SCRIPT_RUNTIME_VAR, prefix)

        return flat_dict


def get_fdef(func_addr, func_id):
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

    def get_finf(func_id):  # info
        # sfunc = func_addr.__name__
        func_info_from_func_def = {}
        try:
            # | start callback point __info (q11429, mod_mfunc.py, line 166)
            # | func__info()
            # | information for form design and initial default input values
            info_meta_func = func_id + '__info'
            info_meta_callback = QCals.addr(info_meta_func)  # ()
            func_info_from_func_def = info_meta_callback()
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
    infs = get_finf(func_id)

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
            fk = QFuncArgs(qargs[arg]).flat
            qargs[arg] = {DICT_CLASS_PLAIN: arg, **fk}
            annos[arg] = {DICT_CLASS_PLAIN: arg}
            infs[arg] = {DICT_CLASS_PLAIN: arg}
    # kwargs = {'func': func, 'kwargs': kwargs}
    return qargs, annos, infs


def get_fhelp(func_id):
    # | start callback point __help (q1, mod_cutil.py, line 117)
    # | func__help()
    # | get additional help text if any, will be printed after static help text inside help window
    help_meta_func = func_id + '__help'
    help_meta_callback = QCals.addr(help_meta_func)  # ()
    return help_meta_callback if help_meta_callback else ''

# Test helpers moved to qcalc/tests/test_mod_mfunc_helpers.py
# See qcalc/tests/test_mod_mfunc_helpers.py for pytest-based tests.
