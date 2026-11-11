# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

from qcore import qtbl

from .mod_building_materials import default_materials_table, estimate_materials

__all__ = ['building_materials', 'building_materials__info']


def building_materials__info():
    return {
        'title': 'Building Materials Estimator',
        'kins': 'building_cost',
        'tags': 'construction, estimation',
        'desc': (
            'Estimate the major materials and the labour of a one or multi-storied RCC-frame building with brick infill: '
            'cement, steel, sand, aggregate, bricks, finishes and skilled and unskilled mandays. '
            'Preliminary quantities only, not a substitute for a BOQ, structural design or bar bending schedule.'
        ),
        'calculate': 'Estimate',
        'schema': {
            'plot_length': {'help_text': 'Overall plot/building length. Example: 37 ft or 11.3 m.'},
            'plot_width': {'help_text': 'Overall plot/building width. Example: 27 ft or 8.2 m.'},
            'floors': {'type': 'integer', 'help_text': 'Number of identical floors above the foundation.'},
            'coverage': {'help_text': 'Share of length × width actually built, e.g. 90 pct for open courts.'},
            'soil': {'type': 'radio', 'choices': {'good': 'Good', 'normal': 'Normal', 'poor': 'Poor'}, 'initial': 'normal',
                     'help_text': 'Soil condition scales the footing concrete.'},
            'method': {
                'type': 'radio', 'initial': 'both',
                'choices': {'both': 'Both methods', 'detailed': 'Detailed', 'quick': 'Quick rule'},
                'help_text': 'Quick rule = area-based rule of thumb. Detailed = derived from concrete, steel, walls and mortar. '
                             'The headline quantities follow Detailed unless only Quick rule is chosen.'},
            'structure_density': {
                'type': 'radio', 'initial': 'typical',
                'choices': {'light': 'Light', 'lean': 'Lean', 'typical': 'Typical', 'heavy': 'Heavy'},
                'help_text': 'Light is for a 1-2 floor single-family house with short spans (about 4 m or less), normal seismic zone '
                             'and normal or good soil. Typical is the safer choice when unsure. Heavy is for long spans, '
                             'higher loads or taller buildings.'},
            'concrete_supply': {'type': 'radio', 'initial': 'site_mix',
                                'choices': {'site_mix': 'Site mix', 'ready_mix': 'Ready-mix'}},
            'mix': {'type': 'radio', 'initial': 'm20',
                    'choices': {'m20': 'M20 (1:1.5:3)', 'm15': 'M15 (1:2:4)', 'custom': 'Custom ratio'},
                    'help_text': 'Nominal mix by volume for site-mixed structural concrete.'},
            'mix_ratio': {'type': 'char',
                          'help_text': 'Used only for a custom mix: cement:sand:aggregate by volume, e.g. 1:1.5:3.'},
            'seismic': {'type': 'radio', 'initial': 'normal', 'choices': {'normal': 'Normal', 'high': 'High'},
                        'help_text': 'High seismic zone or coastal area adds about 15 pct to the reinforcement.'},
            'include_base_works': {'help_text': 'Include lean concrete (PCC) under footings and the ground floor, and brick soling.'},
            'finishes': {'help_text': 'Include plaster, floor screed, tiles and paint quantities.'},
            'include_labour': {
                'help_text': 'Include the detailed skilled and unskilled mandays by trade. Price the mandays with the cost calculator.'},
            'show_coefficients': {
                'label': 'Show the Coefficients tab',
                'help_text': 'Show the editable table of coefficients (member steel, mixes, labour constants, quick-rule bands).'},
            'rooms': {
                'type': 'integer',
                'help_text': 'Enclosed rooms per floor: bedrooms, living or drawing room, dining if walled, kitchen, '
                             'bathrooms, store. Open-plan spaces count once; balconies, corridors and the stair do not count.'},
            'stairs': {'help_text': 'Number of staircases, or auto (1 when there is more than one floor, otherwise none).'},
            'storey_height': {'help_text': 'Floor-to-floor height.'},
            'brick_length': {'help_text': 'Brick length with unit. Bangladesh standard 9.5 inch, India traditional 230 mm, modular 190 mm.'},
            'brick_width': {'help_text': 'Brick width with unit. Bangladesh standard 4.5 inch, India traditional 115 mm, modular 90 mm.'},
            'brick_height': {'help_text': 'Brick height with unit. Bangladesh standard 2.75 inch, India traditional 75 mm, modular 90 mm.'},
            'ext_wall_thickness': {'help_text': 'auto = one brick length plus joint, or enter a length such as 5 inch.'},
            'int_wall_thickness': {'help_text': 'auto = one brick width (half-brick wall), or enter a length such as 5 inch.'},
            'joint_thickness': {'help_text': 'Mortar joint between bricks.'},
            'masonry_mortar': {'type': 'char', 'help_text': 'Cement:sand by volume for brickwork, e.g. 1:4.'},
            'plaster_mortar': {'type': 'char',
                               'help_text': 'Cement:sand by volume for plaster and floor screed, e.g. 1:4.'},
            'mortar_dry_factor': {'help_text': 'Dry-to-wet volume of mortar, usually 1.27 to 1.33.'},
            'concrete_dry_factor': {'help_text': 'Dry-to-wet volume of concrete, usually 1.52 to 1.57.'},
            'cement_bag_volume': {'help_text': 'Volume of one cement bag, 1.225 ft³ for 50 kg at 1440 kg/m³.'},
            'brick_wastage': {'help_text': 'Brick breakage and waste.'},
            'labour_productivity': {
                'help_text': 'Labour efficiency against the book norms in the Coefficients table. 100 pct = book norms (manual handling); '
                             '80 pct raises mandays by 25 pct. Use less than 100 pct for monsoon, small crews, no hoist or congested sites.'},
            'materials_table': {
                'label': 'Coefficients',
                'help_text': 'Editable coefficients for the materials and labour estimate. Keep unique (Group, Key) rows and numeric values.',
                'attrs': {'readonly_cols': ['Group', 'Key', 'Label'], 'fixed_headers': ['Group', 'Key', 'Label', 'Value']}
            },
        },
        'showhide': {'show_coefficients': {'fields': ['materials_table'], 'callback': '@'}},
        'input_blocks': [{
            'column': 1,
            'tabs': [
                {'title': 'Building', 'fields': 'plot_length, plot_width, floors, coverage, soil'},
                {'title': 'Materials',
                 'fields': 'method, structure_density, concrete_supply, mix, mix_ratio, seismic, include_base_works, '
                           'finishes, include_labour, show_coefficients'},
                {'title': 'Walls and Stairs',
                 'fields': 'rooms, stairs, storey_height, brick_length, brick_width, brick_height, '
                           'ext_wall_thickness, int_wall_thickness'},
                {'title': 'Constants',
                 'fields': 'joint_thickness, masonry_mortar, plaster_mortar, mortar_dry_factor, concrete_dry_factor, '
                           'cement_bag_volume, brick_wastage, labour_productivity'},
                {'title': 'Coefficients', 'fields': 'materials_table'},
            ],
        }],
        'step2': [
            {'step': 'run', 'func': 'cost', 'caption': 'Calculate Cost of Materials',
             'spec': '~Footprint Area, ~Total Built-up Area, ~Concrete'},
        ],
    }


def building_materials(plot_length='37 ft', plot_width='27 ft', floors=1, coverage='100 pct', soil='normal',
                       method='both', structure_density='typical', concrete_supply='site_mix', mix='m20',
                       mix_ratio='1:1.5:3', seismic='normal', include_base_works=True, finishes=True,
                       include_labour=True, show_coefficients=False,
                       rooms=6, stairs='auto', storey_height='10 ft',
                       brick_length='9.5 inch', brick_width='4.5 inch', brick_height='2.75 inch',
                       ext_wall_thickness='auto', int_wall_thickness='auto',
                       joint_thickness='10 mm', masonry_mortar='1:4', plaster_mortar='1:4',
                       mortar_dry_factor=1.33, concrete_dry_factor=1.54, cement_bag_volume='1.225 ft^3/bag',
                       brick_wastage='5 pct', labour_productivity='100 pct',
                       materials_table: qtbl = default_materials_table()):
    return estimate_materials(
        plot_length=plot_length, plot_width=plot_width, coverage=coverage, floors=floors, soil=soil,
        materials_table=materials_table, method=method, structure_density=structure_density,
        concrete_supply=concrete_supply, mix=mix, mix_ratio=mix_ratio, seismic=seismic,
        include_base_works=include_base_works, finishes=finishes, rooms=rooms, stairs=stairs,
        storey_height=storey_height, brick_length=brick_length, brick_width=brick_width,
        brick_height=brick_height, ext_wall_thickness=ext_wall_thickness, int_wall_thickness=int_wall_thickness,
        joint_thickness=joint_thickness, masonry_mortar=masonry_mortar, plaster_mortar=plaster_mortar,
        mortar_dry_factor=mortar_dry_factor, concrete_dry_factor=concrete_dry_factor,
        cement_bag_volume=cement_bag_volume, brick_wastage=brick_wastage, include_labour=include_labour,
        labour_productivity=labour_productivity)
