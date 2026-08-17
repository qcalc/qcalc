# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

from qcore import Qty, qfl


def ccwork__info():
    return {
        'title': 'Estimate Gravel, Cement and Sand for Plain Cement Concrete work',
        'step2': [
            {'step': 'cost', 'caption': 'Calculate Cost of Materials',
             'spec': {'include': ['*'], 'exclude': ['CC Work Volume']}
             },
        ],
    }


def ccwork(work_thickness='3 inch', work_length='10.0 ft', work_width='15 inch',
           cement_sand_gravel_ratio: qfl = 1.0, sand_part=2.0, gravel_part=4.0,
           mortar_dry_volume_factor=1.4, cement_bag_volume='1.25 ft**3/bag',
           skilled_labour='10 cft/manday',
           unskilled_labour='10 cft/manday',
           ):
    work_thickness = Qty(work_thickness, 'inch').val
    work_length = Qty(work_length, 'inch').val
    work_width = Qty(work_width, 'inch').val
    cement_bag_volume = Qty(cement_bag_volume, 'inch**3/bag').val
    skilled_labour = Qty(skilled_labour, 'inch**3/manday').val
    unskilled_labour = Qty(unskilled_labour, 'inch**3/manday').val

    work_volume = work_length * work_thickness * work_width
    mortar_dry_volume = work_volume * mortar_dry_volume_factor
    parts = (cement_sand_gravel_ratio + sand_part + gravel_part)
    total_cement_volume = (mortar_dry_volume * cement_sand_gravel_ratio / parts) / cement_bag_volume
    total_sand_volume = mortar_dry_volume * sand_part / parts
    total_gravel_volume = mortar_dry_volume * gravel_part / parts
    skilled_labour_nos = work_volume / skilled_labour
    unskilled_labour_nos = work_volume / unskilled_labour

    return {
        'Cement': Qty(total_cement_volume, 'bag'),
        'Sand': Qty(total_sand_volume, 'inch**3').to('cft'),
        'Gravel': Qty(total_gravel_volume, 'inch**3').to('cft'),
        'CC Work Volume': Qty(work_volume, 'inch**3').to('cft'),
        'Skilled Labour': Qty(skilled_labour_nos, 'manday'),
        'Unskilled Labour': Qty(unskilled_labour_nos, 'manday')
    }


def brickwork__info():
    return {
        'title': 'Estimate Brick, Cement and Sand for Brickwork',
        'step2': [
            {'step': 'cost', 'caption': 'Calculate Cost of Materials',
             'spec': {'exclude': ['Brick Work Volume']}
             },
        ],
        'col': 2,
    }


def brickwork(brick_length='9.5 inch', brick_width='4.5 inch', brick_height='2.75 inch',
              work_thickness='5.5 inch', work_length='10.0 ft', work_width='7.0 ft',
              cement_sand_ratio: qfl = 1.0, sand_part=4.0, mortar_dry_volume_factor=1.4,
              mortar_thickness='0.5 inch', cement_bag_volume='1.25 ft**3/bag',
              brick_wastage='7 pct',
              skilled_labour='30 cft/manday',
              unskilled_labour='20 cft/manday',
              ):
    brick_length = Qty(brick_length, 'inch').val
    brick_width = Qty(brick_width, 'inch').val
    brick_height = Qty(brick_height, 'inch').val
    work_thickness = Qty(work_thickness, 'inch').val
    work_length = Qty(work_length, 'inch').val
    work_width = Qty(work_width, 'inch').val
    mortar_thickness = Qty(mortar_thickness, 'inch').val
    cement_bag_volume = Qty(cement_bag_volume, 'inch**3/bag').val
    brick_wastage = Qty(brick_wastage, 'unit').val
    skilled_labour = Qty(skilled_labour, 'inch**3/manday').val
    unskilled_labour = Qty(unskilled_labour, 'inch**3/manday').val

    brick_volume_wo_mortar = brick_length * brick_width * brick_height
    brick_volume_with_mortar = (brick_length + mortar_thickness) * (
        brick_width + mortar_thickness) * (brick_height + mortar_thickness)
    work_volume = work_length * work_width * work_thickness
    num_of_bricks_used = work_volume / brick_volume_with_mortar
    total_number_of_bricks = int(num_of_bricks_used * (1 + brick_wastage))
    mortar_weight_volume = (brick_volume_with_mortar - brick_volume_wo_mortar) * num_of_bricks_used
    mortar_dry_volume = mortar_weight_volume * mortar_dry_volume_factor
    total_cement_volume = (mortar_dry_volume * cement_sand_ratio / (cement_sand_ratio + sand_part)) / cement_bag_volume
    total_sand_volume = mortar_dry_volume * sand_part / (cement_sand_ratio + sand_part)
    skilled_labour_nos = work_volume / skilled_labour
    unskilled_labour_nos = work_volume / unskilled_labour

    # be careful about handling 'pct'
    # 'o_value()' can be mistakenly typed as 'o_value' which will prevent calculation
    # float can be typed as '0.5'
    # input arg, processing variable and output parameter names may clash and result in incorrect output

    return {
        'Brick': Qty(total_number_of_bricks, 'nos'),
        # | adding a unit will enable cost calculation in conv()
        'Cement': Qty(total_cement_volume, 'bag'),
        'Sand': Qty(total_sand_volume, 'inch**3').to('cft'),
        'Brick Work Volume': Qty(work_volume, 'inch**3').to('cft'),
        'Skilled Labour': Qty(skilled_labour_nos, 'manday'),
        'Unskilled Labour': Qty(unskilled_labour_nos, 'manday')
    }


def plaster__info(): return {
    'title': 'Estimate Cement and Sand for Plaster work',
    'schema': {
        'work_side': {'type': 'radio', 'choices': {1: 'One Side', 2: 'Both Side'}},
    },
    'step2': [
        {'step': 'cost', 'caption': 'Calculate Cost of Materials',
         'spec': {'exclude': ['Plaster Work Area']}
         },
    ],
    'col': 2,
}


def plaster(work_thickness='0.5 inch', work_length='12 ft', work_width='10 ft',
            work_side=2, cement_sand_ratio: qfl = 1.0, sand_part=4.0,
            mortar_dry_volume_factor=1.5, cement_bag_volume='1.25 ft**3/bag',
            skilled_labour='75 sft/manday',
            unskilled_labour='50 sft/manday'
            ):
    work_thickness = Qty(work_thickness, 'inch').val
    work_length = Qty(work_length, 'inch').val
    work_width = Qty(work_width, 'inch').val
    work_side = int(work_side)
    cement_bag_volume = Qty(cement_bag_volume, 'inch**3/bag').val
    skilled_labour = Qty(skilled_labour, 'inch**2/manday').val
    unskilled_labour = Qty(unskilled_labour, 'inch**2/manday').val

    work_volume = work_length * work_thickness * work_width * work_side
    work_area = work_length * work_width * work_side
    mortar_dry_volume = work_volume * mortar_dry_volume_factor
    parts = (cement_sand_ratio + sand_part)
    total_cement_volume = (mortar_dry_volume * cement_sand_ratio / parts) / cement_bag_volume
    total_sand_volume = mortar_dry_volume * sand_part / parts
    skilled_labour_nos = work_area / skilled_labour
    unskilled_labour_nos = work_area / unskilled_labour

    return {
        'Cement': Qty(total_cement_volume, 'bag'),
        'Sand': Qty(total_sand_volume, 'inch**3').to('cft'),
        'Plaster Work Area': Qty(work_area, 'inch**2').to('sft'),
        'Skilled Labour': Qty(skilled_labour_nos, 'manday'),
        'Unskilled Labour': Qty(unskilled_labour_nos, 'manday')
    }


if __name__ == '__main__':
    print(plaster())
