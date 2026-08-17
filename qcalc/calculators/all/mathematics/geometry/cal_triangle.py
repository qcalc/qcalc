# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

from qcore import Qty
import math


def triangle__info():
    return {
        'title': 'Calculate Area of a Triangle',
        'schema': {
            'method': {
                'type': 'choice',
                'choices': {
                    '1': 'Base, height known',
                    '2': '2 Sides and included angle known',
                    '3': '3 Sides known',
                }
            }
        },
        'showhide': {
            'method': {
                'fields': ['side_a', 'side_b', 'side_c', 'base', 'height', 'angle'],
                'callback': {
                    '1': '[0, 0, 0, 1, 1, 1]',
                    '2': '[1, 1, 0, 0, 0, 1]',
                    '3': '[1, 1, 1, 0, 0, 0]',
                },
            },
        }
    }


def triangle(method='2', side_a='40.0 ft', side_b='60.0 ft', side_c='30.0 ft',
             base='30.0 ft', height='40.0 ft',
             angle='30 deg', result_area_unit='decimal', result_length_unit='ft',
             result_angle_unit='deg'
             ):
    if method == '1':
        bq = Qty(base)
        # result_length_unit = bq.uom

        b = bq.val
        hq = Qty(height, result_length_unit)
        h = hq.val
        area = 0.5 * b * h
        areaq = Qty(area, result_length_unit + '^2', result_area_unit)

        ang_abq = Qty(angle)
        # result_angle_unit = ang_abq.uom
        if ang_abq.val:
            ang_ab = ang_abq.to('rad').val
            a = h / math.sin(ang_ab)
            c = math.sqrt(a ** 2 + b ** 2 - 2 * a * b * math.cos(ang_ab))
            cq = Qty(c, result_length_unit)
            ang_bc = math.asin(2 * area / (b * c))
            ang_bcq = Qty(math.asin(2 * area / (b * c)), 'rad', result_angle_unit)
            ang_caq = Qty(math.pi - ang_ab - ang_bc, 'rad', result_angle_unit)
            ang_abq = Qty(ang_ab, 'rad', result_angle_unit)
            aq = Qty(a, result_length_unit)
        else:
            cq = Qty('@' + result_length_unit)
            aq = cq
            ang_abq = Qty('@deg')
            ang_bcq = ang_abq
            ang_caq = ang_abq
    elif method == '2':
        aq = Qty(side_a)
        # result_length_unit = aq.uom
        ang_abq = Qty(angle)
        # result_angle_unit = ang_abq.uom

        a = aq.val
        bq = Qty(side_b, aq.uom)
        b = bq.val
        ang_ab = ang_abq.to('rad').val
        area = 0.5 * a * b * math.sin(ang_ab)
        areaq = Qty(area, result_length_unit + '^2', result_area_unit)
        # calculate side3
        c = math.sqrt(a ** 2 + b ** 2 - 2 * a * b * math.cos(ang_ab))
        cq = Qty(c, result_length_unit)
        ang_bc = math.asin(2 * area / (b * c))
        ang_bcq = Qty(math.asin(2 * area / (b * c)), 'rad', result_angle_unit)
        ang_caq = Qty(math.pi - ang_ab - ang_bc, 'rad', result_angle_unit)
        ang_abq = Qty(ang_ab, 'rad', result_angle_unit)
    else:
        aq = Qty(side_a)
        # result_length_unit = aq.uom
        # result_angle_unit = 'deg'
        a = aq.val
        bq = Qty(side_b, result_length_unit)
        b = bq.val
        cq = Qty(side_c, result_length_unit)
        c = cq.val
        s = (a + b + c) / 2
        area = (s * (s - a) * (s - b) * (s - c)) ** 0.5
        areaq = Qty(area, result_length_unit + '^2', result_area_unit)
        ang_ab = math.asin(2 * area / (a * b))
        ang_abq = Qty(ang_ab, 'rad', result_angle_unit)
        ang_bc = math.asin(2 * area / (b * c))
        ang_bcq = Qty(ang_bc, 'rad', result_angle_unit)
        ang_caq = Qty(math.pi - ang_ab - ang_bc, 'rad', result_angle_unit)
    return {'Area': areaq,
            'Side a': aq, 'Side b': bq, 'Side c': cq,
            'Angle ab': ang_abq, 'Angle bc': ang_bcq, 'Angle ca': ang_caq}
