# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

from qcore import Qty


def bmi__info():
    return {
        'title': 'Calculate Body Mass Index',
        'desc':
            "Body Mass Index (BMI) is a person's weight in kilograms divided by the square of height in meters.\
    A high BMI can be an indicator of high body fatness. BMI can be used to screen for weight categories\
    that may lead to health problems but it is not diagnostic of the body fatness or health of an individual.",
        'images': {
            'top': ['calc/images/obesity.png'],
        },
        'step2': [
            {
                'step': 'run', 'func': 'bmr', 'caption': 'Calculate BMR',
                'spec': {'weight': 'weight', 'height': 'height'}
            }
        ],
    }


def bmi(weight='132 lb', height='5.5 ft'):
    weight_kg = Qty(weight, 'kg')
    height_m = Qty(height, 'm')
    # print(weight_kg, height_m)
    bmi_kgpm2 = weight_kg / height_m ** 2
    return {'BMI': bmi_kgpm2}  # used in bodyfat2()
