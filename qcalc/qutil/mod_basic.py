import re
import sys
import os
import qconst


def category_slug(category):
    return category.split(',')[0].lower().replace(' ', '-').replace('(', '').replace(')', '')


def truncate(txt: str, n: int):
    """Limit text to ``n`` characters and mark anything that was shortened.

    Text of length ``n`` or less is returned unchanged. Longer text is cut to
    ``n`` characters and followed by ``'... Truncated'``.
    """
    return txt if len(txt) <= n else (txt[:n] + '... Truncated')


def sort_by_val(vdict: dict) -> dict:
    return dict(sorted(vdict.items(), key=lambda x: x[1]))


def nzs(sval):
    """Return an empty string when ``sval`` is ``None``; otherwise return it unchanged."""
    return '' if sval is None else sval


def iif(condition: bool, truev, falsev):
    """Return ``truev`` when ``condition`` is truthy, otherwise ``falsev``.

    Useful inside calculator expressions where a compact inline conditional is
    clearer than a full ``if`` statement.
    """
    return truev if condition else falsev


def css2strs(cs_string, separator=','):
    """Split separated text into a list of stripped strings.

    Returns input as-is when a list/tuple is already provided.
    """
    if isinstance(cs_string, (list, tuple)): return cs_string
    cs_string = cs_string.strip()
    if cs_string == '': return []
    list_strings = [x.strip() for x in cs_string.split(separator)]
    return list_strings


def replace_words(str_to_replace, words_to_replace, replace_with, case_sensitive=True):
    # words_to_replace is a list of words
    # a word can start with number
    # ref: https://stackoverflow.com/questions/15658187/replace-all-words-from-word-list-with-another-string-in-python
    flags = 0 if case_sensitive else re.IGNORECASE
    # big_regex = re.compile(r'\b%s\b' % r'\b|\b'.join(map(re.escape, words_to_replace)), flags)
    big_regex = re.compile(
        qconst.WORD_LIST_PATTERN % '|'.join(map(re.escape, words_to_replace)),
        flags,
    )
    replaced_str = big_regex.sub(replace_with, str_to_replace)
    return replaced_str


def replace_variables(str_to_replace, variables_dict, case_sensitive=True):
    """Replace variable names in text using values from a dictionary.

    For example, ``replace_variables('length * width', {'length': '4', 'width': '3'})``
    returns ``'4 * 3'``. Replacement values must be strings. Only complete
    variable names are replaced, not matching text inside a longer name.
    Matching is case-sensitive by default; set ``case_sensitive=False`` to
    ignore letter case.
    """
    if case_sensitive:
        lookup = variables_dict
        flags = 0
    else:
        lookup = {k.lower(): v for k, v in variables_dict.items()}
        flags = re.IGNORECASE

    # big_regex = re.compile(r'\b%s\b' % r'\b|\b'.join(map(re.escape, variables_dict)), flags)
    big_regex = re.compile(
        qconst.WORD_LIST_PATTERN % '|'.join(map(re.escape, variables_dict)),
        flags,
    )

    replaced_str = big_regex.sub(
        lambda m: lookup[m.group(0) if case_sensitive else m.group(0).lower()],
        str_to_replace
    )

    return replaced_str


def parameter_values(xpr: str, case_sensitive: bool = False) -> dict:
    """Read named numeric values from a calculator expression.

    ``parameter_values("f(power='1.3 kW', factor=0.8)")`` returns
    ``{'power': 1.3, 'factor': 0.8}``. Quantity units are not included in the
    returned numbers. Parameter names ignore case by default and are converted
    to lowercase; use ``case_sensitive=True`` to preserve and match exact names.
    If a name appears more than once, its first value is used.
    """
    flags = 0 if case_sensitive else re.IGNORECASE
    values = {}
    for match in re.finditer(qconst.PARAMETER_PATTERN, xpr, re.VERBOSE | flags):
        text = match.group('number')
        if text is None:
            text = match.group('quantity').split()[0]
        key = match.group('name') if case_sensitive else match.group('name').lower()
        values.setdefault(key, float(text))
    return values


def replace_parameter_values(
    xpr_to_replace: str,
    parameters_dict: dict,
    case_sensitive: bool = False,
) -> str:
    """Replace named numeric values in a calculator expression.

    ``parameters_dict`` maps parameter names to their new values. Quoted
    quantities keep their original units: replacing ``power`` in
    ``"f(power='1.3 kW', factor=0.8)"`` with ``1.25`` produces
    ``"f(power='1.25 kW', factor=0.8)"``. Parameters absent from the dictionary
    remain unchanged.

    Names ignore case by default. Set ``case_sensitive=True`` to match exact
    spelling. The updated expression is returned as text.
    """

    flags = 0 if case_sensitive else re.IGNORECASE

    pattern = re.compile(qconst.PARAMETER_PATTERN, re.VERBOSE | flags)

    def replace(match):
        name = match.group("name")

        # Find the actual dictionary key, respecting case_sensitive.
        if case_sensitive:
            if name not in parameters_dict:
                return match.group(0)
            key = name
        else:
            key = next(
                (
                    k
                    for k in parameters_dict
                    if k.lower() == name.lower()
                ),
                None,
            )
            if key is None:
                return match.group(0)

        value = parameters_dict[key]

        # Preserve the original unit for quoted quantities.
        if match.group("quantity") is not None:
            quantity = match.group("quantity")

            unit_match = re.search(
                r"""
                [+-]?(?:\d+(?:\.\d*)?|\.\d+)
                (?P<space>\s+)
                (?P<unit>.+)
                """,
                quantity,
                re.VERBOSE,
            )

            if not unit_match:
                return match.group(0)

            unit = unit_match.group("unit")

            return (
                f"{name}"
                f"{match.group(2)}"
                f"{match.group('quote')}"
                f"{value} {unit}"
                f"{match.group('quote')}"
            )

        # Plain numeric parameter.
        return (
            f"{name}"
            f"{match.group(2)}"
            f"{value}"
        )

    return pattern.sub(replace, xpr_to_replace)


def joinx(slist, separator=' '):
    """Join text items without leaving extra separators around blank items.

    ``joinx(['Hello', '', 'world'])`` returns ``'Hello world'`` instead of the
    ``'Hello  world'`` produced by ``' '.join(...)``. The default separator is
    one space; supply ``separator`` to use something else.

    Provide a non-empty list or tuple of strings.
    """
    s1 = slist[0]
    for s2 in slist[1:]:
        spc = separator if s1 != '' and s2 != '' else ''
        s1 = s1 + spc + s2
    return s1


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


def curdir_fullpath(ref_fname, fname, subdir=''):
    dirname = os.path.dirname(ref_fname)
    fullpath = os.path.join(dirname, subdir, fname)
    return fullpath


def xpr_coeffs(xpr):
    """Return the numeric coefficients from a linear expression.

    For example, ``xpr_coeffs('3x - y + 2z')`` returns ``[3.0, -1.0, 2.0]``.
    A variable without a written coefficient has coefficient ``1`` or ``-1``.
    Exponents using ``^`` or ``**`` are rejected with ``ValueError``.
    """
    # xpr('3x-a+2y2-9.5_zZ') or xpr('3,-1,2,-9.5')
    # returns [3,-1,2,-9.5]
    if '**' in xpr or '^' in xpr:
        raise ValueError('Linear expressions must not contain exponents')
    xpr = xpr.replace('*', '').replace(' ', '')
    matches = re.sub(r'[^\W0-9]\w*', ',', xpr).split(',')
    if matches[len(matches) - 1] == '':
        matches = matches[:-1]
    coeffs = []
    # i = 0
    for match in matches:
        if match == '-':
            match = '-1'
        elif match in ('', '+'):
            match = '1'
        coeffs.append(float(match))
    # print(xpr)
    # print(matches)
    # print(coeffs)
    return coeffs


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


def js_string(value) -> str:
    escaped = str(value).replace('\\', '\\\\').replace("'", "\\'").replace('\n', '\\n')
    return f"'{escaped}'"


def _as_list(item) -> list:
    return list(item) if isinstance(item, (list, tuple)) else [item]


def _showhide_condition(values: list) -> str:
    """Inline JS condition, true when the controlling field's value is one of ``values``.

    ``values`` are strings (choice values) or bools (a checkbox).
    """
    var = qconst.SCRIPT_RUNTIME_VAR
    if all(isinstance(v, bool) for v in values):
        return var if values[0] else '!' + var
    if any(isinstance(v, bool) for v in values):
        raise ValueError(f'showhide values cannot mix booleans and strings: {values}')
    values = [str(v) for v in values]
    if any(var in v for v in values):
        raise ValueError(f"showhide values cannot contain '{var}': {values}")
    if len(values) == 1:
        return f'{var}==={js_string(values[0])}'
    return f"[{', '.join(js_string(v) for v in values)}].indexOf({var}) >= 0"


def _showhide_entry(fields: list, conditions: list) -> dict:
    callback = conditions[0] if len(conditions) == 1 else '[' + ', '.join(conditions) + ']'
    return {'fields': fields, 'callback': callback}


def when_show(by_value: dict) -> dict:
    """Choose which fields to show for each value of a controlling field.

    ``'mode': when_show({'File': 'upload', 'URL': 'url', ('A', 'B'): ['x', 'y']})``
    shows ``upload`` for File, ``url`` for URL, and both ``x`` and ``y`` for A
    or B. A tuple key groups several controlling values. Checkbox values can be
    ``True`` or ``False``. Unlisted values hide the fields named here.

    Use ``show_when`` when several values should show the same fields.
    """
    shown = {}  # field -> values showing it, in the order of the first appearance
    for key, fields in by_value.items():
        for field in _as_list(fields):
            shown.setdefault(field, []).extend(_as_list(key))
    return _showhide_entry(list(shown), [_showhide_condition(v) for v in shown.values()])


def show_when(by_field: dict) -> dict:
    """Show fields when a controlling field has selected values.

    ``'method': show_when({'base': '1', 'angle': ['1', '2']})`` shows ``base``
    when method is 1, and ``angle`` when method is 1 or 2. A list or tuple
    groups acceptable values, and checkbox values can be ``True`` or ``False``.

    Use ``when_show`` when each controlling value shows a different set of fields.
    """
    return _showhide_entry(list(by_field), [_showhide_condition(_as_list(v)) for v in by_field.values()])
