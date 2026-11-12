# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

from calc import QCost
from qcore import Qty, qfl

# Outputs that are not priced by include_cost.
CC_COST_SPEC = '~CC Work Volume'
BRICK_COST_SPEC = '~Brick Work*'
PLASTER_COST_SPEC = '~Plaster Work Area'
COST_HELP = 'Price the quantities and mandays with your saved Schedule of Rates (illustrative rates are used until you save one).'


def ccwork__info():
    return {
        'title': 'Estimate Gravel, Cement and Sand for Plain Cement Concrete work',
        'kins': 'rates, brickwork, plaster',
        'tags': 'construction, estimation',
        'schema': {
            'csg_ratio': {'label': 'Cement Sand Gravel Ratio'},
            'include_cost': {'help_text': COST_HELP},
        },
        'inp1': 0.5,
    }


def ccwork(work_thickness='3 inch', work_length='10.0 ft', work_width='15 inch',
           csg_ratio: qfl = 1.0, csg_ratio__sand_part=2.0, csg_ratio__gravel_part=4.0,
           mortar_dry_volume_factor=1.4, cement_bag_volume='1.25 ft**3/bag',
           skilled_labour_rate='10 cft/manday',
           unskilled_labour_rate='10 cft/manday',
           include_cost=False,
           ):
    work_thickness_inch = Qty(work_thickness, 'inch').val  # inch
    work_length_inch = Qty(work_length, 'inch').val  # inch
    work_width_inch = Qty(work_width, 'inch').val  # inch
    cement_bag_volume_v = Qty(cement_bag_volume, 'inch**3/bag').val
    skilled_labour_v = Qty(skilled_labour_rate, 'inch**3/manday').val
    unskilled_labour_v = Qty(unskilled_labour_rate, 'inch**3/manday').val

    work_volume = work_length_inch * work_thickness_inch * work_width_inch  # in3
    mortar_dry_volume = work_volume * mortar_dry_volume_factor  # in3
    parts = (csg_ratio + csg_ratio__sand_part + csg_ratio__gravel_part)
    total_cement_volume = (mortar_dry_volume * csg_ratio / parts) / cement_bag_volume_v  # bag
    total_sand_volume = mortar_dry_volume * csg_ratio__sand_part / parts  # in3
    total_gravel_volume = mortar_dry_volume * csg_ratio__gravel_part / parts  # in3
    skilled_labour_manday = work_volume / skilled_labour_v
    unskilled_labour_manday = work_volume / unskilled_labour_v

    result = {
        'Cement': Qty(total_cement_volume, 'bag'),
        'Sand': Qty(total_sand_volume, 'inch^3').to('cft'),
        'Gravel': Qty(total_gravel_volume, 'inch^3').to('cft'),
        'CC Work Volume': Qty(work_volume, 'inch^3').to('cft'),
        'Skilled Labour': Qty(skilled_labour_manday, 'manday'),
        'Unskilled Labour': Qty(unskilled_labour_manday, 'manday')
    }
    if include_cost:
        result.update(QCost.from_result(result, CC_COST_SPEC).results(per=result['CC Work Volume'], per_label='Volume'))
    return result


def brickwork__info():
    return {
        'title': 'Estimate Brick, Cement and Sand for Brickwork',
        'kins': 'rates, ccwork, plaster',
        'tags': 'construction, estimation',
        'interactive': True,
        'schema': {
            'work_thickness': {
                'help_text': 'select or enter a thickness in inches',
                'type': 'select2',
                'choices': {'1': '1/2 Brick', '2': '1 Brick', '3': '1.5 Bricks', '4': '2 Bricks'},
            },
            'cs_ratio': {'label': 'Cement Sand Ratio'},
            'include_cost': {'help_text': COST_HELP},
        },
        'layout': 'tb',
        'inp1': 0.5,
    }


def brickwork(brick_length='9.5 inch', brick_width='4.5 inch', brick_height='2.75 inch',
              work_thickness='1', work_length='10.0 ft', work_width='7.0 ft',
              cs_ratio: qfl = 1.0, cs_ratio__sand_part=4.0, mortar_dry_volume_factor=1.4,
              mortar_thickness='0.5 inch', cement_bag_volume='1.25 ft**3/bag',
              brick_wastage='5 pct',
              skilled_labour_rate='30 cft/manday',
              unskilled_labour_rate='20 cft/manday',
              include_cost=False,
              ):
    brick_length_inch = Qty(brick_length, 'inch').val
    brick_width_inch = Qty(brick_width, 'inch').val
    brick_height_inch = Qty(brick_height, 'inch').val
    work_length_inch = Qty(work_length, 'inch').val
    work_width_inch = Qty(work_width, 'inch').val
    mortar_thickness_inch = Qty(mortar_thickness, 'inch').val
    work_thickness_inch = {'1': brick_width_inch+2*mortar_thickness_inch,
                    '2': brick_length_inch+2*mortar_thickness_inch,
                    '3': (brick_width_inch+brick_length_inch)+3*mortar_thickness_inch,
                    '4': (brick_length_inch*2)+3*mortar_thickness_inch}.get(work_thickness, float(work_thickness))
    cement_bag_volume_v = Qty(cement_bag_volume, 'inch**3/bag').val
    brick_wastage_v = Qty(brick_wastage, 'unit').val
    skilled_labour_v = Qty(skilled_labour_rate, 'inch**3/manday').val
    unskilled_labour_v = Qty(unskilled_labour_rate, 'inch**3/manday').val

    brick_volume_wo_mortar_v = brick_length_inch * brick_width_inch * brick_height_inch
    brick_volume_with_mortar_v = (brick_length_inch + mortar_thickness_inch) * (
        brick_width_inch + mortar_thickness_inch) * (brick_height_inch + mortar_thickness_inch)
    work_volume_v = work_length_inch * work_width_inch * work_thickness_inch
    num_of_bricks_used_v = work_volume_v / brick_volume_with_mortar_v
    total_number_of_bricks_v = int(num_of_bricks_used_v * (1 + brick_wastage_v))
    mortar_weight_volume_v = (brick_volume_with_mortar_v - brick_volume_wo_mortar_v) * num_of_bricks_used_v
    mortar_dry_volume_v = mortar_weight_volume_v * mortar_dry_volume_factor
    total_cement_volume_v = (mortar_dry_volume_v * cs_ratio / (
        cs_ratio + cs_ratio__sand_part)) / cement_bag_volume_v
    total_sand_volume_v = mortar_dry_volume_v * cs_ratio__sand_part / (cs_ratio + cs_ratio__sand_part)
    skilled_labour_nos_v = work_volume_v / skilled_labour_v
    unskilled_labour_nos_v = work_volume_v / unskilled_labour_v
    result = {
        'Brick': Qty(total_number_of_bricks_v, 'nos'),
        # | adding a unit will enable cost calculation in conv()
        'Cement': Qty(total_cement_volume_v, 'bag'),
        'Sand': Qty(total_sand_volume_v, 'inch^3').to('cft'),
        'Brick Work Thickness': Qty(work_thickness_inch, 'inch'),
        'Brick Work Volume': Qty(work_volume_v, 'inch^3').to('cft'),
        'Skilled Labour': Qty(skilled_labour_nos_v, 'manday'),
        'Unskilled Labour': Qty(unskilled_labour_nos_v, 'manday')
    }
    if include_cost:
        result.update(QCost.from_result(result, BRICK_COST_SPEC).results(per=result['Brick Work Volume'], per_label='Volume'))
    return result


def plaster__info(): return {
    'title': 'Estimate Cement and Sand for Plaster work',
    'kins': 'rates, brickwork, ccwork',
    'tags': 'construction, estimation',
    'schema': {
        'schema': {
            'cs_ratio': {'label': 'Cement Sand Ratio'},
        },
        'work_side': {'type': 'radio', 'choices': {1: 'One Side', 2: 'Both Side'}},
        'include_cost': {'help_text': COST_HELP},
    },
    'inp1': 0.5,
}


def plaster(work_thickness='0.5 inch', work_length='12 ft', work_width='10 ft',
            work_side=2, cs_ratio: qfl = 1.0, cs_ration__sand_part=4.0,
            mortar_dry_volume_factor=1.5, cement_bag_volume='1.25 ft**3/bag',
            skilled_labour_rate='75 sft/manday',
            unskilled_labour_rate='50 sft/manday',
            include_cost=False
            ):
    work_thickness_inch = Qty(work_thickness, 'inch').val
    work_length_inch = Qty(work_length, 'inch').val
    work_width_inch = Qty(work_width, 'inch').val
    work_side = int(work_side)
    cement_bag_volume_v = Qty(cement_bag_volume, 'inch**3/bag').val
    skilled_labour_v = Qty(skilled_labour_rate, 'inch**2/manday').val
    unskilled_labour_v = Qty(unskilled_labour_rate, 'inch**2/manday').val

    work_volume = work_length_inch * work_thickness_inch * work_width_inch * work_side  # in3
    work_area = work_length_inch * work_width_inch * work_side  # in2
    mortar_dry_volume = work_volume * mortar_dry_volume_factor  # in3
    parts = (cs_ratio + cs_ration__sand_part)
    total_cement_volume = (mortar_dry_volume * cs_ratio / parts) / cement_bag_volume_v  # bag
    total_sand_volume = mortar_dry_volume * cs_ration__sand_part / parts  # in3
    skilled_labour_manday = work_area / skilled_labour_v  # manday
    unskilled_labour_manday = work_area / unskilled_labour_v  # manday

    result = {
        'Cement': Qty(total_cement_volume, 'bag'),
        'Sand': Qty(total_sand_volume, 'inch^3').to('cft'),
        'Plaster Work Area': Qty(work_area, 'inch^2').to('sft'),
        'Skilled Labour': Qty(skilled_labour_manday, 'manday'),
        'Unskilled Labour': Qty(unskilled_labour_manday, 'manday')
    }
    if include_cost:
        result.update(QCost.from_result(result, PLASTER_COST_SPEC).results(per=result['Plaster Work Area'], per_label='Area'))
    return result


if __name__ == '__main__':
    print(plaster())
