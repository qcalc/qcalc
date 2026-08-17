# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

# import sett
import inspect


# test layout using tlay0() to tlay4(), ipbal(), ttable(), tcal2(), showhide()


def inarow(func_addr, spec, c4f_fargs=None, incol=True):
    all_args = inspect.getfullargspec(func_addr).args
    spec_arg_list = spec.split('-')  # list of 2 args
    if len(spec_arg_list) == 1:  # 'x'
        spec_arg_list.append(spec_arg_list[0])  # make it as if 'x-x'
    j = 0
    for arg_or_sl in spec_arg_list:
        if arg_or_sl.isdigit():
            spec_arg_list[j] = all_args[int(arg_or_sl) - 1]
        j += 1

    if c4f_fargs is None:
        all_flat_args = all_args
        all_arg_fcnt = {key: 1 for key in all_args}
    else:
        all_flat_args = c4f_fargs['fargs']
        all_arg_fcnt = c4f_fargs['c4f']

    flag_start = 0
    flag_stop = 0
    first_arg = all_flat_args[0]
    div_begin = []
    div_end = []
    last_arg = all_flat_args[-1]
    i = 0
    for arg in all_args:
        start = 0
        n = 0
        qfunc_arg = f"{arg}--@"
        if arg in all_flat_args:
            n = all_arg_fcnt[arg]
            start = all_flat_args.index(arg)
        elif qfunc_arg in all_flat_args:
            n = 0
            qfunc_prefix = f"{arg}--"
            for farg in all_arg_fcnt:
                if farg.startswith(qfunc_prefix):
                    n += all_arg_fcnt[farg]
            start = all_flat_args.index(qfunc_arg)
        arg_components = all_flat_args[start:start + n]

        if flag_start == 0:
            qf_arg_list0 = f"{spec_arg_list[0]}--@"
            if spec_arg_list[0] in arg_components or qf_arg_list0 in arg_components:
                flag_start = 1
                first_arg = arg_components[0]
                # if incol:
                #     div_end.append(arg_components[-1])

        if flag_stop == 0:
            qf_arg_list1 = f"{spec_arg_list[1]}--@"
            if spec_arg_list[1] in arg_components or qf_arg_list1 in arg_components:
                flag_stop = 1
                last_arg = arg_components[-1]
                # if incol:
                #     div_begin.append(arg_components[0])

        if flag_start == 1 or flag_stop == 1:
            if incol:
                # for carg in arg_components[1:-1]:
                for carg in arg_components:
                    div_begin.append(carg)
                    div_end.append(carg)
            else:
                div_begin.append(arg_components[0])
                div_end.append(arg_components[-1])

        if flag_stop == 1:
            break
        i += 1
    return first_arg, div_begin, div_end, last_arg


def layrow(func_addr, rspec, c4f_fargs=None):
    if c4f_fargs and isinstance(rspec, int): rspec = distribute_fields(rspec, c4f_fargs)
    first_arg = []
    margs1 = []
    margs2 = []
    last_arg = []
    for spec in rspec:
        fa, mas1, mas2, la = inarow(func_addr, spec, c4f_fargs, incol=False)
        first_arg.append(fa)
        margs1 += mas1
        margs2 += mas2
        last_arg.append(la)
    return {"newrow": first_arg, "inrowb": margs1, "inrowe": margs2, "endrow": last_arg}


def laycol(f, cspec, c4f_fargs=None):
    # print('c', cspec, c4f_fargs)
    if c4f_fargs and isinstance(cspec, int): cspec = distribute_fields(cspec, c4f_fargs)
    first_arg = []
    last_arg = []
    for spec in cspec:
        fa, mas1, mas2, la = inarow(f, spec, c4f_fargs, incol=True)
        first_arg.append(fa)
        last_arg.append(la)
    # print('"newcol": first_arg, "endcol": last_arg', {"newcol": first_arg, "endcol": last_arg})
    return {"newcol": first_arg, "endcol": last_arg}


# specs {'col':["z-z","w-w"]}
# returns 'newcol':['z','w'], 'endcol':['z','w']

def distribute_fields(ncol, c4f_fargs):
    fargs = list(c4f_fargs['c4f'].keys())
    nflds = len(fargs)
    if nflds == 0: return ['']
    ncol = ncol if ncol<= nflds else nflds
    per_col = nflds // ncol
    remainder = nflds % ncol
    result = []
    start = 1

    for i in range(ncol):
        end = start + per_col - 1
        if remainder > 0:
            end += 1
            remainder -= 1
        if end > nflds:
            end = nflds
        while end < nflds and fargs[end].endswith('_part'):
            end += 1
            remainder -= 1
        result.append(f"{start}-{end}")
        start = end + 1
    # print('d', result, nflds)
    return result


if __name__ == "__main__":
    def ftry(x, y, z, t, u, v, w, p, q, r='2 ft', s=12):
        loc1 = 12
        loc2 = 13
        return


    # specs {'row':["t-v","q-s"]}
    # returns 'newrow':['t','q'], 'endrow':['w','s'],
    # 'inrowb':['t','u','v','q','r','s'],
    # 'inrowe':['t','u_uom','v','q','r_uom','s'],

    def ftry2(x='99 g', y=1, z=2,
              t=3, u='4 ft', v=5,
              w='6g', p=7,
              q=8, r='5 ft', s='',
              a='', b='', c='', d='', e='', f='', g='', h=''):
        return x


    def bf(age='30.0 yr', sex='M',
           triceps='7 mm', biceps='5 mm', chest='8 mm', subscapular='4 mm',
           abdominal='6 mm', suprailiac='10 mm', thigh='8 mm', axilla='3 mm'):
        return


    def bf2(age=30, sex='M',
            triceps=7, biceps=5, chest=8, subscapular=4,
            abdominal=6, suprailiac=10, thigh=8, axilla=3):
        return


    all_args = inspect.getfullargspec(ftry).args
    print(all_args)

    print(1, inarow(ftry, 't-w'))
    print(2, inarow(ftry, 't-x'))
    print(3.1, inarow(ftry, 't-'))
    print(3.2, inarow(ftry, 't'))
    print(3.3, inarow(ftry, 't-t'))
    print(5, inarow(ftry, 'ab'))
    print(6, inarow(ftry, '-t'))

    print(7, layrow(ftry, ["t-w", "q-s"]))
    print(8, laycol(ftry, ["z-v", "w-q"]))

    print(9, layrow(ftry2, ["t-w", "q-s"]))
    print(10, laycol(ftry2, ["b-d", "e-g"]))

    print(11, laycol(bf, ["3-6", "7-10"]))
    print(12, layrow(bf, ["3-6", "7-10"]))
    print(13, laycol(bf2, ["3-6", "7-10"]))
    print(14, layrow(bf2, ["3-6", "7-10"]))

    print(15, laycol(bf2, ["3-3", "7-7"]))

    # Example usage:
    c4f_args = {'c4f':{'a':1,'b':1,'c':1,'d':1,'e':1,'f':1,'aa':1,'bb':1,'cc':1,'dd':1,'ee':1,'ff':1,
    'aaa':1,'bbb':1,'ccc':1,'ddd':1,'eee':1},
    'fargs':['a','b','c','d','e','f','aa','bb','cc','dd','ee','ff','aaa','bbb','ccc','ddd','eee']}
    print(distribute_fields(2, c4f_args))  # Output: ['1-9', '10-17']
    print(distribute_fields(3, c4f_args))  # Output: ['1-6', '7-12', '13-17']

    c4f_args = {'c4f':{'a':2,'b':2,'c':1,'d':1,'e':1,'f':1,'aa':1,'bb':1,'cc':1,'dd':1,'ee':1,'ff':1,
    'aaa':1,'bbb':1,'ccc':1,'ddd':1,'eee':1},
    'fargs':['a','a_uom','b','b_uom','c','d','e','f','aa','bb','cc','dd','ee','ff','aaa','bbb','ccc','ddd','eee']}
    print(distribute_fields(2, c4f_args))  # Output: ['1-9', '10-17']
    print(distribute_fields(3, c4f_args))  # Output: ['1-6', '7-12', '13-17']

    c4f_args = {'c4f':{'a':2,'b':2,'c':1,'c_part':1,'e':1},
    'fargs':['a','a_uom','b','b_uom','c','c_part','e']}
    print(distribute_fields(2, c4f_args))  # Output: ['1-4', '5-5']
    print(distribute_fields(3, c4f_args))  # Output: ['1-2', '3-4', '5-5']

    c4f_args = {'c4f':{'a':6,'d':1},
    'fargs':['a','a_uom','b_part','b_part_uom','c_part','c_part_uom','d']}
    print(distribute_fields(1, c4f_args))  # Output: ['1-2']
    print(distribute_fields(2, c4f_args))  # Output: ['1-1', '2-2']
    print(distribute_fields(4, c4f_args))  # Output: ['1-1', '2-2']

    c4f_args = {'c4f':{}, 'fargs':[]}
    print(distribute_fields(2, c4f_args))  # Output: ['']

    c4f_args = {'c4f':{'a':1}, 'fargs':['a']}
    print(distribute_fields(2, c4f_args))  # Output: ['1-1']
