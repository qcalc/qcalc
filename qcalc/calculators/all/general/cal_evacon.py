# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

import ast
from qcore import QScreen
from calc import QCals, QRam, QPref
from asteval import Interpreter
from qutil import HtmxHttpRequest, q1139_request_init, preprocess_expression, is_debug, \
    validate_expression_security

_AUGASSIGN_OPS = {
    ast.Add: "+", ast.Sub: "-", ast.Mult: "*", ast.Div: "/",
    ast.FloorDiv: "//", ast.Mod: "%", ast.Pow: "**",
    ast.LShift: "<<", ast.RShift: ">>",
    ast.BitOr: "|", ast.BitXor: "^", ast.BitAnd: "&", ast.MatMult: "@",
}


def _parse_top_level_assignment(xpr: str, tree):
    """
    Return (var_name, rhs_expression) only for a simple top-level assignment like:
        x = <expr>  or  x += <expr>
    Return None for normal expressions, function kwargs, comparisons, etc.
    """
    # If it is a valid expression (e.g. bmi(weight='60kg'), x==1, {'a': 1}),
    # it's not a console-assignment command.
    try:
        ast.parse(xpr, mode="eval")
        return None
    except SyntaxError:
        pass

    if tree is None or len(tree.body) != 1:
        return None

    stmt = tree.body[0]

    if isinstance(stmt, ast.AugAssign):
        if not isinstance(stmt.target, ast.Name):
            return None
        op_symbol = _AUGASSIGN_OPS.get(type(stmt.op))
        if op_symbol is None:
            return None
        var_name = stmt.target.id
        if hasattr(stmt.value, "end_col_offset"):
            rhs_val = xpr[stmt.value.col_offset:stmt.value.end_col_offset].strip()
        else:
            parts = xpr.split(op_symbol + "=", 1)
            rhs_val = parts[1].strip() if len(parts) == 2 else ""
        # rebuild as a plain expression so the current value of var_name is reused
        return var_name, f"{var_name} {op_symbol} ({rhs_val})"

    if not isinstance(stmt, ast.Assign):
        return None

    if len(stmt.targets) != 1 or not isinstance(stmt.targets[0], ast.Name):
        return None

    var_name = stmt.targets[0].id

    # Safely slice RHS from source using end_col_offset (Python 3.8+)
    if hasattr(stmt.value, "end_col_offset"):
        rhs = xpr[stmt.value.col_offset:stmt.value.end_col_offset].strip()
    else:
        # Fallback if needed
        parts = xpr.split("=", 1)
        rhs = parts[1].strip() if len(parts) == 2 else ""

    return var_name, rhs


def _base_name(node):
    # unwrap x[k].attr[k2] style targets down to the root Name, if any
    while isinstance(node, (ast.Subscript, ast.Attribute)):
        node = node.value
    return node.id if isinstance(node, ast.Name) else None


def _find_reserved_mutation(tree, reserved_syms: set):
    # detect x[...]=, x.attr=, del x, etc. targeting a reserved/protected name,
    # which _parse_top_level_assignment doesn't cover (only plain Name targets)
    if tree is None:
        return None
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            targets = node.targets
        elif isinstance(node, (ast.AugAssign, ast.AnnAssign)):
            targets = [node.target]
        elif isinstance(node, ast.Delete):
            targets = node.targets
        else:
            continue
        for t in targets:
            name = _base_name(t)
            if name and name in reserved_syms:
                return name
    return None


def _expr_may_mutate(tree) -> bool:
    # only persist usyms when xpr could plausibly change stored state, to avoid
    # a session write on every plain-read calculation (e.g. "2+2")
    if tree is None:
        return True  # unparseable: be safe and persist
    for node in ast.walk(tree):
        if isinstance(node, (ast.Assign, ast.AugAssign, ast.AnnAssign, ast.Delete, ast.Call)):
            return True
        if isinstance(node, (ast.Subscript, ast.Attribute)) and isinstance(node.ctx, ast.Store):
            return True
    return False


def _top_level_assigned_names(tree):
    # collect plain Name targets assigned at the top level, e.g. "x=1; y=2",
    # which _parse_top_level_assignment skips because it only handles a single statement
    if tree is None:
        return set()
    names = set()
    for stmt in tree.body:
        if isinstance(stmt, ast.Assign):
            names.update(t.id for t in stmt.targets if isinstance(t, ast.Name))
        elif isinstance(stmt, ast.AugAssign) and isinstance(stmt.target, ast.Name):
            names.add(stmt.target.id)
    return names


def qeval(request: HtmxHttpRequest, xpr: str):
    out = QScreen()
    syms = QCals.qsymbol_dict.copy()
    q1139_request_init(request)
    usyms = QRam.getp({})
    reserved_syms = set(syms)
    syms.update(usyms)

    # Inject the request object into the symbol table
    if is_debug() or request.user.is_staff:
        syms['request'] = request
        reserved_syms.add('request')

    strict_assign = QPref.getp1('strict_assign')

    aeval = Interpreter(
        # nested_symtable requires an asteval Group-based symtable (built via
        # user_symbols=), not a plain dict, or calls to user-defined functions
        # break name lookup (AttributeError: 'dict' object has no attribute
        # '__getattr__').
        user_symbols=syms,
        readonly_symbols=reserved_syms if strict_assign else None,
        nested_symtable=True,
        writer=out.out,
        err_writer=out.out,
    )

    xpr = preprocess_expression(xpr).strip()

    # command: strict
    if xpr in {"strict on", "strict off"}:
        enabled = xpr.endswith("on")
        QPref.setp1("strict_assign", enabled)
        stdout = out.flush()
        return f"strict assign set to {'on' if enabled else 'off'}", stdout
    elif xpr == "strict":
        stdout = out.flush()
        return f"strict assign is {'on' if strict_assign else 'off'}", stdout

    # command: forget
    if xpr == "forget":
        usyms.clear()
        QRam.clear()
        stdout = out.flush()
        return "Assigned variables cleared", stdout

    # command: help
    if xpr in ["?", "help"]:
        help_text = (
            "Commands:\n"
            "  ? | help [<name>]  show this help screen or help on qcalc symbols\n"
            "  find <name>        show qcalc symbols matching a wildcard (*,?) filter\n"
            "  strict [on|off]    disable/enable assignment to any variable\n"
            "  forget             clear stored variables\n"
            "  cls                clear screen\n"
            "  <expr>             evaluate a calculation\n"
            "  <value> to <unit>  convert a quantity to another unit\n"
            "  <value> as <unit>  same-unit conversion for display\n"
            "  x = <expr>         assign a value to a variable\n"
            "  qtypes()           to get a list of calculator field types\n"
            "  qsymbols()         to get a list of qcalc symbols\n"
            "  qmodules()         list of importable modules in frontend\n"
            "\n"
            "Examples:\n"
            "  ft to inch\n"
            "  (2+3*5-12)/3\n"
            "  3.5*m to ft\n"
            "  3.5 m to ft\n"
            "  3.5*m + 2.5*ft\n"
            "  3.5m + 2.5ft\n"
            "  3.5*m as yd, ft, inch\n"
            "  x = 60*ft/s\n"
            "  y = 35*m/s\n"
            "  x+y to m/s\n"
            "  help bmi\n"
            "  find bm*\n"
        )
        stdout = out.flush()
        return help_text, stdout

    if xpr.startswith("?") or xpr.startswith("help "):
        rest = xpr[1:].strip() if xpr.startswith("?") else xpr[4:].strip()
        if rest:
            if ' ' not in rest:
                from qapi.mod_autil import qsymhelp
                help_text = qsymhelp(rest)
                stdout = out.flush()
                return help_text, stdout
            stdout = out.flush()
            return "Usage: help <name>  or  help --<name>", stdout

    if xpr.startswith("find"):
        rest = xpr[4:].strip()
        if rest:
            if ' ' not in rest:
                from qapi.mod_autil import qsymbols, qsymhelp
                matches = qsymbols('all', rest)
                stdout = out.flush()
                if not matches:
                    return f"No qCalc symbols matched '{rest}'", stdout
                if len(matches) == 1:
                    return qsymhelp(rest), stdout
                else:
                    return matches, stdout
            stdout = out.flush()
            return "Usage: find <name>", stdout
        stdout = out.flush()
        return "Usage: find <name>", stdout

    def validate_and_aeval(expr):
        validate_expression_security(expr, syms)
        return aeval(expr)

    # command: to
    if " to " in xpr:
        qty_from, qty_to = [part.strip() for part in xpr.split(" to ", 1)]
        res = validate_and_aeval(qty_from).to_units(qty_to)
        res = ' or '.join([str(r) for r in res])
        stdout = out.flush()
        return res, stdout

    # command: as
    if " as " in xpr:
        qty_from, qty_to = [part.strip() for part in xpr.split(" as ", 1)]
        res = validate_and_aeval(qty_from).as_units(qty_to)
        stdout = out.flush()
        return res, stdout

    # parse once and reuse for all assignment/mutation checks below
    try:
        exec_tree = ast.parse(xpr, mode="exec")
    except SyntaxError:
        exec_tree = None

    # assignment
    # examples: bmi(weight='60kg'), x = bmi(weight='60kg'), x==1, d={'a':1},
    # a,b=1,2 (non-assignment), x=2; y=3 (multi-statement, handled below instead)
    assign_info = _parse_top_level_assignment(xpr, exec_tree)
    if assign_info:
        # var_name, var_value = xpr.split("=", 1)
        # var_name = var_name.strip()
        var_name, var_value = assign_info
        if not strict_assign or var_name not in reserved_syms:
            res = validate_and_aeval(var_value.strip())
            usyms[var_name] = res
            QRam.setp(usyms)
            stdout = out.flush()
            return f"{var_name} assigned.", stdout
        else:
            stdout = out.flush()
            return f"Error: {var_name} can't be assigned", stdout

    # guard against strict-mode bypass via subscript/attribute/multi-statement assignment
    if strict_assign:
        blocked_name = _find_reserved_mutation(exec_tree, reserved_syms)
        if blocked_name:
            stdout = out.flush()
            return f"Error: {blocked_name} can't be assigned", stdout

    # evaluate
    res = validate_and_aeval(xpr)
    # sync back scalar rebinds from multi-statement input (e.g. "x=1; y=2"),
    # which live only in aeval's own symtable and aren't shared by reference
    for name in _top_level_assigned_names(exec_tree):
        if name in aeval.symtable:
            usyms[name] = aeval.symtable[name]
    if _expr_may_mutate(exec_tree):
        # persist in case xpr mutated an existing variable in-place
        # (e.g. x["name"]=5), which isn't caught as a top-level assignment
        QRam.setp(usyms)
    stdout = out.flush()
    return res, stdout
