from qcore import Qty


def rcc_column_materials__info():
    return {
        'title': 'RCC Column Material Requirement',
        'desc': (
            'Estimate reinforcement steel, concrete, sand and khoa for an RCC column. '
            'Concrete is based on a 1:1.5:3 nominal mix with a dry-volume factor of 1.54. '
            'Longitudinal bars and stirrups are included in the steel quantity. '
            'Nominal concrete cover is 40 mm and each stirrup includes 10 bar diameters '
            'for each hook.'
        ),
        'calculate': 'Estimate',
        'schema': {
            'number_of_bars': {
                'type': 'integer',
                'initial': 8,
                'label': 'Number of longitudinal bars',
            },
        },
    }


def rcc_column_materials(
    column_length='3 m',
    column_width='300 mm',
    column_depth='300 mm',
    number_of_bars=8,
    bar_size='16 mm',
    stirrup_spacing='150 mm',
    stirrup_size='8 mm',
):
    # ---------------------------------------------------------
    # Column dimensions
    # ---------------------------------------------------------

    length = Qty(column_length, 'm')
    width = Qty(column_width, 'm')
    depth = Qty(column_depth, 'm')

    # ---------------------------------------------------------
    # Reinforcement
    # ---------------------------------------------------------

    bar_dia = Qty(bar_size, 'mm')
    stirrup_dia = Qty(stirrup_size, 'mm')
    spacing = Qty(stirrup_spacing, 'mm')

    # Nominal concrete cover
    cover = Qty('40 mm')

    # ---------------------------------------------------------
    # Longitudinal bars
    #
    # Approximate bar length = column length.
    # Anchorage/lap is not included because it depends on
    # structural detailing and was not supplied as an input.
    # ---------------------------------------------------------

    longitudinal_length = (
        length * int(number_of_bars)
    )

    # Steel density = 7850 kg/m3
    bar_area = 3.141592653589793 * bar_dia ** 2 / 4
    longitudinal_volume = (
        bar_area * longitudinal_length
    )

    longitudinal_weight = (
        longitudinal_volume * Qty('7850 kg/m3')
    )

    # ---------------------------------------------------------
    # Stirrup dimensions
    #
    # Centre-line dimensions are approximated from the column
    # dimensions, cover and stirrup diameter.
    # ---------------------------------------------------------

    stirrup_width = (
        width
        - 2 * cover
        - stirrup_dia
    )

    stirrup_depth = (
        depth
        - 2 * cover
        - stirrup_dia
    )

    # 2 horizontal + 2 vertical legs + 20d hook allowance
    stirrup_length = (
        2 * stirrup_width
        + 2 * stirrup_depth
        + 20 * stirrup_dia
    )

    # Number of stirrups, including both ends.
    number_of_stirrups = (
        int(length / spacing) + 1
    )

    total_stirrup_length = (
        stirrup_length * number_of_stirrups
    )

    stirrup_area = (
        3.141592653589793
        * stirrup_dia ** 2
        / 4
    )

    stirrup_volume = (
        stirrup_area * total_stirrup_length
    )

    stirrup_weight = (
        stirrup_volume * Qty('7850 kg/m3')
    )

    total_steel = (
        longitudinal_weight + stirrup_weight
    )

    # ---------------------------------------------------------
    # Gross concrete volume
    # ---------------------------------------------------------

    gross_concrete_volume = (
        length * width * depth
    )

    # ---------------------------------------------------------
    # Reinforcement volume
    # ---------------------------------------------------------

    reinforcement_volume = (
        longitudinal_volume + stirrup_volume
    )

    # Net concrete volume
    concrete_volume = (
        gross_concrete_volume - reinforcement_volume
    )

    # ---------------------------------------------------------
    # Concrete ingredients
    #
    # Nominal mix = 1 : 1.5 : 3
    # Dry volume factor = 1.54
    #
    # Total proportion = 5.5
    # ---------------------------------------------------------

    dry_volume = (
        concrete_volume * 1.54
    )

    sand_volume = (
        dry_volume * 1.5 / 5.5
    )

    khoa_volume = (
        dry_volume * 3 / 5.5
    )

    return {
        'Longitudinal steel': Qty(longitudinal_weight, 'kg'),
        'Stirrup steel': Qty(stirrup_weight, 'kg'),
        'Total reinforcement steel': Qty(total_steel, 'kg'),
        'Concrete volume': Qty(concrete_volume, 'm3'),
        'Sand': Qty(sand_volume, 'm3'),
        'Khoa': Qty(khoa_volume, 'm3'),
        'Number of stirrups': number_of_stirrups,
    }
