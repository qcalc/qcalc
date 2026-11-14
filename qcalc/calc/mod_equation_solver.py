# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

from __future__ import annotations

import math
import cmath
from numbers import Number

from sympy import Eq, log as sympy_log, symbols, solve as sympy_solve, sympify
from sympy.abc import _clash1

from qcore import Qty, isMeasureQuantity, UnitRegistry
from qutil import to_python_expr
from calc.mod_sandbox import CalcSandbox


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


def _is_unit_symbol_name(name: str) -> bool:
    return UnitRegistry.is_uom(name)


def _symbol_assumption_flags(domain):
    if not isinstance(domain, dict):
        return {}
    assumptions = domain.get("assumptions")
    if not isinstance(assumptions, dict):
        return {}
    return {k: bool(v) for k, v in assumptions.items() if isinstance(k, str)}


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
        otype, normalized, _ = Qty.kind(text)
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
    """Return (known values, unit hints, whether any value is a Qty)."""
    solved_values = {}
    unit_hints = {}
    qty_present = False

    for key, raw in (values or {}).items():
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


class QEquationSolver:
    """
    Solve an equation for one unknown with scalar-fast and unit-aware routes.

    Parameters
    ----------
    left, right:
        Left and right equation expressions as text.
    unknown:
        Symbol name to solve for. If omitted, must be inferable uniquely.
    domain:
        Optional domain metadata. Supported forms:
        - "kPa" (unit hint for unknown)
        - {"unit": "kPa"}
        - {"units": {"P": "kPa"}}
        - {"P": "kPa"}
        - {"assumptions": {"real": True, "positive": True}}
    values:
        Dict of known symbol values. Values may be scalar numbers, `Qty`,
        quantity strings (e.g. "3 ft"), or unit hints (e.g. "kPa", "@kPa").
    method:
        "auto", "scalar", or "qty".
    units_in_expression:
        If True, treat known unit tokens appearing directly in `left`/`right`
        (e.g. 12ft^2) as units. If False (default), they are treated as symbols.

    Construction parses and validates the inputs; `solve()` returns the result.
    """

    def __init__(
        self,
        left,
        right,
        unknown=None,
        domain=None,
        values=None,
        method="auto",
        units_in_expression=False,
    ):
        if method not in {"auto", "scalar", "qty"}:
            raise ValueError("method must be one of: 'auto', 'scalar', 'qty'.")

        self.domain = domain
        self.units_in_expression = units_in_expression
        self.left = to_python_expr(left)
        self.right = to_python_expr(right)
        self.eq = Eq(
            sympify(self.left, locals=_SYMPY_LOCALS),
            sympify(self.right, locals=_SYMPY_LOCALS),
        )
        self.values, self.unit_hints, qty_present = _normalize_values(values)
        self.unknown_symbol = self._infer_unknown(unknown)
        self.unknown = str(self.unknown_symbol)
        self.mode = self._resolve_mode(method, qty_present)

        if self.unknown in self.values:
            raise ValueError(
                f"Unknown '{self.unknown}' was provided in values. "
                "Provide known values only."
            )

        self.unit_hint = (
            self.unit_hints.get(self.unknown)
            or _unit_hint_from_domain(self.unknown, domain)
        )

    def solve(self):
        solutions = sympy_solve(self.eq.subs(self._known_subs()), self.unknown_symbol)
        if not solutions:
            raise ValueError("No solution found for the given equation and inputs.")

        if self.mode == "scalar":
            if self.unit_hint:
                raise ValueError(
                    "result_unit requires quantity context (known_values with units or units_in_expression)."
                )
            return self._result([self._scalar_solution(s) for s in solutions])

        return self._result([self._qty_solution(s) for s in solutions])

    def _infer_unknown(self, unknown):
        assumptions = _symbol_assumption_flags(self.domain)
        if unknown:
            return symbols(unknown, **assumptions)

        remaining = sorted(
            str(sym) for sym in self.eq.free_symbols if str(sym) not in self.values
        )
        units = [name for name in remaining if _is_unit_symbol_name(name)]
        names = [name for name in remaining if name not in units]

        interpreted_symbols = names if self.units_in_expression else remaining
        if len(interpreted_symbols) == 1:
            return symbols(interpreted_symbols[0], **assumptions)

        message = (
            "Could not infer a single unknown symbol. "
            f"Interpreted symbols: {', '.join(interpreted_symbols) or '(none)'}. "
        )
        if self.units_in_expression:
            message += (
                f"Interpreted units: {', '.join(units) or '(none)'}. "
                "Provide known_values so exactly one symbol remains unsolved."
            )
        elif units:
            message += (
                f"Detected unit-like symbols: {', '.join(units)}. "
                "If these are units in the equation text, enable units_in_expression."
            )
        else:
            message += "Provide known_values so exactly one symbol remains unsolved."
        raise ValueError(message)

    def _resolve_mode(self, method, qty_present):
        if self.units_in_expression and any(
            _is_unit_symbol_name(str(sym)) for sym in self.eq.free_symbols
        ):
            return "qty"
        if method == "auto":
            return "qty" if qty_present or self.unit_hints else "scalar"
        return method

    def _known_subs(self):
        subs = {}
        for name, value in self.values.items():
            if isMeasureQuantity(value):
                if self.mode == "scalar":
                    raise ValueError(
                        "Scalar solve path received Qty input. Use method='auto' or method='qty'."
                    )
                continue
            subs[symbols(name)] = value
        return subs

    @staticmethod
    def _scalar_solution(solution):
        value = solution.evalf() if hasattr(solution, "evalf") else solution
        if getattr(value, "is_number", False):
            value = float(value) if getattr(value, "is_real", None) else complex(value)
        return value

    def _qty_solution(self, solution):
        namespace = dict(self.values)
        if self.units_in_expression:
            for sym in solution.free_symbols:
                name = str(sym)
                if name not in namespace and _is_unit_symbol_name(name):
                    namespace[name] = Qty(1, name)
        value = CalcSandbox.eval(str(solution), gdict=_EVAL_GLOBALS, ldict=namespace)

        if isinstance(value, Number):
            if isinstance(value, complex) and self.unit_hint is not None:
                raise ValueError(
                    "Complex-valued solution cannot be converted to Qty with result unit. "
                    "Remove result_unit or constrain the equation to real solutions."
                )
            if self.unit_hint is not None:
                raise ValueError(
                    "result_unit can only be applied to unit-bearing solutions. "
                    "This solution is dimensionless."
                )
        elif not isMeasureQuantity(value):
            raise TypeError(
                "Qty solve path produced a non-quantity result. "
                "Use method='scalar' or provide unit-compatible inputs."
            )

        if isMeasureQuantity(value) and self.unit_hint:
            value = Qty(value, self.unit_hint)
        return value

    def _result(self, solved_values):
        result = {
            "status": "ok",
            "mode": self.mode,
            "unknown": self.unknown,
            "solution_count": len(solved_values),
            "solutions": solved_values,
            "unit": None,
            "normalized_equation": f'{self.left} = {self.right}',
        }
        qty_values = [v for v in solved_values if isMeasureQuantity(v)]
        if qty_values and len(qty_values) == len(solved_values):
            first_uom = qty_values[0].uom
            if all(v.uom == first_uom for v in qty_values):
                result["unit"] = first_uom
        return result
