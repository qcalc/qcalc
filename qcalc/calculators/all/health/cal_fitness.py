# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

import numpy as np
import pandas as pd

from qcore import Qty
from fitness_tools.composition.bodyfat import DurninWomersley, \
    JacksonPollock3Site, JacksonPollock4Site, JacksonPollock7Site
from calc import list2options, gender_choice
from .cal_bmi import bmi
from math import log10

"""
def bf2__info():
    return {
        'title': 'bf2',
        'col':['3-6','7-10'],
        # 'row': ['1-3', '4-6', '7-9'],
        'template':'v4.21'
    }
def bf2(age=30, sex='M',
        triceps=7, biceps=5, chest=8, subscapular=4,
        abdominal=6, suprailiac=10, thigh=8, axilla=3):
    return
"""


def bodyfat__info():
    return {
        'title': 'Body Fat from Skinfold Measurements',
        'col': ['3-6', '7-11'],
        # 'row': ['1-3', '4-6', '7-9'],
        'schema': {
            'sex': list2options(gender_choice)
        },
        # 'template': 'v4.21'
    }


def bodyfat(age='30.0 yr', sex='M',
            triceps='7 mm', biceps='5 mm', chest='8 mm', subscapular='4 mm',
            abdominal='6 mm', suprailiac='10 mm', thigh='8 mm', axilla='3 mm',
            show_details=False):  # , dummy=1
    age = int(Qty(age, 'yr').val)
    # print(age)
    if sex == 'M':
        sex = 'male'
    else:
        sex = 'female'
    triceps = Qty(triceps, 'mm').val
    biceps = Qty(biceps, 'mm').val
    chest = Qty(chest, 'mm').val
    subscapular = Qty(subscapular, 'mm').val
    abdominal = Qty(abdominal, 'mm').val
    suprailiac = Qty(suprailiac, 'mm').val
    thigh = Qty(thigh, 'mm').val
    axilla = Qty(axilla, 'mm').val
    bf = []
    bf_detail = []
    bf_data = []
    data_used = {'age', 'sex'}
    if triceps is not None and biceps is not None and subscapular is not None and suprailiac is not None:
        du = ['triceps', 'biceps', 'subscapular', 'suprailiac']
        data_used.update(du)
        calc_dw = DurninWomersley(age, sex, (int(triceps), int(biceps), int(subscapular), int(suprailiac)))
        bd_dw = calc_dw.body_density()
        bf_dw_si = calc_dw.siri(bd_dw)
        bf_dw_br = calc_dw.brozek(bd_dw)
        bf_dw_sc = calc_dw.schutte(bd_dw)
        bf_dw_wa = calc_dw.wagner(bd_dw)
        bf_dw_or = calc_dw.ortiz(bd_dw)
        bf.append(bf_dw_si)
        bf.append(bf_dw_br)
        bf.append(bf_dw_sc)
        bf.append(bf_dw_wa)
        bf.append(bf_dw_or)
        bf_detail.append("Durnin-Womersley-Siri")
        bf_detail.append("Durnin-Womersley-Brozek")
        bf_detail.append("Durnin-Womersley-Schutte")
        bf_detail.append("Durnin-Womersley-Wagner")
        bf_detail.append("Durnin-Womersley-Ortiz")
        bf_data.append(du)
        bf_data.append(du)
        bf_data.append(du)
        bf_data.append(du)
        bf_data.append(du)

    jp3 = False
    if chest is not None and triceps is not None and subscapular is not None and sex == 'male':
        du = ['chest', 'triceps', 'subscapular']
        data_used.update(du)
        calc_jp3 = JacksonPollock3Site(age, sex, (int(chest), int(triceps), int(subscapular)))
        jp3 = True
    elif triceps is not None and thigh is not None and suprailiac is not None:
        du = ['triceps', 'thigh', 'suprailiac']
        data_used.update(du)
        calc_jp3 = JacksonPollock3Site(age, sex, (int(triceps), int(thigh), int(suprailiac)))
        jp3 = True
    if jp3:
        bd_jp3 = calc_jp3.body_density()
        bf_jp3_si = calc_jp3.siri(bd_jp3)
        bf_jp3_br = calc_jp3.brozek(bd_jp3)
        bf_jp3_sc = calc_jp3.schutte(bd_jp3)
        bf_jp3_wa = calc_jp3.wagner(bd_jp3)
        bf_jp3_or = calc_jp3.ortiz(bd_jp3)
        bf.append(bf_jp3_si)
        bf.append(bf_jp3_br)
        bf.append(bf_jp3_sc)
        bf.append(bf_jp3_wa)
        bf.append(bf_jp3_or)
        bf_detail.append("Jackson-Pollock-3Site-Siri")
        bf_detail.append("Jackson-Pollock-3Site-Brozek")
        bf_detail.append("Jackson-Pollock-3Site-Schutte")
        bf_detail.append("Jackson-Pollock-3Site-Wagner")
        bf_detail.append("Jackson-Pollock-3Site-Ortiz")
        bf_data.append(du)
        bf_data.append(du)
        bf_data.append(du)
        bf_data.append(du)
        bf_data.append(du)

    if abdominal is not None and triceps is not None and thigh is not None and suprailiac is not None:
        du = ['abdominal', 'triceps', 'thigh', 'suprailiac']
        data_used.update(du)
        calc_jp4 = JacksonPollock4Site(age, sex, (int(abdominal), int(triceps), int(thigh), int(suprailiac)))
        bf_jp4 = calc_jp4.body_fat()
        bf.append(bf_jp4)
        bf_detail.append("Jackson-Pollock-4Site")
        bf_data.append(du)

    if biceps is not None and chest is not None and subscapular is not None and abdominal is not None and \
        suprailiac is not None and thigh is not None and axilla is not None:
        du = ['biceps', 'chest', 'subscapular', 'abdominal', 'suprailiac', 'thigh', 'axilla']
        data_used.update(du)
        calc_jp7 = JacksonPollock7Site(age, sex, (int(biceps), int(chest), int(subscapular),
                                                  int(abdominal), int(suprailiac), int(thigh), int(axilla)))
        bd_jp7 = calc_jp7.body_density()
        bf_jp7_si = calc_jp7.siri(bd_jp7)
        bf_jp7_br = calc_jp7.brozek(bd_jp7)
        bf_jp7_sc = calc_jp7.schutte(bd_jp7)
        bf_jp7_wa = calc_jp7.wagner(bd_jp7)
        bf_jp7_or = calc_jp7.ortiz(bd_jp7)
        bf.append(bf_jp7_si)
        bf.append(bf_jp7_br)
        bf.append(bf_jp7_sc)
        bf.append(bf_jp7_wa)
        bf.append(bf_jp7_or)
        bf_detail.append("Jackson-Pollock-7Site-Siri")
        bf_detail.append("Jackson-Pollock-7Site-Brozek")
        bf_detail.append("Jackson-Pollock-7Site-Schutte")
        bf_detail.append("Jackson-Pollock-7Site-Wagner")
        bf_detail.append("Jackson-Pollock-7Site-Ortiz")
        bf_data.append(du)
        bf_data.append(du)
        bf_data.append(du)
        bf_data.append(du)
        bf_data.append(du)

    bcnt = len(bf)
    if bcnt == 0:
        raise Exception('Error (BF): Not enough data')

    ret = {
        'Body Fat Average (%)': np.average(bf),
        'Body Fat Max (%)': np.max(bf),
        'Body Fat Min (%)': np.min(bf),
        'Standard Deviation': np.std(bf),
        'Method Count': bcnt,
        'Data Used': ', '.join(sorted(data_used))
    }

    if show_details:
        df = pd.DataFrame([bf_detail, bf, bf_data]).transpose()
        df.columns = ['Method', 'Body Fat %', 'Data Used']
        ret.update({'Methods': df})

    return ret


def bodyfat2__info():
    return {
        'title': 'Body Fat from Weight and Height',
        'schema': {
            'sex': list2options(gender_choice)
        },
        'showhide': {
            'sex': {'fields': ['hip'], 'callback':"'@'=='F'"}
        },
        # 'template': 'v4.21',
    }


# https://www.calculator.net/body-fat-calculator.html
def bodyfat2(age='30.0 yr', sex='M', weight='60.0 kg', height='175.0 cm',
             neck='48.0 cm', waist='90.0 cm', hip='95.0 cm'):
    bmi_r = bmi(weight, height)
    bmi_v = bmi_r['BMI'].val

    # Metric Units yr, kg, cm
    age = Qty(age, 'yr').val
    # weight = Qty(weight, 'kg').val
    height = Qty(height, 'cm').val
    neck = Qty(neck, 'cm').val
    waist = Qty(waist, 'cm').val
    hip = Qty(hip, 'cm').val

    # BMI method
    if sex == 'M' and age > 18.0:
        # for adult males
        bf_bmi = 1.20 * bmi_v + 0.23 * age - 16.2
    elif sex == 'F' and age > 18.0:
        # for adult females
        bf_bmi = 1.20 * bmi_v + 0.23 * age - 5.4
    elif sex == 'M':
        # for boys
        bf_bmi = 1.51 * bmi_v - 0.70 * age - 2.2
    elif sex == 'F':
        # for girls
        bf_bmi = 1.51 * bmi_v - 0.70 * age + 1.4

    # US Navy method, using Metric Unit Formula (yr, kg, cm)
    if sex == 'M':
        # SI, Metric Units
        bf_navy = 495.0 / (1.0324 - 0.19077 * log10(waist - neck) + 0.15456 * log10(height)) - 450.0
    else:
        # SI, Metric Units
        bf_navy = 495.0 / (1.29579 - 0.35004 * log10(waist + hip - neck) + 0.22100 * log10(height)) - 450.0

    return {
        'Body Fat (%) US Navy Method': bf_navy,
        'Body Fat (%) BMI Method': bf_bmi
    }
