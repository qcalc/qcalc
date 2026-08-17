# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

from qcore import Qty
from calc import list2options, gender_choice


def crcl0__info():
    return {
        'schema': {
            'sex': {
                'type': 'choice',
                'initial': 'M',
                'choices': {'M': 'Male', 'F': 'Female'}
            }
        }
    }


def crcl0(age=55.0, age_u='yr',
          weight=65.0, weight_u='kg',
          serum_creatinine=1.0, cr_u='mg/dl',
          sex='F'
          ):
    """
    Estimated Creatinine Clearance = [[140 - age(yr)]*weight(kg)]/[72*serum Cr(mg/dL)]
    (multiply by 0.85 for women).
    Source: https://www.mcw.edu/calculators/creatinine-clearance
    """
    age_yr = Qty(age, age_u, 'yr')
    # age_yr.to('yr')
    weight_kg = Qty(weight, weight_u, 'kg')
    # weight_kg.to('kg')
    serum_creatinine_mgdl = Qty(serum_creatinine, cr_u, 'mg/dl')
    # serum_creatinine_mgdl.to('mg/dl')
    temp = Qty((140 - age_yr.getValue()) * weight_kg.value / (72 * serum_creatinine_mgdl.getValue()), 'ml/min')
    if sex == 'F':
        temp = temp * 0.85
    return temp


def crcl__info():
    return {
        'title': 'Calculate Creatinine Clearance',
        'schema': {
            'sex': list2options(gender_choice, initial='M', type='radio'),
        }
    }


def crcl(age='55.0 yr', weight='65.0 kg',
         serum_creatinine='1.0 mg/dl', sex='M'):
    age_yr = Qty(age, 'yr').value
    weight_kg = Qty(weight, 'kg').value
    serum_creatinine_mgdl = Qty(serum_creatinine, 'mg/dl').value
    temp = Qty((140 - age_yr) * weight_kg / (72 * serum_creatinine_mgdl), 'ml/min')
    if sex == 'F':
        temp = temp * 0.85
    return temp
