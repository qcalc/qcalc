# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

from qcore import Qty
from calc import dict2options, FLD_GENDER_CHOICE


def crcl__info():
    return {
        'title': 'Calculate Creatinine Clearance',
        'schema': {
            'sex': dict2options(FLD_GENDER_CHOICE, initial='M', type='radio'),
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
