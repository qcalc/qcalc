# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

# import qsett
from .mod_qcals import QCals
from qcore import qfunc, qdict
import inspect
from qconst import COMBINE_FINF
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
            if dict_class == '@':
                csfunc = val.pop(dict_class)
                unflat_args[arg] = q0164_execute_qfunc(csfunc, val, timeout, pref, request)
            elif dict_class == '#':
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
        spnames = arg.split("--")
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
        # | only qfunc/qdict chained args are sentinel-tagged ('@'/'#') by get_fdef() and
        # | meant to be split into subfields here - a plain dict (e.g. a qtbl default) must
        # | stay a single opaque field value
        if isinstance(val, dict) and next(iter(val), None) in ('@', '#'):
            sqfunc = arg if prefix == '' else prefix + "--" + arg
            flat_dict.update(flatten_fargs(val, prefix=sqfunc))
        else:
            if prefix == '':
                flat_dict[arg] = val
            else:
                flat_dict[prefix + "--" + arg] = val
    return flat_dict


def flatten_finfo(func_args: dict, prefix='') -> dict:
    flat_dict: dict = {}
    for arg, val in func_args.items():
        if isinstance(val, dict) or isinstance(val, list):
            at = next(iter(val))
            if at != '@':
                if arg in COMBINE_FINF:
                    if prefix != '':
                        if isinstance(val, dict):
                            keylist = list(val.keys())
                            for key in keylist:
                                val[prefix + "--" + key] = val.pop(key, None)
                        else:  # list
                            val = [prefix + "--" + key for key in val]  # @28.09.24

                    flat_dict[arg] = val

                    if prefix != '':
                        if arg == 'schema':  # val is dict of fields
                            pass
                        elif arg == 'related':  # val is dict of fields
                            for key in flat_dict[arg]:
                                fields = flat_dict[arg][key]['fields']
                                fields = {prefix + '--' + field: val for field, val in fields.items()}
                                flat_dict[arg][key]['fields'] = fields
                        elif arg in ['showhide', 'autofill', 'anyof']:  # val is dict of fields
                            for key in flat_dict[arg]:
                                fields = flat_dict[arg][key]['fields']
                                fields = [prefix + '--' + field for field in fields]
                                flat_dict[arg][key]['fields'] = fields
                else:
                    if prefix == '':
                        flat_dict[arg] = val
                    else:
                        flat_dict[prefix + "--" + arg] = val
            elif at == '@' and isinstance(val, dict):
                sqfunc = arg if prefix == '' else prefix + "--" + arg
                _ = val.pop('@')
                child_flat_dict = flatten_finfo(val, prefix=sqfunc)
                for key in child_flat_dict:
                    if key in flat_dict:
                        flat_dict[key].update(child_flat_dict[key])
                    else:
                        flat_dict[key] = child_flat_dict[key]
        elif arg == 'script':
            if prefix == '':
                flat_dict[arg] = val.replace('@', '')
            else:
                flat_dict[arg] = val.replace('@', prefix + '--')

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
            qargs[arg] = {'@': fid, **fk}
            annos[arg] = {'@': fid, **fa}
            infs[arg] = {'@': fid, **fi}
        elif ann is not None and ann == qdict:
            fk = flatten_fargs(qargs[arg])
            qargs[arg] = {'#': arg, **fk}
            annos[arg] = {'#': arg}
            infs[arg] = {'#': arg}
    # kwargs = {'func': func, 'kwargs': kwargs}
    return qargs, annos, infs


def call_f(fadr):
    def call_func(fadr, fk, fa):
        for arg in fa:
            # print(arg, fa[arg], type(fa[arg]), type(fa[arg]) == dict)
            if isinstance(fa[arg], dict):
                # print(fk)
                res = call_func(fk[arg]['func'], fk[arg]['args'], fa[arg])
                # print(res)
                fk[arg] = res
                fa[arg] = None
        # print(fk)
        # res = f(**fk)
        res = fadr(**fk)
        return res

    fk, fa, fi = get_fdef(fadr, fadr.__name__)
    res = call_func(fadr, fk, fa)
    return res


def _test():
    from calculators.all.health.cal_fitness import bodyfat
    from calculators.all.others.cal_others import gold

    def callf1(x=10, bf: qfunc = bodyfat, y='3ft'):
        # args={'age': 35, 'sex': 'F'}
        # res = call_f(f) #, args)
        return bf['Body Fat Average (%)']

    def callf2__info():
        return {
            'title': 'callf2',
            'schema': {
                'age': {'label': 'Age in years'},
                'sex': {'label': 'Gender'}
            }
        }

    def callf2(age: float = 35.0, sex='F'):
        kwargs = {'age': 35, 'sex': 'F'}
        return bodyfat(**kwargs)

    def callf3__info():
        return {
            'title': 'callf3',
            'schema': {
                'x': {'label': 'Mars'},
                'y': {'label': 'Venus'}
            },
            'autofill': {
                'fill': {
                    'fields': ['x', 'email'],
                    'autofill': {'1': [10, 'hello@there.com'], '2': [20, 'hi@there.net']}
                }
            },
            'showhide': {'__': {'fields': ['fg--making_charge_pct']}},
        }

    def callf3(fill=1, x=100, email='', f1: qfunc = callf1, fg: qfunc = gold):
        # res3 = call_func(f3) > call_f1, gold > bodyfat
        # print(res3)
        # res2 = call_f(f2)
        return fg['Gold Weight'], f1

    def callf4__info():
        return {
            'title': 'callf4',
            'schema': {
                'x': {'label': 'Factor'},
                'y': {'label': 'Multiplier'}
            }
        }

    def callf4(f3: qfunc = callf3, f1: qfunc = callf1, x='5 ft', y='100.0'):
        return f3, f1

    def tst1():
        res = get_fdef(bodyfat, 'bodyfat')
        print(res)
        res = get_fdef(gold, 'gold')
        print(res)
        res = get_fdef(callf1, 'calf1')
        print(res)
        print(callf2())
        print(call_f(callf2))  # no qfunc - still works
        res = get_fdef(callf2, 'callf2')
        print(res)
        # print(callf)  # has qfunc - hence don't work
        print(call_f(callf1))  # has qfunc - works
        print(call_f(callf3))  # has qfunc - works
        print(call_f(callf4))
        # print(callf4()) # ultimately wont work, when qfunc results are used inside called function
        fa = {'a': 1, 'b': 2, 'c': 3}
        fb = {'x': 11, 'y': 12, 'z': 13, 'f1': {'func': 'fa', 'args': fa}}
        fc = {'u': 21, 'f2': {'func': 'fb', 'args': fb}, 'v': 22, 'w': 23}
        fd = {'xx': 31, 'f3': {'func': 'fc', 'args': fc}, 'yy': 32, 'zz': 33, 'f2': {'func': 'fb', 'args': fb},
              'tt': 34}
        print('---- simplest')
        ff = flatten_fargs(fa)
        uf = q0162_dictify_fargs(ff)
        print(ff)
        print(uf)
        print('----')
        ff = flatten_fargs(fd)
        uf = q0162_dictify_fargs(ff)
        print(ff)
        print(uf)
        ff2 = flatten_fargs(uf)
        uf2 = q0162_dictify_fargs(ff2)
        print(ff2)
        print(uf2)

    def tst_func(faddr, func_id):
        # fargs, fanns, finfs = get_fdef(callf3, 'callf3')
        flat_fargs, flat_fanns, flat_finfs = func_meta(faddr, func_id)
        # print('fargs: ', fargs)
        # flat_fargs = flatten_fargs(fargs)
        print('flat_fargs: ', flat_fargs)
        unflat_flat_fargs = q0162_dictify_fargs(flat_fargs)
        print('unflat_flat_fargs: ', unflat_flat_fargs)
        flat_unflat_flat_fargs = flatten_fargs(unflat_flat_fargs)
        print('flat_unflat_flat_fargs', flat_unflat_flat_fargs)
        # assert(fargs == unflat_flat_fargs)
        assert (flat_unflat_flat_fargs == flat_fargs)
        print('')
        print('flat_fargs: ', flat_fargs)
        # print('fanns: ', fanns)
        # flat_fanns = flatten_fargs(fanns)
        print('flat_fanns: ', flat_fanns)

        # print('finfs: ', finfs)
        # flat_finfs = flatten_finfo(finfs)
        print('flat_finfs: ', flat_finfs)

        """
        fargs:  {'fill': 1, 'x': 100, 'email': '', 'f1': {'@': 'callf1', 'x': 10, 'bf': {'@': 'bodyfat', 'age': '30.0 yr', 'sex': 'M', 'triceps': '7 mm', 'biceps': '5 mm', 'chest': '8 mm', 'subscapular': '4 mm', 'abdominal': '6 mm', 'suprailiac': '10 mm', 'thigh': '8 mm', 'axilla': '3 mm', 'show_details': False}, 'y': '3ft'}, 'fg': {'@': 'gold', 'gold_weight_intl': '10.0 g', 'gold_weight_india': '@vori, @anna, @roti, @point', 'gold_price': '79.0 UNC', 'gold_price_per': 'g', 'vat_pct': 5.0, 'making_charge_pct': 6.0}}
        fanns:  {'fill': None, 'x': None, 'email': None, 'f1': {'@': 'callf1', 'x': None, 'bf': {'@': 'bodyfat', 'age': None, 'sex': None, 'triceps': None, 'biceps': None, 'chest': None, 'subscapular': None, 'abdominal': None, 'suprailiac': None, 'thigh': None, 'axilla': None, 'show_details': None}, 'y': None}, 'fg': {'@': 'gold', 'gold_weight_intl': None, 'gold_weight_india': None, 'gold_price': None, 'gold_price_per': None, 'vat_pct': None, 'making_charge_pct': None}}
        finfs:  {'f1': {'@': 'callf1', 'bf': {'@': 'bodyfat', 'schema': {'sex': {'type': 'radio', 'initial': 'M', 'choices': {'M': 'Male', 'F': 'Female'}}}}}, 'fg': {'@': 'gold', 'schema': {'vat_pct': {'label': 'VAT %'}, 'making_charge_pct': {'label': 'Making Charge %'}}, 'anyof': {'1': {'fields': ['gold_weight_intl', 'gold_weight_india']}}}}

        flat_fargs:  {'fill': 1, 'x': 100, 'email': '', 'f1--@': 'callf1', 'f1--x': 10, 'f1--bf--@': 'bodyfat', 'f1--bf--age': '30.0 yr', 'f1--bf--sex': 'M', 'f1--bf--triceps': '7 mm', 'f1--bf--biceps': '5 mm', 'f1--bf--chest': '8 mm', 'f1--bf--subscapular': '4 mm', 'f1--bf--abdominal': '6 mm', 'f1--bf--suprailiac': '10 mm', 'f1--bf--thigh': '8 mm', 'f1--bf--axilla': '3 mm', 'f1--bf--show_details': False, 'f1--y': '3ft', 'fg--@': 'gold', 'fg--gold_weight_intl': '10.0 g', 'fg--gold_weight_india': '@vori, @anna, @roti, @point', 'fg--gold_price': '79.0 UNC', 'fg--gold_price_per': 'g', 'fg--vat_pct': 5.0, 'fg--making_charge_pct': 6.0}
        flat_fanns:  {'fill': None, 'x': None, 'email': None, 'f1--@': 'callf1', 'f1--x': None, 'f1--bf--@': 'bodyfat', 'f1--bf--age': None, 'f1--bf--sex': None, 'f1--bf--triceps': None, 'f1--bf--biceps': None, 'f1--bf--chest': None, 'f1--bf--subscapular': None, 'f1--bf--abdominal': None, 'f1--bf--suprailiac': None, 'f1--bf--thigh': None, 'f1--bf--axilla': None, 'f1--bf--show_details': None, 'f1--y': None, 'fg--@': 'gold', 'fg--gold_weight_intl': None, 'fg--gold_weight_india': None, 'fg--gold_price': None, 'fg--gold_price_per': None, 'fg--vat_pct': None, 'fg--making_charge_pct': None}
        flat_finfs:  {'schema': {'f1--bf--sex': {'type': 'radio', 'initial': 'M', 'choices': {'M': 'Male', 'F': 'Female'}}, 'fg--vat_pct': {'label': 'VAT %'}, 'fg--making_charge_pct': {'label': 'Making Charge %'}}, 'anyof': {'fg--1': {'fields': ['fg--gold_weight_intl', 'fg--gold_weight_india']}}}

        """

    tst_func(callf2, 'callf2')
    tst_func(callf3, 'callf3')


if __name__ == '__main__':
    _test()
