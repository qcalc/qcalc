# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

import sys
import re
import os
import bisect
from qutil.mod_data import str2type, time2float
from datetime import date, datetime, time as dt_time


def category_slug(category):
    return category.split(',')[0].lower().replace(' ', '-').replace('(', '').replace(')', '')


def iif(condition: bool, truev, falsev):
    return truev if condition else falsev


def idx2names(id_or_names: str, all_args: list[str]) -> list:
    # idx2name('x,y,3,4,z,?',['a','b','c','d','x','y','z']) = ['x','y','c','d','z','?']
    j = 0
    spec_arg_list = css2strs(id_or_names)
    for arg_or_sl in spec_arg_list:
        if arg_or_sl.isdigit():
            spec_arg_list[j] = all_args[int(arg_or_sl) - 1]
        j += 1
    return spec_arg_list


def truncate(txt: str, n: int):
    return txt if len(txt) <= n else (txt[:n] + '... Truncated')


def joinx(slist, separator=' '):
    """
    # >>> joinx(('hello','', 'how','you','?'))
    # >>> 'hello how you ?'
    # >>> ' '.join(('hello','', 'how','you','?'))
    # >>> 'hello how you ?'
    """
    s1 = slist[0]
    for s2 in slist[1:]:
        spc = separator if s1 != '' and s2 != '' else ''
        s1 = s1 + spc + s2
    return s1


def quick_find(list_: list, find: str):
    idx = bisect.bisect_left(list_, find)
    if idx < len(list_) and list_[idx] == find:
        return list_[idx]
    return None


def sort_by_key(vdict: dict) -> dict:
    keys = list(vdict.keys())
    keys.sort()
    return {k: vdict[k] for k in keys}


def sort_by_val(vdict: dict) -> dict:
    return dict(sorted(vdict.items(), key=lambda x: x[1]))


def nzv(nval):
    return 0 if nval is None else nval


def nzs(sval):
    return '' if sval is None else sval


def vals2css(vals: list, separator=', '):
    return separator.join(map(str, vals))


def css2values(cs_string, separator=',', time2val='hr'):  # '', ('hr','min','s', 'ms', or 'mics')
    if isinstance(cs_string, list): return cs_string, type(cs_string[0]) if len(cs_string) > 0 else float
    cs_string = cs_string.strip()
    if cs_string == '': return [], float
    list_values = []
    try:
        list_strings = [x.strip() for x in cs_string.split(separator)]
        data_type = str2type(list_strings[0])
        if data_type == float:
            list_values = [float(x) for x in list_strings]
        elif data_type == int:
            list_values = [int(x) for x in list_strings]
        elif data_type == date:
            list_values = [date.fromisoformat(x) for x in list_strings]
        elif data_type == datetime:
            list_values = [datetime.fromisoformat(x) for x in list_strings]
        elif data_type == dt_time:
            if time2val == '':
                list_values = [dt_time.fromisoformat(x) for x in list_strings]
            else:
                list_values = [time2float(dt_time.fromisoformat(x), time2val) for x in list_strings]
                data_type = float
        elif data_type == str:
            list_values = list_strings
    except ValueError as e:
        raise ValueError(f"Error (C2V): Input issue: {e}")
    # print('l', list_values, data_type)
    return list_values, data_type


def css2strs(cs_string, separator=','):
    if isinstance(cs_string, (list, tuple)): return cs_string
    cs_string = cs_string.strip()
    if cs_string == '': return []
    list_strings = [x.strip() for x in cs_string.split(separator)]
    return list_strings


def css2floats(cs_string, separator=','):
    if isinstance(cs_string, list): return cs_string
    cs_string = cs_string.strip()
    if cs_string == '': return []
    list_floats = [float(x.strip()) for x in cs_string.split(separator)]
    return list_floats


def css2ints(cs_string, separator=','):
    if isinstance(cs_string, list): return cs_string
    cs_string = cs_string.strip()
    if cs_string == '': return []
    list_ints = [int(float(x.strip())) for x in cs_string.split(separator)]
    return list_ints


def curdir_fullpath(ref_fname, fname, subdir=''):
    dirname = os.path.dirname(ref_fname)
    fullpath = os.path.join(dirname, subdir, fname)
    return fullpath


def xpr_coeffs(xpr):
    # xpr('3x-a+2y2-9.5_zZ') or xpr('3,-1,2,-9.5')
    # returns [3,-1,2,-9.5]
    matches = re.sub(r'[^\W0-9]\w*', ',', xpr).split(',')
    if matches[len(matches) - 1] == '':
        matches = matches[:-1]
    coeffs = []
    # i = 0
    for match in matches:
        if match == '-':
            match = '-1'
        elif match == '':
            match = '1'
        coeffs.append(float(match))
    # print(xpr)
    # print(matches)
    # print(coeffs)
    return coeffs


def replace_words(str_to_replace, words_to_replace, replace_with, case_sensitive=True):
    # words_to_replace is a list of words
    # a word can start with number
    # ref: https://stackoverflow.com/questions/15658187/replace-all-words-from-word-list-with-another-string-in-python
    flags = 0 if case_sensitive else re.IGNORECASE
    big_regex = re.compile(r'\b%s\b' % r'\b|\b'.join(map(re.escape, words_to_replace)), flags)
    replaced_str = big_regex.sub(replace_with, str_to_replace)
    return replaced_str


def key_val(spath):
    # ref: https://stackoverflow.com/questions/28128942/
    # multiple-url-key-value-pair-parameters-that-are-optional-in-django
    # key1/value1/key2/value2

    bits = spath.split('/')
    it = iter(bits)
    kvdict = dict(zip(it, it))
    return kvdict


def docstring_to_html(docstring):
    # Split the docstring into lines
    lines = docstring.split('\n')

    # Initialize HTML content list
    html_lines = []

    in_params_section = False

    for line in lines:
        stripped_line = line.strip()

        # Check for the "Parameters:" section
        if stripped_line.lower() == 'parameters:':
            html_lines.append('<dl><dt><strong>Parameters:</strong></dt>')
            in_params_section = True
            continue

        # Check if we're in the parameters section and line is a parameter definition
        if in_params_section:
            param_match = re.match(r':param\s+(\w+)\s*:\s*(.*)', stripped_line)
            if param_match:
                param_name, param_desc = param_match.groups()
                html_lines.append(f'<dd><strong>{param_name}</strong> → {param_desc}</dd>')
                continue
            else:
                # If the line is not a parameter definition, close the definition list
                in_params_section = False
                html_lines.append('</dl>')

        # Convert to paragraph or line break
        if stripped_line:
            html_lines.append('<p>' + stripped_line + '</p>')
        else:
            html_lines.append('<br>')

    # If we ended while still in the parameters section, close the definition list
    if in_params_section:
        html_lines.append('</dl>')

    # Join the lines into a single string
    html_content = '\n'.join(html_lines)

    return html_content


def doctrim(docstring):
    if not docstring:
        return ''
    # Convert tabs to spaces (following the normal Python rules)
    # and split into a list of lines:
    lines = docstring.expandtabs().splitlines()
    # Determine minimum indentation (first line doesn't count):
    indent = sys.maxsize
    for line in lines[1:]:
        stripped = line.lstrip()
        if stripped:
            indent = min(indent, len(line) - len(stripped))
    # Remove indentation (first line is special):
    trimmed = [lines[0].strip()]
    if indent < sys.maxsize:
        for line in lines[1:]:
            trimmed.append(line[indent:].rstrip())
    # Strip off trailing and leading blank lines:
    while trimmed and not trimmed[-1]:
        trimmed.pop()
    while trimmed and not trimmed[0]:
        trimmed.pop(0)
    # Return a single string:
    return '\n'.join(trimmed)


def fchoices(vchoices):
    # transform to [(1, 'a'), (2, 'b'), (3, 'c')]
    if isinstance(vchoices, dict):
        # {1: 'a', 2: 'b', 3: 'c'}
        return list(vchoices.items())
    elif isinstance(vchoices, (list, tuple)):
        if vchoices and isinstance(vchoices[0], (list, tuple)):
            # ((1, 'a'), (2, 'b'), (3, 'c'))
            # [(1, 'a'), (2, 'b'), (3, 'c')]
            return list(vchoices)
        elif vchoices and isinstance(vchoices[0], dict):
            # [{'name': 'a', 'value': 1}, {'name': 'b', 'value': 2}, {'name': 'c', 'value': 3}]
            return [(c['value'], c['name']) for c in vchoices]
        else:
            # ['a', 'b', 'c']
            return [(v, v) for v in vchoices]
    elif isinstance(vchoices, set):
        # {'a', 'b', 'c'}
        return [(v, v) for v in vchoices]
    else:
        return []


if __name__ == '__main__':
    def _test():
        print(fchoices({1: 'a', 2: 'b', 3: 'c'}))
        print(fchoices(((1, 'a'), (2, 'b'), (3, 'c'))))
        print(fchoices([(1, 'a'), (2, 'b'), (3, 'c')]))
        print(fchoices([{'name': 'a', 'value': 1}, {'name': 'b', 'value': 2}, {'name': 'c', 'value': 3}]))
        print(fchoices(['a', 'b', 'c']))
        print(fchoices({'a', 'b', 'c'}))
        print(idx2names('x,y,3,4,z,?', ['a', 'b', 'c', 'd', 'x', 'y', 'z']))
        # ['x', 'y', 'c', 'd', 'z', '?']
        print(replace_words('km/usd', ['USD'], 'bdt'))
        print(replace_words('km/uSd', ['USD'], 'bdt', False))
        print(css2strs([1, 2, 3]))  # list
        print(css2strs('1, 2, 3'))  # string
        print(css2strs((1, 2, 3)))  # touple
        # print(css2strs({1, 2, 3})) # set


    _test()
