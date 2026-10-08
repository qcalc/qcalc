# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

from __future__ import annotations

import math
import cmath
from numbers import Number

from sympy import Eq, log as sympy_log, symbols, solve, sympify
from sympy.abc import _clash1

from qcore import Qty, isMeasureQuantity, is_str_uom, str_type
from qutil import preprocess_expression
from calc.mod_qcals import QCals


def _safe_sqrt(value):
    if isMeasureQuantity(value):
        return value.sqrt()
    if isinstance(value, complex):
        return cmath.sqrt(value)
    return math.sqrt(value) if value >= 0 else cmath.sqrt(value)


def _safe_log(value, base=math.e):
    if isMeasureQuantity(value):
        raise ValueError('log requires a dimensionless value.')
    if isinstance(value, complex):
        return cmath.log(value, base)
    return math.log(value, base)


def _safe_log10(value):
    return _safe_log(value, 10)


def _sympy_log10(value):
    return sympy_log(value, 10)


_EVAL_GLOBALS = {
    "__builtins__": {},
    "pi": math.pi,
    "e": math.e,
    "I": 1j,
    "sqrt": _safe_sqrt,
    "log": _safe_log,
    "log10": _safe_log10,
    "abs": abs,
    "min": min,
    "max": max,
    "pow": pow,
}


_SYMPY_LOCALS = dict(_clash1)
_SYMPY_LOCALS.update({
    'log10': _sympy_log10,
})


def _normalize_equation_text(left: str, right: str):
    return preprocess_expression(left), preprocess_expression(right)


def _to_equation(left_expr: str, right_expr: str):
    left_expr = sympify(left_expr, locals=_SYMPY_LOCALS)
    right_expr = sympify(right_expr, locals=_SYMPY_LOCALS)
    return Eq(left_expr, right_expr)


def _is_unit_symbol_name(name: str) -> bool:
    return is_str_uom(name)


def _unit_symbol_names_in_equation(eq) -> set[str]:
    return {
        str(sym)
        for sym in eq.free_symbols
        if _is_unit_symbol_name(str(sym))
    }


def _symbol_assumption_flags(domain):
    if not isinstance(domain, dict):
        return {}
    assumptions = domain.get("assumptions")
    if not isinstance(assumptions, dict):
        return {}
    return {k: bool(v) for k, v in assumptions.items() if isinstance(k, str)}


def _get_unknown_symbol(
    eq,
    unknown,
    domain,
    known_names=None,
    units_in_expression=False,
):
    known_names = set(known_names or ())
    if unknown:
        assumption_flags = _symbol_assumption_flags(domain)
        return symbols(unknown, **assumption_flags)

    remaining = sorted((str(sym) for sym in eq.free_symbols if str(sym) not in known_names))
    remaining_units = sorted(name for name in remaining if _is_unit_symbol_name(name))
    remaining_symbols = [name for name in remaining if name not in remaining_units]

    interpreted_symbols = remaining_symbols if units_in_expression else remaining
    interpreted_units = remaining_units if units_in_expression else []

    if len(interpreted_symbols) != 1:
        detected_unit_like = sorted(name for name in remaining if _is_unit_symbol_name(name))
        if detected_unit_like and not units_in_expression:
            raise ValueError(
                "Could not infer a single unknown symbol. "
                f"Interpreted symbols: {', '.join(interpreted_symbols) if interpreted_symbols else '(none)'}. "
                f"Detected unit-like symbols: {', '.join(detected_unit_like)}. "
                "If these are units in the equation text, enable units_in_expression."
            )

        if units_in_expression:
            raise ValueError(
                "Could not infer a single unknown symbol. "
                f"Interpreted symbols: {', '.join(interpreted_symbols) if interpreted_symbols else '(none)'}. "
                f"Interpreted units: {', '.join(interpreted_units) if interpreted_units else '(none)'}. "
                "Provide known_values so exactly one symbol remains unsolved."
            )

        raise ValueError(
            "Could not infer a single unknown symbol. "
            f"Interpreted symbols: {', '.join(interpreted_symbols) if interpreted_symbols else '(none)'}. "
            "Provide known_values so exactly one symbol remains unsolved."
        )
    return symbols(interpreted_symbols[0], **_symbol_assumption_flags(domain))


def _unit_hint_from_domain(unknown_name, domain):
    if domain is None:
        return None
    if isinstance(domain, str):
        return domain
    if isinstance(domain, dict):
        if unknown_name in domain and isinstance(domain[unknown_name], str):
            return domain[unknown_name]
        units = domain.get("units")
        if isinstance(units, dict) and isinstance(units.get(unknown_name), str):
            return units[unknown_name]
        unit = domain.get("unit")
        if isinstance(unit, str):
            return unit
    return None


def _parse_value(raw):
    if isMeasureQuantity(raw):
        return raw, "qty", None
    if isinstance(raw, bool):
        return raw, "scalar", None
    if isinstance(raw, Number):
        return float(raw), "scalar", None
    if isinstance(raw, str):
        text = raw.strip()
        if text == "":
            raise ValueError("Empty value string is not allowed.")
        otype, normalized, _ = str_type(text)
        if otype == "qty":
            return Qty(normalized), "qty", None
        if otype == "uom":
            return None, "hint", normalized
        try:
            return float(text), "scalar", None
        except ValueError as err:
            raise ValueError(f"Could not parse value '{raw}'.") from err
    raise TypeError(f"Unsupported value type: {type(raw)!r}")


def _normalize_values(values):
    values = values or {}
    solved_values = {}
    unit_hints = {}
    qty_present = False

    for key, raw in values.items():
        value, kind, hint = _parse_value(raw)
        if kind == "hint":
            unit_hints[key] = hint
            continue
        if kind == "qty" and getattr(getattr(value, "unit", None), "offset", 0) != 0:
            value = value.in_base_units()
        solved_values[key] = value
        if kind == "qty":
            qty_present = True

    return solved_values, unit_hints, qty_present


def _is_qty_value(value):
    return isMeasureQuantity(value)


def _is_qty_mode(method, qty_present, unit_hints, domain, unknown_name):
    if method == "scalar":
        return False
    if method == "qty":
        return True
    if qty_present or unit_hints:
        return True
    return False


def _eval_sympy_expression(expr, value_namespace, units_in_expression=False):
    eval_namespace = {name: value_namespace[name] for name in value_namespace}
    if units_in_expression:
        for name in set(expr.free_symbols):
            symbol_name = str(name)
            if symbol_name not in eval_namespace and _is_unit_symbol_name(symbol_name):
                eval_namespace[symbol_name] = Qty(1, symbol_name)
    expr_text = str(expr)
    return QCals.safe_eval(expr_text, gdict=_EVAL_GLOBALS, ldict=eval_namespace)


def _result_with_status(unknown_name, mode, solved_values, normalized_equation=None):
    result = {
        "status": "ok",
        "mode": mode,
        "unknown": unknown_name,
        "solution_count": len(solved_values),
        "solutions": solved_values,
        "unit": None,
    }
    if normalized_equation is not None:
        result["normalized_equation"] = normalized_equation
    qty_values = [v for v in solved_values if isMeasureQuantity(v)]
    if len(qty_values) == len(solved_values) and qty_values:
        first_uom = qty_values[0].uom
        if all(v.uom == first_uom for v in qty_values):
            result["unit"] = first_uom
    return result


def solve_equation(
    left,
    right,
    unknown=None,
    values=None,
    domain=None,
    method="auto",
    units_in_expression=False,
):
    """
    Solve an equation for one unknown with scalar-fast and unit-aware routes.

    Parameters
    ----------
    left, right:
        Left and right equation expressions as text.
    unknown:
        Symbol name to solve for. If omitted, must be inferable uniquely.
    values:
        Dict of known symbol values. Values may be scalar numbers, `Qty`,
        quantity strings (e.g. "3 ft"), or unit hints (e.g. "kPa", "@kPa").
    domain:
        Optional domain metadata. Supported forms:
        - "kPa" (unit hint for unknown)
        - {"unit": "kPa"}
        - {"units": {"P": "kPa"}}
        - {"P": "kPa"}
        - {"assumptions": {"real": True, "positive": True}}
    method:
        "auto", "scalar", or "qty".
    units_in_expression:
        If True, treat known unit tokens appearing directly in `left`/`right`
        (e.g. 12ft^2) as units. If False (default), they are treated as symbols.
    """
    if method not in {"auto", "scalar", "qty"}:
        raise ValueError("method must be one of: 'auto', 'scalar', 'qty'.")

    normalized_left, normalized_right = _normalize_equation_text(left, right)
    eq = _to_equation(normalized_left, normalized_right)
    normalized_values, unit_hints, qty_present = _normalize_values(values)
    unknown_symbol = _get_unknown_symbol(
        eq=eq,
        unknown=unknown,
        domain=domain,
        known_names=normalized_values.keys(),
        units_in_expression=units_in_expression,
    )
    unknown_name = str(unknown_symbol)

    qty_mode = _is_qty_mode(
        method=method,
        qty_present=qty_present,
        unit_hints=unit_hints,
        domain=domain,
        unknown_name=unknown_name,
    )
    unit_symbols_present = units_in_expression and _unit_symbol_names_in_equation(eq)
    if unit_symbols_present:
        qty_mode = True
    mode = "qty" if qty_mode else "scalar"

    if unknown_name in normalized_values:
        raise ValueError(
            f"Unknown '{unknown_name}' was provided in values. "
            "Provide known values only."
        )

    known_subs = {}
    for name, value in normalized_values.items():
        if mode == "scalar" and _is_qty_value(value):
            raise ValueError(
                "Scalar solve path received Qty input. Use method='auto' or method='qty'."
            )
        if mode == "qty" and _is_qty_value(value):
            continue
        known_subs[symbols(name)] = value

    reduced_eq = eq.subs(known_subs)
    solutions = solve(reduced_eq, unknown_symbol)
    if not solutions:
        raise ValueError("No solution found for the given equation and inputs.")

    unit_hint = unit_hints.get(unknown_name) or _unit_hint_from_domain(unknown_name, domain)

    if mode == "scalar" and unit_hint:
        raise ValueError(
            "result_unit requires quantity context (known_values with units or units_in_expression)."
        )

    solved_values = []

    if mode == "scalar":
        for solution in solutions:
            value = solution.evalf() if hasattr(solution, "evalf") else solution
            if getattr(value, "is_number", False):
                if getattr(value, "is_real", None):
                    value = float(value)
                else:
                    value = complex(value)
            solved_values.append(value)

        return _result_with_status(
            unknown_name=unknown_name,
            mode=mode,
            solved_values=solved_values,
            normalized_equation=f'{normalized_left} = {normalized_right}',
        )

    for solution in solutions:
        qty_solution_value = _eval_sympy_expression(
            solution,
            normalized_values,
            units_in_expression=units_in_expression,
        )
        if isinstance(qty_solution_value, Number):
            if isinstance(qty_solution_value, complex) and unit_hint is not None:
                raise ValueError(
                    "Complex-valued solution cannot be converted to Qty with result unit. "
                    "Remove result_unit or constrain the equation to real solutions."
                )
            if unit_hint is not None:
                raise ValueError(
                    "result_unit can only be applied to unit-bearing solutions. "
                    "This solution is dimensionless."
                )
        elif not isMeasureQuantity(qty_solution_value):
            raise TypeError(
                "Qty solve path produced a non-quantity result. "
                "Use method='scalar' or provide unit-compatible inputs."
            )

        if isMeasureQuantity(qty_solution_value) and unit_hint:
            qty_solution_value = Qty(qty_solution_value, unit_hint)
        solved_values.append(qty_solution_value)

    return _result_with_status(
        unknown_name=unknown_name,
        mode=mode,
        solved_values=solved_values,
        normalized_equation=f'{normalized_left} = {normalized_right}',
    )
