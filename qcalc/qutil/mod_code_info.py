# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

"""Draft generator for calculator ``<name>__info()`` metadata.

The engine is pure Python: it only parses source text with ``ast`` and never imports or executes it.

Input is a function signature, a whole function or a whole module (with ``hints['func_name']``).
Output is an ``InfoResult`` with the ``__info`` spec, ready to paste Python code and warnings for
the things that could not be inferred.

Inference layers:
1. Signature: a non-None default already gives qcalc the field type and initial value, so the schema only
   gets type/initial for arguments without one (toggle/percent names, choices) or when explicitly asked.
2. Names: ``*_enabled`` / ``enable_*`` toggles form feature groups (tabs and show/hide) from
   token matches and argument adjacency; ``table_<arg>`` helpers are matched by name.
   Show/hide callbacks are inline expressions (``'@'``, ``"@==='x'"``, or one expression per field
   in a list), so no ``script`` is generated.
3. Body: comparisons such as ``arg == 'x'`` or ``arg in ('a', 'b')`` give choices;
   ``return {...}`` keys give output names.
4. Overrides and hints supplied by the caller always win.
"""

import ast
import math
import re
from dataclasses import dataclass, field

from .mod_func import variable_to_title
__all__ = ['InfoResult', 'build_info']

TABLE_ANNOTATIONS = {'qtable', 'qtbl'}
SKIP_ANNOTATIONS = {'qfunc', 'qhide', 'qhidex'}
TOGGLE_NAME = re.compile(r'(?:enable_|use_|show_|is_|has_|allow_|include_)|(?:_enabled|_enable|_flag)$')
CONTROLLER_PATTERNS = (
    (re.compile(r'(.+)_enabled$'), 3),
    (re.compile(r'(.+)_enable$'), 3),
    (re.compile(r'enable_(.+)$'), 2),
    (re.compile(r'use_(.+)$'), 1),
)
COMMON_NAME = re.compile(r'(?:show_|display_|verbose|debug|seed)')
CHOICE_NAME = re.compile(r'(?:^objective$|_type$|_policy$|_mode$|_method$|_strategy$|_kind$)')
PERCENT_NAME = re.compile(r'(?:_pct|_percent|_ratio|_rate)$')
RULE_PATTERN = re.compile(r'^\s*(\w+)\s*(==|!=|not\s+in|in)\s*(.+?)\s*$')

INDENT = '    '
INLINE_LIMIT = 70
MIN_OUTPUTS_FOR_TABS = 4
_MISSING = object()


@dataclass
class InfoResult:
    func_name: str
    spec: dict
    code: str
    warnings: list = field(default_factory=list)


class _Raw(str):
    """Source text emitted as is by the code renderer."""


@dataclass
class _Arg:
    name: str
    annotation: str | None
    default: object = _MISSING  # _MISSING: no default, None allowed as a real default
    default_known: bool = True

    @property
    def has_default(self):
        return self.default is not _MISSING

    @property
    def is_table(self):
        return self.annotation in TABLE_ANNOTATIONS

    @property
    def is_toggle(self):
        if self.annotation in ('bool', 'boolean'):
            return True
        if self.annotation is not None:
            return False
        if isinstance(self.default, bool):
            return True
        return (not self.has_default or self.default is None) and bool(TOGGLE_NAME.search(self.name))


def _make_titler(proper):
    """Title function using qcalc's variable_to_title plus the calculator's ``proper`` words."""
    proper_dict = {w.lower(): w for w in _list_hint(proper)}
    return lambda text: variable_to_title(str(text).strip(), proper_dict)


def _stem(token):
    if len(token) > 3 and token.endswith('s') and not token.endswith('ss'):
        return token[:-1]
    return token


def _tokens(name):
    return [_stem(t) for t in name.lower().split('_') if t]


def _is_blank(value):
    if value is None:
        return True
    if isinstance(value, float) and math.isnan(value):
        return True
    return isinstance(value, str) and not value.strip()


def _truthy(value):
    return str(value).strip().lower() in ('1', 'true', 'yes', 'y', 'on')


# --------------------------------------------------------------------------- parsing

def _parse_tolerant(source, func_name):
    """Parse a module, a function, or a signature written as ``def f(x)``, ``f(x)``, ``f(x):`` or ``x, y=1``."""
    text = source.strip('\n').rstrip()
    if re.search(r'^\s*(?:async\s+)?def\s', text, re.M):
        base = text
    elif re.match(r'\w+\s*\(', text):  # "f(x, y=1)" without def
        base = 'def ' + text
    else:  # a bare argument list such as "x, y=1"
        base = f"def {func_name or 'calculator'}({text.strip()})"
    # as written, then with a body, then with a missing colon and a body
    candidates = [base, base + '\n    pass\n', base.rstrip().rstrip(':') + ':\n    pass\n']
    last_error = None
    for candidate in candidates:
        try:
            tree = ast.parse(candidate)
        except SyntaxError as e:
            last_error = e
            continue
        if any(isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) for n in tree.body):
            return tree
    raise ValueError(
        f'Error (CIN): Cannot parse the function signature or source: {last_error or "no function found"}'
    )


def _select_function(tree, func_name):
    funcs = [n for n in tree.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
    if func_name:
        for node in funcs:
            if node.name == func_name:
                return node
        raise ValueError(f"Error (CIN): Function '{func_name}' is not defined in the source")
    names = [f.name for f in funcs]
    info_owners = [n[:-6] for n in names if n.endswith('__info')]
    if len(info_owners) == 1 and info_owners[0] in names:
        return funcs[names.index(info_owners[0])]
    plain = [f for f in funcs if '__' not in f.name]
    if len(plain) == 1:
        return plain[0]
    if not plain:
        raise ValueError('Error (CIN): No function is defined in the source')
    raise ValueError(
        f"Error (CIN): Cannot determine the calculator function from {[f.name for f in plain]}. "
        "Specify the function name."
    )


def _annotation_name(node):
    if node is None:
        return None
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value.split('.')[-1]
    text = ast.unparse(node)
    return text.split('[')[0].split('.')[-1]


def _literal(node):
    try:
        return ast.literal_eval(node), True
    except Exception:
        return None, False


def _extract_args(func_node):
    spec = func_node.args
    positional = spec.posonlyargs + spec.args
    defaults = [None] * (len(positional) - len(spec.defaults)) + list(spec.defaults)
    pairs = list(zip(positional, defaults)) + list(zip(spec.kwonlyargs, spec.kw_defaults))
    args = []
    for node, default_node in pairs:
        arg = _Arg(node.arg, _annotation_name(node.annotation))
        if default_node is not None:
            arg.default, arg.default_known = _literal(default_node)
        args.append(arg)
    return args


def _docstring_help(doc, name):
    if not doc:
        return None
    pattern = re.compile(
        rf'^\s*(?:[-*]\s*)?(?::param\s+)?{re.escape(name)}\s*(?:\([^)]*\))?\s*:\s*(\S.*)$', re.M
    )
    match = pattern.search(doc)
    return match.group(1).strip() if match else None


def _docstring_desc(doc):
    if not doc:
        return ''
    first = doc.strip().split('\n\n')[0]
    return ' '.join(first.split())


# --------------------------------------------------------------------------- body scans

def _target_name(expr):
    """Name behind wrappers such as str(x).strip().lower()."""
    while True:
        if isinstance(expr, ast.Name):
            return expr.id
        if isinstance(expr, ast.Call):
            if isinstance(expr.func, ast.Attribute):
                expr = expr.func.value
            elif expr.args:
                expr = expr.args[0]
            else:
                return None
        elif isinstance(expr, ast.Attribute):
            expr = expr.value
        else:
            return None


def _string_values(node):
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return [node.value]
    if isinstance(node, (ast.Tuple, ast.List, ast.Set)):
        values = []
        for item in node.elts:
            if isinstance(item, ast.Constant) and isinstance(item.value, str):
                values.append(item.value)
        return values
    return []


def _scan_choices(tree, arg_names):
    """Collect string literals compared with each argument in functions that take that argument."""
    found = {name: [] for name in arg_names}
    for fn in ast.walk(tree):
        if not isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        params = {a.arg for a in fn.args.posonlyargs + fn.args.args + fn.args.kwonlyargs}
        wanted = params & set(arg_names)
        if not wanted:
            continue
        for node in ast.walk(fn):
            if not isinstance(node, ast.Compare):
                continue
            operands = [node.left] + list(node.comparators)
            for index, op in enumerate(node.ops):
                if not isinstance(op, (ast.Eq, ast.NotEq, ast.In, ast.NotIn)):
                    continue
                left, right = operands[index], operands[index + 1]
                for expr, other in ((left, right), (right, left)):
                    name = _target_name(expr)
                    if name in wanted:
                        for value in _string_values(other):
                            if value and value not in found[name]:
                                found[name].append(value)
    return found


def _walk_own(func_node):
    """Walk a function body without descending into nested functions, lambdas or classes."""
    stack = list(reversed(func_node.body))
    while stack:
        node = stack.pop()
        yield node
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda, ast.ClassDef)):
            continue
        stack.extend(reversed(list(ast.iter_child_nodes(node))))


def _scan_outputs(func_node):
    returned = set()
    keys = []

    def add(key):
        if key not in keys:
            keys.append(key)

    own = list(_walk_own(func_node))
    for node in own:
        if isinstance(node, ast.Return) and node.value is not None:
            if isinstance(node.value, ast.Name):
                returned.add(node.value.id)
            elif isinstance(node.value, ast.Dict):
                for key in node.value.keys:
                    if isinstance(key, ast.Constant) and isinstance(key.value, str):
                        add(key.value)
    for node in own:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Subscript) and isinstance(target.value, ast.Name) \
                        and target.value.id in returned \
                        and isinstance(target.slice, ast.Constant) and isinstance(target.slice.value, str):
                    add(target.slice.value)
                elif isinstance(target, ast.Name) and target.id in returned and isinstance(node.value, ast.Dict):
                    for key in node.value.keys:
                        if isinstance(key, ast.Constant) and isinstance(key.value, str):
                            add(key.value)
    return keys


# --------------------------------------------------------------------------- overrides and hints

_OVERRIDE_KEYS = {
    'arg': 'arg', 'argument': 'arg', 'name': 'arg',
    'label': 'label',
    'help': 'help_text', 'help_text': 'help_text',
    'choices': 'choices',
    'group': 'group', 'tab': 'group',
    'show_when': 'show_when', 'showwhen': 'show_when',
    'type': 'type',
    'initial': 'initial', 'default': 'initial',
}


def _normalize_overrides(overrides):
    if not overrides:
        return {}
    rows = [dict(v, arg=k) for k, v in overrides.items()] if isinstance(overrides, dict) else list(overrides)
    result = {}
    for row in rows:
        clean = {}
        for key, value in dict(row).items():
            norm = _OVERRIDE_KEYS.get(re.sub(r'[\s-]+', '_', str(key).strip().lower()))
            if norm and not _is_blank(value):
                clean[norm] = value.strip() if isinstance(value, str) else value
        name = clean.pop('arg', None)
        if name and clean:
            result[str(name)] = clean
    return result


def _parse_choices(value, title):
    if _is_blank(value):
        return {}
    if isinstance(value, dict):
        return {str(k): str(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return {str(v): title(v) for v in value}
    choices = {}
    for item in re.split(r'[,;\n]', str(value)):
        item = item.strip()
        if not item:
            continue
        key, sep, label = item.partition('=')
        key = key.strip()
        choices[key] = label.strip() if sep and label.strip() else title(key)
    return choices


def _parse_initial(value):
    if isinstance(value, str):
        try:
            return ast.literal_eval(value)
        except Exception:
            return value
    return value


def _parse_rule(text):
    match = RULE_PATTERN.match(text)
    if not match:
        raise ValueError(f"cannot parse show_when '{text}', use e.g. objective == cost_minimize")
    controller, op, raw = match.groups()
    op = re.sub(r'\s+', ' ', op)
    raw = raw.strip()
    if op in ('==', '!='):
        values = [raw.strip('\'" ')]
    else:
        raw = raw.strip('[](){} ')
        values = [v.strip().strip('\'" ') for v in raw.split(',') if v.strip()]
    if not values:
        raise ValueError(f"show_when '{text}' has no value")
    return controller, op, values


def _list_hint(value):
    if _is_blank(value):
        return []
    if isinstance(value, str):
        return [v.strip() for v in re.split(r'[,\n]', value) if v.strip()]
    return [str(v) for v in value]


# --------------------------------------------------------------------------- grouping

def _find_groups(args):
    """Feature groups keyed by the best toggle: X_enabled > enable_X > use_X."""
    groups = {}
    for arg in args:
        if not arg.is_toggle:
            continue
        for pattern, priority in CONTROLLER_PATTERNS:
            match = pattern.match(arg.name)
            if match:
                key = match.group(1)
                current = groups.get(key)
                if current is None or priority > current['priority']:
                    groups[key] = {
                        'key': key, 'controller': arg.name, 'priority': priority,
                        'tokens': _tokens(key), 'members': [], 'first_index': None,
                    }
                break
    return groups


def _assign_groups(args, groups, overrides):
    """Return {arg name: group key | ('tab', title) | None}."""
    controllers = {g['controller']: g['key'] for g in groups.values()}
    assignment = {}
    current = None
    for index, arg in enumerate(args):
        override_group = overrides.get(arg.name, {}).get('group')
        if override_group:
            assignment[arg.name] = ('tab', str(override_group))
            continue
        if arg.name in controllers:
            assignment[arg.name] = None
            current = controllers[arg.name]
            continue
        arg_tokens = set(_tokens(arg.name))
        best, best_size = None, 0
        for group in groups.values():
            size = len(group['tokens'])
            if group['tokens'] and set(group['tokens']) <= arg_tokens and size > best_size:
                best, best_size = group['key'], size
        if best and not arg.is_toggle:
            assignment[arg.name] = best
            current = best
        elif current and not arg.is_toggle and not COMMON_NAME.match(arg.name):
            assignment[arg.name] = current
        else:
            assignment[arg.name] = None
            current = None
        if assignment[arg.name]:
            group = groups[assignment[arg.name]]
            group['members'].append(arg.name)
            if group['first_index'] is None:
                group['first_index'] = index
    return assignment


def _common_prefix_token(table_args):
    counts = {}
    for arg in table_args:
        parts = arg.name.lower().split('_')
        if len(parts) > 1:
            counts[parts[0]] = counts.get(parts[0], 0) + 1
    shared = [t for t, n in counts.items() if n >= 2]
    return shared[0] if shared else None


def _build_tabs(args, groups, assignment, title):
    by_name = {a.name: a for a in args}
    prefix = _common_prefix_token([a for a in args if a.is_table])
    settings = []
    tabs = []  # (first_index, title, fields)
    tab_index = {}

    def tab(tab_title, index):
        if tab_title not in tab_index:
            tab_index[tab_title] = [index, tab_title, []]
            tabs.append(tab_index[tab_title])
        return tab_index[tab_title]

    for index, arg in enumerate(args):
        target = assignment.get(arg.name)
        if isinstance(target, tuple):
            tab(target[1], index)[2].append(arg.name)
        elif target:
            tab(title(groups[target]['key']), index)[2].append(arg.name)
        elif arg.is_table:
            name = arg.name
            if prefix and name.lower().startswith(prefix + '_'):
                name = name[len(prefix) + 1:]
            tab(title(name), index)[2].append(arg.name)
        else:
            settings.append(arg.name)
    tabs.sort(key=lambda t: t[0])
    result = []
    if settings:
        result.append({'title': 'Settings', 'fields': settings})
    result.extend({'title': t[1], 'fields': t[2]} for t in tabs)
    for entry in result:
        entry['fields'] = [n for n in entry['fields'] if n in by_name]
    return result


def _build_output_tabs(outputs, output_groups, title):
    tabs = []
    placed = set()
    for group_title, names in output_groups.items():
        names = [n for n in names if n in outputs]
        if names:
            tabs.append({'title': group_title, 'fields': names})
            placed.update(names)
    rest = [o for o in outputs if o not in placed]
    firsts = {}
    for name in rest:
        firsts.setdefault(name.split()[0].lower(), []).append(name)
    emitted = set()
    for name in rest:
        first = name.split()[0].lower()
        members = firsts[first]
        if len(members) >= 2:
            if first not in emitted:
                tabs.append({'title': _tab_title(members[0].split()[0], title), 'fields': members})
                emitted.add(first)
        else:
            tabs.append({'title': _tab_title(name, title), 'fields': [name]})
    return tabs


def _tab_title(name, title):
    return title(name) if name == name.lower() else name


# --------------------------------------------------------------------------- show / hide
# Callbacks are inline expressions where '@' stands for the controlling field's value
# (true/false for a checkbox, a quoted string otherwise), as in stock_chart() or bodyfat2().
# A list of expressions gives the visibility of each field in 'fields' one by one.

def _js_string(value):
    escaped = value.replace('\\', '\\\\').replace("'", "\\'").replace('\n', '\\n')
    return f"'{escaped}'"


def _inline_condition(op, values):
    lowered = [v.lower() for v in values]
    if op in ('==', '!=') and lowered[0] in ('true', 'false'):
        return '@' if (lowered[0] == 'true') == (op == '==') else '!@'
    literals = [_js_string(v) for v in values]
    if op == '==':
        return f'@==={literals[0]}'
    if op == '!=':
        return f'@!=={literals[0]}'
    return f"[{', '.join(literals)}].indexOf(@) {'< 0' if op == 'not in' else '>= 0'}"


def _build_showhide(args, groups, overrides, warnings):
    names = {a.name for a in args}
    by_controller = {}  # controller -> [(condition, [fields])]

    def add(controller, condition, fields):
        entries = by_controller.setdefault(controller, [])
        for entry in entries:
            if entry[0] == condition:
                entry[1].extend(fields)
                return
        entries.append((condition, list(fields)))

    ruled = set()
    for arg_name, override in overrides.items():
        text = override.get('show_when')
        if not text or arg_name not in names:
            continue
        try:
            controller, op, values = _parse_rule(str(text))
        except ValueError as e:
            warnings.append(f'{arg_name}: {e}')
            continue
        if controller not in names:
            warnings.append(f"{arg_name}: show_when refers to unknown argument '{controller}'")
            continue
        if any('@' in v for v in values):
            warnings.append(f"{arg_name}: show_when values cannot contain '@'")
            continue
        ruled.add(arg_name)
        add(controller, _inline_condition(op, values), [arg_name])

    for group in groups.values():
        members = [m for m in group['members'] if m not in ruled]
        if members:
            add(group['controller'], '@', members)

    showhide = {}
    for controller, entries in by_controller.items():
        fields = [f for _, flds in entries for f in flds]
        if len(entries) == 1:
            callback = entries[0][0]
        else:
            callback = '[' + ', '.join(cond for cond, flds in entries for _ in flds) + ']'
        showhide[controller] = {'fields': fields, 'callback': callback}
    return showhide


# --------------------------------------------------------------------------- schema

def _schema_entry(arg, override, detected_choices, doc, table_helpers, warnings, title, explicit=False):
    if arg.is_table:
        helper = f'table_{arg.name}'
        if table_helpers and helper in table_helpers:
            return _Raw(f"{helper}({arg.name!r})"), helper
        warnings.append(f"{arg.name}: no table_{arg.name}() helper found, define its table schema manually")
        return None, None

    entry = {}
    choices = _parse_choices(override.get('choices'), title) or {}
    inferred_choices = False
    if not choices and detected_choices:
        pool = list(detected_choices)
        if isinstance(arg.default, str) and arg.default and arg.default not in pool:
            pool.insert(0, arg.default)
        if len(pool) >= 2:
            choices = {v: title(v) for v in pool}
            inferred_choices = True
    explicit_type = override.get('type')
    override_initial = _parse_initial(override['initial']) if 'initial' in override else _MISSING
    # qcalc takes the field type and initial value from a non-None default (see QJField._val2type),
    # so schema type/initial are only needed when there is no such default, unless asked explicitly
    has_value = arg.has_default and (arg.default is not None or not arg.default_known)
    default = arg.default if has_value and arg.default_known else _MISSING
    initial = _MISSING

    if has_value and override_initial is not _MISSING:
        warnings.append(
            f"{arg.name}: initial override ignored, the default value in the signature takes precedence"
        )
        override_initial = _MISSING

    if choices:
        entry['type'] = 'choice'
        entry['choices'] = choices
        if not has_value:
            initial = next(iter(choices))
        elif explicit and isinstance(default, str) and default in choices:
            initial = default
        if inferred_choices:
            warnings.append(f"{arg.name}: choices {list(choices)} inferred from the code, please verify")
    else:
        if arg.annotation is None:
            if has_value:
                if explicit:
                    for py_type, field_type in ((bool, 'checkbox'), (float, 'float'), (int, 'integer')):
                        if isinstance(default, py_type):
                            entry['type'], initial = field_type, default
                            break
            elif arg.is_toggle:
                entry['type'], initial = 'checkbox', False
            elif PERCENT_NAME.search(arg.name):
                entry['type'] = 'float'
                if not arg.has_default:
                    initial = 0.0
            elif CHOICE_NAME.search(arg.name):
                warnings.append(f"{arg.name}: looks like a choice but no choices were found, "
                                "supply them with an override")
        if explicit_type:
            entry['type'] = explicit_type

    if override_initial is not _MISSING:
        initial = override_initial
    if initial is not _MISSING and (entry.get('type') or choices):
        entry['initial'] = initial

    if override.get('label'):
        entry['label'] = override['label']
    help_text = override.get('help_text') or _docstring_help(doc, arg.name)
    if help_text:
        entry['help_text'] = help_text
    return entry or None, None


# --------------------------------------------------------------------------- rendering

def _format_key(key):
    return repr(key) if isinstance(key, str) else str(key)


def _format_value(value, level):
    pad = INDENT * level
    if isinstance(value, _Raw):
        return str(value)
    if isinstance(value, dict):
        if not value:
            return '{}'
        lines = [f"{pad}{INDENT}{_format_key(k)}: {_format_value(v, level + 1)}," for k, v in value.items()]
        return '{\n' + '\n'.join(lines) + '\n' + pad + '}'
    if isinstance(value, (list, tuple)):
        if not value:
            return '[]'
        if all(not isinstance(v, (dict, list, tuple, _Raw)) for v in value):
            inline = '[' + ', '.join(repr(v) for v in value) + ']'
            if len(inline) <= INLINE_LIMIT:
                return inline
        lines = [f"{pad}{INDENT}{_format_value(v, level + 1)}," for v in value]
        return '[\n' + '\n'.join(lines) + '\n' + pad + ']'
    return repr(value)


def _render_code(func_name, spec, helpers_used): 
    # Render the __info() function code for the given function name, spec, and helpers used.
    lines = []
    if helpers_used:
        lines.append(f"# Requires: from calc import {', '.join(sorted(helpers_used))}")
    lines.append(f'def {func_name}__info():')
    lines.append(f'{INDENT}return {_format_value(spec, 1)}')
    return '\n'.join(lines) + '\n'


# --------------------------------------------------------------------------- public API

def build_info(source, overrides=None, hints=None, table_helpers=None):
    """Build a draft ``__info`` for the calculator described by ``source``.

    ``overrides``: ``{arg: {...}}`` or a list of rows with an ``arg`` key. Supported keys are
    ``label``, ``help_text``, ``choices`` (dict, list or ``'a=Label A, b=Label B'``), ``group`` (tab title),
    ``show_when`` (``"controller == value"``, ``!=``, ``in a, b``), ``type`` and ``initial``.

    ``hints``: ``func_name``, ``title``, ``desc``, ``tags``, ``calculate``, ``layout``, ``tabs``
    (``False`` disables, ``True`` forces tab layout), ``outputs`` (names, list or comma separated text),
    ``output_groups`` (``{tab: [output names]}``), ``scan_body`` (``False`` skips body scans) and
    ``explicit_defaults`` (``True`` also writes type/initial for fields with a non-None default;
    by default qcalc derives them from the signature, so they are omitted) and ``proper``
    (comma separated words whose case is kept in titles, e.g. ``'SOP, BOM'``; also written as the
    ``proper`` key of ``__info``).

    ``table_helpers``: names of available ``table_<arg>`` schema builders, e.g. ``{'table_sop_demand'}``.
    """
    hints = dict(hints or {})
    overrides = _normalize_overrides(overrides)
    warnings = []

    tree = _parse_tolerant(source, hints.get('func_name'))
    func_node = _select_function(tree, hints.get('func_name'))
    func_name = func_node.name
    doc = ast.get_docstring(func_node)

    args = [
        a for a in _extract_args(func_node)
        if not a.name.startswith('__') and a.annotation not in SKIP_ANNOTATIONS
    ]
    for name in overrides:
        if name not in {a.name for a in args}:
            warnings.append(f"override for unknown argument '{name}' ignored")

    scan_body = hints.get('scan_body', True) is not False
    detected = _scan_choices(tree, [a.name for a in args if not a.is_table]) if scan_body else {}
    outputs = _list_hint(hints.get('outputs')) or (_scan_outputs(func_node) if scan_body else [])

    groups = _find_groups(args)
    assignment = _assign_groups(args, groups, overrides)
    groups = {k: g for k, g in groups.items() if g['members']}

    titler = _make_titler(hints.get('proper'))
    schema = {}
    helpers_used = set()
    explicit = bool(hints.get('explicit_defaults'))
    for arg in args:
        entry, helper = _schema_entry(
            arg, overrides.get(arg.name, {}), detected.get(arg.name, []), doc, table_helpers, warnings,
            titler, explicit=explicit,
        )
        if entry:
            schema[arg.name] = entry
        if helper:
            helpers_used.add(helper)

    showhide = _build_showhide(args, groups, overrides, warnings)

    spec = {'title': hints.get('title') or titler(func_name)}
    desc = hints.get('desc') or _docstring_desc(doc)
    if desc:
        spec['desc'] = desc

    tabs = _build_tabs(args, groups, assignment, titler)
    use_tabs = hints.get('tabs')
    if use_tabs is None:
        use_tabs = len(tabs) >= 2
    output_groups = hints.get('output_groups') or {}
    output_tabs = _build_output_tabs(outputs, output_groups, titler) \
        if outputs and (len(outputs) >= MIN_OUTPUTS_FOR_TABS or output_groups) else []

    layout = hints.get('layout') or ('tb' if use_tabs or output_tabs else None)
    if layout:
        spec['layout'] = layout
    if hints.get('calculate'):
        spec['calculate'] = hints['calculate']
    if use_tabs and tabs:
        spec['input_columns'] = 1
    if output_tabs:
        spec['output_columns'] = 1
    if use_tabs and tabs:
        spec['input_blocks'] = [{'column': 1, 'tabs': tabs}]
    if output_tabs:
        spec['output_blocks'] = [{'column': 1, 'tabs': output_tabs}]
    if showhide:
        spec['showhide'] = showhide
    if schema:
        spec['schema'] = schema

    tags = hints.get('tags')
    if _is_blank(tags):
        words = [w for w in func_name.lower().split('_') if w]
        words += [titler(g['key']).lower() for g in groups.values()]
        tags = ', '.join(dict.fromkeys(words))
    spec['tags'] = tags
    proper = _list_hint(hints.get('proper'))
    if proper:
        spec['proper'] = ', '.join(proper)

    code = _render_code(func_name, spec, helpers_used)
    ast.parse(code)  # the generated code must always be valid Python
    return InfoResult(func_name=func_name, spec=spec, code=code, warnings=warnings)
