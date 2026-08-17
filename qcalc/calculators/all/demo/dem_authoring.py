# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

"""Small, copy-friendly examples for people authoring qCalc calculators."""

from qcore import Qty


def demo_paint_estimate__info():
    return {
        'title': 'Paint Estimate: Calculator Authoring Demo',
        'desc': 'A compact example of qCalc form metadata, quantity inputs, and readable results.',
        'calculate': 'Estimate paint',
        'schema': {
            'length': {'help_text': 'Room length. Try 16 ft or 5 m.'},
            'width': {'help_text': 'Room width. Try 12 ft or 4 m.'},
            'height': {'help_text': 'Wall height. Try 8 ft or 2.4 m.'},
            'coats': {'help_text': 'Number of paint coats to apply.'},
            'coverage': {'help_text': 'Paint coverage per litre, for example 10 m^2/L.'},
            'waste_percent': {'help_text': 'Extra paint allowed for cuts and touch-ups.'},
            'include_ceiling': {'help_text': 'Add the ceiling to the paintable area.'},
        },
    }


def demo_paint_estimate(
    length='16 ft',
    width='12 ft',
    height='8 ft',
    coats: int = 2,
    coverage='10 m^2/L',
    waste_percent: float = 10.0,
    include_ceiling: bool = False,
):
    """Estimate paint from room dimensions while accepting mixed units."""
    room_length = Qty(length)
    room_width = Qty(width)
    room_height = Qty(height)
    paint_coverage = Qty(coverage)

    wall_area = 2 * (room_length + room_width) * room_height
    paintable_area = wall_area + (room_length * room_width if include_ceiling else Qty('0 m^2'))
    paint_needed = paintable_area * coats / paint_coverage * (1 + waste_percent / 100)

    return {
        'Paintable Area': paintable_area.to('m^2'),
        'Paint Needed': paint_needed.to('L'),
        'Purchase Guide': f'Buy at least {paint_needed.to("L").val:.1f} L of paint.',
    }
