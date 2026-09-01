# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

from titlecase import titlecase
import re
import os
import io
import keyword
import tokenize
import inspect
import qconst
import qvars

fid_separator = '-'  # | '.' doesn't work with select2 field, can't be '_' as need to identify parts

# | DSL words that look like NAME tokens right after a number but aren't units (e.g. "5 to ft")
_non_unit_words = {'to', 'as'}


def insert_implicit_multiply(expr):
    """
    Insert '*' between a number and an immediately following unit/name, e.g.
    '5kg' -> '5*kg', '3.5 m' -> '3.5*m'. Leaves scientific/complex/hex numeric
    literals (3e5, 3j, 0x1A), string contents, and DSL words (to/as/keywords) untouched.
    """
    if '\n' in expr:  # column-offset reconstruction below only supports a single line
        return expr

    try:
        tokens = list(tokenize.generate_tokens(io.StringIO(expr).readline))
    except (tokenize.TokenError, IndentationError, SyntaxError):
        return expr

    skip_types = {
        tokenize.ENCODING, tokenize.ENDMARKER, tokenize.NEWLINE,
        tokenize.NL, tokenize.INDENT, tokenize.DEDENT, tokenize.COMMENT,
    }

    out = []
    last_end = 0
    prev_type = None
    for tok_type, tok_str, start, end, _ in tokens:
        if tok_type in skip_types:
            continue
        gap = expr[last_end:start[1]]
        if (
            prev_type == tokenize.NUMBER
            and tok_type == tokenize.NAME
            and not keyword.iskeyword(tok_str)
            and tok_str not in _non_unit_words
        ):
            gap = gap + '*' if gap else '*'
        out.append(gap)
        out.append(tok_str)
        last_end = end[1]
        prev_type = tok_type
    out.append(expr[last_end:])
    return ''.join(out)


def names2fid(catalog_name, cal_name):
    return cal_name if catalog_name == 'all' else f'{cal_name}{fid_separator}{catalog_name}'


def fid2names(fid):
    names = fid.split(fid_separator)
    catalog_name = names[1] if len(names) > 1 else "all"
    func_name_ = names[0]
    return catalog_name, func_name_


def fid2owner(func_id):
    # | e.g. func_id = func-owner__info, cal_id = func-owner
    cal_id = func_id.split('__')[0]
    names = cal_id.split(fid_separator)
    owner = names[1] if len(names) > 1 else 'qcalc'  # qvars.super_user.username
    # print(func_id, owner, qvars.app_user, qvars.app_user.username)
    cal_name = names[0]
    return cal_id, cal_name, owner


def fid2help_file(func_id):
    catalog, func_name_ = fid2names(func_id)
    help_path = func_name_
    if func_name_.startswith('demo_'):
        help_path = os.path.join('demo', func_name_)

    if catalog != 'all':
        help_file = os.path.join(catalog, f"{help_path}_help.html")
    else:
        help_file = f"{help_path}_help.html"
    return help_file


def preprocess_expression(qexpr, disp=False):  # deb@13.08.23, @25.11.23
    expr_unit = qexpr
    if not disp:  # Before Calculation
        expr_unit = expr_unit.replace('^', '**')  # exponent
        expr_unit = expr_unit.replace('****', '^')  # xor
        expr_unit = insert_implicit_multiply(expr_unit)  # 5kg -> 5*kg
    else:  # Before Displaying
        expr_unit = expr_unit.replace('****', '^^')  # xor
        expr_unit = expr_unit.replace('**', '^')  # exponent
    expr_unit = expr_unit.replace('!', '/')  # browser friendly, can't use | as it is a binary operator
    # | expr_unit = expr_unit.replace('.', '*')  # can't replace (.)  e.g. m*ft^1.5, 1.5*7
    return expr_unit


def title_to_variable(title, data_type=''):
    # __r(esult), __rf(loat), __ri(nt), __rq(ty)
    title = title.replace(': ', '--').replace(' ', '_').lower()
    title = title + data_type
    return title


def doc_title(name):
    var = name.replace('_', ' ').replace('-', ' ').strip()
    var = titlecase(var).replace('Qcalc', 'qCalc')
    return var


def variable_to_title(var):
    var = re.sub(r'__r[a-z]?', '', var).replace('_', ' ').replace('--', ': ')
    var = titlecase(var)
    return var


def vlist2titles(func) -> list:
    # generate a dict with variable title and name from a variable list
    # can be used during returning a list of variables to be output
    titles = []
    params = list(inspect.signature(func).parameters.values())
    for p in params:
        titles.append(variable_to_title(p.name))
    return titles


def path_title(path):
    return path_to_title(path, qconst.name_separator, qconst.separator_display)


def path_to_title(path, separator='/', sep_display=' > '):
    path = path.replace('_', ' ').replace(separator, sep_display)
    path = titlecase(path)
    return path


if __name__ == '__main__':
    print(variable_to_title('gold__rq_uom'))
    assert variable_to_title('gold__rq_uom') == 'Gold Uom'
    print(variable_to_title('gold__rq'))
    assert variable_to_title('gold__rq') == 'Gold'
    print(variable_to_title('count__ri'))
    assert variable_to_title('count__ri') == 'Count'
    print(variable_to_title('age__rf'))
    assert variable_to_title('age__rf') == 'Age'
    print(variable_to_title('name__r'))
    assert variable_to_title('name__r') == 'Name'

    print(title_to_variable('Gold', '__rq'))
    assert title_to_variable('Gold', '__rq') == 'gold__rq'
    print(title_to_variable('Gold', '__rq') + '_uom')
    assert title_to_variable('Gold', '__rq') + '_uom' == 'gold__rq_uom'
    print(title_to_variable('Interest Rate', '__rf'))
    assert title_to_variable('Interest Rate', '__rf') == 'interest_rate__rf'

    print(title_to_variable('Func Xyz: Parameter 1'))
    assert title_to_variable('Func Xyz: Parameter 1') == 'func_xyz--parameter_1'
    print(variable_to_title('func_xyz--parameter_1'))
    assert variable_to_title('func_xyz--parameter_1') == 'Func Xyz: Parameter 1'
    print(fid2names('abc-def'))
    print(fid2names('abc'))

    tests = ['3.5m', '5 to ft', '3.5*m as yd, ft, inch', "bmi(weight='60kg')", '3e5', '0x1A', '1_000', 'x=2ft',
             '3.5m/s to ft/s', '5kg+2g', 'x=1', '3.5 m', '2(3+4)', '3j', 'x==1', '5 in inch', "3.5*m/s"]
    for t in tests:
        print(repr(t), '->', repr(insert_implicit_multiply(t)))
