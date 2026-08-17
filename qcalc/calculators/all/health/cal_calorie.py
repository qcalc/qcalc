# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

from qcore import Qty
from calc import list2options, gender_choice, activity_choice, calorie_formula_choice


def calorie_needs__info():
    return {
        'title': 'Calorie Calculator',
        'desc': 'Calories of energy a person needs everyday',
        'schema': {
            'gender': list2options(gender_choice),
            'activity': list2options(activity_choice),
            'formula': list2options(calorie_formula_choice),
        }
    }


def calorie_needs(
    age='30.5 yr', gender='M', height='5.5 ft', weight='60.0 kg',
    activity=1.2, formula='M', body_fat='20 pct'):
    weight_kg = Qty(weight, 'kg').val
    height_cm = Qty(height, 'cm').val
    age_yr = Qty(age, 'yr').val
    fat = Qty(body_fat, 'unit').val
    bmr = 0.0
    if formula == 'M':
        if gender == 'M':
            bmr = 10 * weight_kg + 6.25 * height_cm - 5 * age_yr + 5
        else:
            bmr = 10 * weight_kg + 6.25 * height_cm - 5 * age_yr - 161
    elif formula == 'H':
        if gender == 'M':
            bmr = 13.397 * weight_kg + 4.799 * height_cm - 5.677 * age_yr + 88.362
        else:
            bmr = 9.247 * weight_kg + 3.098 * height_cm - 4.330 * age_yr + 447.593
    elif formula == 'K':
        bmr = 370 + 21.6 * (1 - fat) * weight_kg
    calorie = bmr * float(activity)
    return {
        'Maintain Weight': Qty(calorie, 'Calorie/day'),
        'Mild Weight Loss (0.5 lb/wk)': Qty(calorie - 250, 'Calorie/day'),
        'Weight Loss (1 lb/wk)': Qty(calorie - 500, 'Calorie/day'),
        'Extreme Weight Loss (2 lb/wk)': Qty(calorie - 1000, 'Calorie/day'),
    }


def bmr__info():
    return {
        'title': 'Basal Metabolic Rate (BMR)',
        'desc': 'Calculate Basal Metabolic Rate (BMR) using the Harris-Benedict equation',
        'schema': {
            'gender': list2options(gender_choice),
        },
        'step2': [
            {
                'step': 'run', 'func': 'bmi', 'caption': 'Calculate BMI',
                'spec': {'weight': 'weight', 'height': 'height'}
            }
        ],
    }


def bmr(weight='70 kg', height='175 cm', age: float = 30.0, gender='M'):
    """
    Calculate Basal Metabolic Rate (BMR) using the Harris-Benedict equation.

    Parameters:
    - weight (float): Weight in kilograms.
    - height (float): Height in centimeters.
    - age (float): Age in years.
    - gender (str): Gender, either 'M' for male or 'F' for female.

    Returns:
    - float: BMR value in cal/d (calorie per day).
    """
    weight_kg = Qty(weight, 'kg').val
    height_cm = Qty(height, 'cm').val

    if weight_kg <= 0 or height_cm <= 0 or age <= 0:
        raise ValueError("Error (BMR): Weight, height, and age must be positive values.")

    if gender == 'M':
        bmr = 88.362 + (13.397 * weight_kg) + (4.799 * height_cm) - (5.677 * age)
    else:
        bmr = 447.593 + (9.247 * weight_kg) + (3.098 * height_cm) - (4.330 * age)

    bmr_cal_per_day = Qty(bmr, 'cal/d')
    return {"Basal Metabolic Rate": bmr_cal_per_day}
