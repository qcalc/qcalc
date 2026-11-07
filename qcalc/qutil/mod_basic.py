import re
import sys
import os
import qconst


def category_slug(category):
    return category.split(',')[0].lower().replace(' ', '-').replace('(', '').replace(')', '')


def truncate(txt: str, n: int):
    return txt if len(txt) <= n else (txt[:n] + '... Truncated')


def sort_by_val(vdict: dict) -> dict:
    return dict(sorted(vdict.items(), key=lambda x: x[1]))


def nzs(sval):
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
    """Replace variables in a string using a dictionary of variable/replacement pairs."""
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
    """Read the current numeric value of each parameter in a calculator expression.

    Example:
        "f(power='1.3 kW', factor=0.8)" -> {'power': 1.3, 'factor': 0.8}
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
    """
    Replace parameter values in a calculator expression.

    Examples:
        xpr = (
            "ac_running_cost("
            "power='1.3 kW', "
            "usage='150.0 hr/mo', "
            "electricity_rate='10.0 BDT/kWh', "
            "operating_factor=0.8, "
            "days='30.0 day'"
            ")"
        )

        parameters = {
            "power": 1.25,
            "operating_factor": 0.75,
        }

        result:
            ac_running_cost(
                power='1.25 kW',
                usage='150.0 hr/mo',
                electricity_rate='10.0 BDT/kWh',
                operating_factor=0.75,
                days='30.0 day'
            )
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
    """Join string-like items while skipping separators around blank items.

    Unlike ``separator.join(...)``, this avoids extra separators when adjacent
    values are blank, making it handy for building labels/messages from optional
    parts.

    Example:
    >> joinx(('hello','', 'how','you','?'))
    >> 'hello how you ?'
    >> ' '.join(('hello','', 'how','you','?'))
    >> 'hello how you ?'
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
