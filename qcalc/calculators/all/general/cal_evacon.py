# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

import ast
from qcore import QScreen
from calc import QCals, QRam, QPref
from calc.mod_qcals_security import validate_expression_security
from asteval import Interpreter
from qutil import HtmxHttpRequest, q1139_request_init, preprocess_expression, is_debug


def _parse_top_level_assignment(xpr: str):
    """
    Return (var_name, rhs_expression) only for a simple top-level assignment like:
        x = <expr>
    Return None for normal expressions, function kwargs, comparisons, etc.
    """
    # If it is a valid expression (e.g. bmi(weight='60kg'), x==1, {'a': 1}),
    # it's not a console-assignment command.
    try:
        ast.parse(xpr, mode="eval")
        return None
    except SyntaxError:
        pass

    # Try statement parse and accept only: Name = <expr>
    try:
        tree = ast.parse(xpr, mode="exec")
    except SyntaxError:
        return None

    if len(tree.body) != 1:
        return None

    stmt = tree.body[0]
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
        symtable=syms,
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
    if xpr == "help":
        help_text = (
            "Commands:\n"
            "  strict [on|off]    disable/enable assignment to any variable\n"
            "  forget             clear stored variables\n"
            "  cls                clear screen\n"
            "  <expr>             evaluate a calculation\n"
            "  <value> to <unit>  convert a quantity to another unit\n"
            "  <value> as <unit>  same-unit conversion for display\n"
            "  x = <expr>         assign a value to a variable\n"
            "  qlib()             to get a list of qcalc functions\n\n"
            "  qtypes()           to get a list of calculator field types\n\n"
            "Examples:\n"
            "  ft to inch\n"
            "  (2+3*5-12)/3\n"
            "  3.5*m to ft\n"
            "  3.5 m to ft\n"
            "  3.5*m as yd, ft, inch\n"
            "  x = 60*ft/s\n"
            "  y = 35*m/s\n"
            "  x+y to m/s"
        )
        stdout = out.flush()
        return help_text, stdout

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

    # assignment
    assign_info = _parse_top_level_assignment(xpr)
    """
    bmi(weight='60kg')
    x = bmi(weight='60kg')
    x==1
    d={'a':1}
    a,b=1,2 (treated as non-assignment)
    x=2; y=3 (treated as non-assignment)
    """
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

    # evaluate
    res = validate_and_aeval(xpr)
    stdout = out.flush()
    return res, stdout
