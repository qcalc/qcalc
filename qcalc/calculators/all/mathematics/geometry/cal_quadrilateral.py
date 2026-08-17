# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

from qcore import Qty
import math


def quadlat__info():
    return {
        'title': 'Calculate Area of a Quadrilateral',
        'schema': {
            'object': {
                'type': 'choice',
                'choices': {
                    's': 'Square',
                    'r': 'Rectangle',
                    't': 'Trapezoid',
                    'i': 'Isosceles Trapezoid',
                    'h': 'Rhombas',
                    'k': 'Kite',
                    'p': 'Parallelogram',
                    'q': 'Irregular Quadrilateral',
                }
            }
        },
        'showhide': {
            'object': {
                'fields': ['side_a', 'side_b', 'side_c', 'side_d', 'angle_a', 'angle_c', 'height'],
                'callback': {
                    's': '[1, 0, 0, 0, 0, 0, 0]',
                    'r': '[1, 1, 0, 0, 0, 0, 0]',
                    't': '[1, 0, 1, 0, 0, 0, 1]',
                    'i': '[1, 1, 1, 1, 1, 1, 0]',
                    'h': '[1, 1, 1, 1, 1, 1, 0]',
                    'k': '[1, 1, 1, 1, 1, 1, 0]',
                    'p': '[1, 1, 1, 1, 1, 1, 0]',
                    'q': '[1, 1, 1, 1, 1, 1, 0]',
                },
            },
        },
    }


def quadlat(object='r', side_a='40.0 ft', side_b='60.0 ft', side_c='30.0 ft',
            side_d='30.0 ft', angle_a='120 deg',
            angle_c='60 deg', height='25 ft',
            result_area_unit='decimal', result_length_unit='ft',
            result_angle_unit='deg'
            ):
    if object == 's':
        aq = Qty(side_a, result_length_unit)
        areaq = aq * aq
        areaq = areaq.to(result_area_unit)
    elif object == 'r':
        aq = Qty(side_a, result_length_unit)
        bq = Qty(side_b, result_length_unit)
        areaq = aq * bq
        areaq = areaq.to(result_area_unit)
    elif object == 't':
        aq = Qty(side_a, result_length_unit)
        cq = Qty(side_c, result_length_unit)
        hq = Qty(height, result_length_unit)
        areaq = (aq + cq) * hq / 2
        areaq = areaq.to(result_area_unit)
    else:
        aq = Qty(side_a, result_length_unit)
        bq = Qty(side_b, result_length_unit)
        cq = Qty(side_c, result_length_unit)
        dq = Qty(side_d, result_length_unit)
        angle_a = Qty(angle_a).to('rad').val
        angle_c = Qty(angle_c).to('rad').val
        a = aq.val
        b = bq.val
        c = cq.val
        d = dq.val
        s = (a + b + c + d) / 2
        area = ((s - a) * (s - b) * (s - c) * (s - d) - 0.5 * a * b * c * d * (1 + math.cos(angle_a + angle_c))) ** 0.5
        areaq = Qty(area, f'{result_length_unit}^2', result_area_unit)
    return {'Area': areaq}
