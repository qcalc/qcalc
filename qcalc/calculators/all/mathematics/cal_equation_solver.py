# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

import pandas as pd

from calc import solve_equation
from qcore import qlist, qtext, qhtml
from qutil import md2html


def equation_solver__info():
    return {
        "title": "Scalar and Unit-Aware Equation Solver",
        "tags": "equation, symbolic, unit-aware",
        "desc": (
            "Solve a single equation for one unknown. Uses a fast scalar path when all "
            "known values are numeric, and a unit-aware path when any Qty value is present."
        ),
        "schema": {
            "left": {
                "help_text": "Left side expression, for example: P*V or 2*x + 3",
            },
            "right": {
                "help_text": "Right side expression, for example: n*R*T or 11",
            },
            "known_values": {
                "help_text": (
                    "One known value per line as name=value. Value may be scalar (a=5) or quantity "
                    "(d=120 ft, v=10 m/s)."
                ),
            },
            "result_unit": {
                "help_text": (
                    "Optional output unit for the unknown, for example kPa or m/s. "
                ),
            },
            "units_in_expression": {
                "help_text": (
                    "When enabled, known unit names typed directly inside Left/Right expressions "
                    "(e.g. 12ft^2) are interpreted as units. Default is off."
                ),
            },
        },
    }


def _parse_name_value_lines(lines):
    data = {}
    for line in lines or []:
        text = str(line).strip()
        if text == "":
            continue
        if "=" not in text:
            raise ValueError(
                f"Invalid known_values row '{text}'. Expected format name=value."
            )
        name, value = text.split("=", 1)
        name = name.strip()
        value = value.strip()
        if name == "" or value == "":
            raise ValueError(
                f"Invalid known_values row '{text}'. Both name and value are required."
            )
        data[name] = value
    return data


def _solutions_table(values):
    return pd.DataFrame({"Solution": list(values)})


def equation_solver(
    left: qtext = "pi*radius^2",
    right: qtext = "area",
    known_values: qlist[str] = ['area=100 sft'],
    result_unit: qtext = "inch",
    units_in_expression: bool = False,
):
    known_values_map = _parse_name_value_lines(known_values)

    domain = None
    unit_text = result_unit.strip() if isinstance(result_unit, str) else ""
    if unit_text != "":
        domain = {"unit": unit_text}

    result = solve_equation(
        left=left,
        right=right,
        unknown=None,
        values=known_values_map,
        domain=domain,
        method="auto",
        units_in_expression=units_in_expression,
    )

    return {
        "Equation": qhtml(md2html(f"$${result['normalized_equation'].replace("**", "^")}$$", wrap=True)),
        "Unknown": result["unknown"],
        "Solutions": _solutions_table(result["solutions"]),
        "Status": result["status"],
        "Solution Count": result["solution_count"],
        "Mode": result["mode"],
    }
