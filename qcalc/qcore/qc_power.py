# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

"""Dependency-light formatting helpers for unit exponent expressions."""


def _format_power_expression(items, sort_key=None, dimensionless="1"):
    ordered_items = list(items)
    if sort_key is not None:
        ordered_items = sorted(ordered_items, key=sort_key)

    num_parts = []
    denom_parts = []
    for name, power in ordered_items:
        if power == 0:
            continue
        if power < 0:
            denom_parts.append(_render_power_term(name, -power))
        else:
            num_parts.append(_render_power_term(name, power))

    if not num_parts and not denom_parts:
        return dimensionless

    num = "*".join(num_parts) if num_parts else "1"
    denom = "" if not denom_parts else "/" + "/".join(denom_parts)
    return num + denom


def _render_power_term(name, power):
    if name == "1":
        return "1"
    if power == 1:
        return name
    return f"{name}^{power}"
