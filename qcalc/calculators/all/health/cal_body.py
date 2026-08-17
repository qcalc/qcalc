# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

# Gender, Age, Weight, Height, Physical activity Level, Country
from qcore import Qty


def water_intake__info():
    return {
        'title': 'Water Intake Calculator'
    }


def water_intake(weight='60.0 kg'):
    weight_kg = Qty(weight, 'kg').val
    intake_min = Qty(weight_kg * 0.03, 'l/d')
    intake_max = Qty(weight_kg * 0.035, 'l/d')
    return {
        'Water Intake (min)': intake_min,
        'Water Intake (max)': intake_max
    }


def target_heart_rate__info():
    return {
        'title': 'Target Heart Rate'
    }


def target_heart_rate(age='30.0 yr', resting_heart_rate=72, training_intensity=0.4):
    # https://www.heartonline.org.au/resources/calculators/target-heart-rate-calculator
    # https://www.calculatorsoup.com/calculators/health/target-heart-rate-zone-calculator.php
    age_yr = Qty(age, 'yr').val
    max_heart_rate = 206.9 - 0.67 * age_yr  # or simple formula: 220 - age
    heart_rate_reserve = max_heart_rate - resting_heart_rate
    thr_min = heart_rate_reserve * training_intensity + resting_heart_rate
    thr_max = max_heart_rate * training_intensity
    return {
        'Target Heart Rate (min)': thr_min,
        'Target Heart Rate (max)': thr_max
    }
