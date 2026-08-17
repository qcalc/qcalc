# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

from qcore import Qty


def heart__info():
    return {
        'title': 'Heart Condition Assessment',
    }


def heart(systolic_bp='120 mmHg', diastolic_bp='80 mmHg', fasting_glucose='100 mg/dL', hb_alc='5.0 pct',
          total_cholesterol='200 mg/dL', triglycerides='150 mg/dL', hdl_cholesterol='60 mg/dL',
          ldl_cholesterol='100 mg/dL', bmi=20.0):
    """
    Assess one's heart condition based on various health parameters.

    Parameters:
    systolic_bp: Systolic blood pressure. Defaults to '120 mmHg'.
    diastolic_bp: Diastolic blood pressure. Defaults to '80 mmHg'.
    fasting_glucose: Fasting glucose level. Defaults to '100 mg/dL'.
    hb_alc: Hemoglobin Alc level in percentage. Defaults to '5.0 pct'.
    total_cholesterol: Total cholesterol level. Defaults to '200 mg/dL'.
    triglycerides: Triglycerides level. Defaults to '150 mg/dL'.
    hdl_cholesterol: HDL cholesterol level. Defaults to '60 mg/dL'.
    ldl_cholesterol: LDL cholesterol level. Defaults to '100 mg/dL'.

    Returns:
    A string indicating the heart condition assessment.
    """
    # https://www.ba-bamail.com/health/hair-conditions/warning-these-4-numbers-can-detect-an-unhealthy-heart/
    try:
        q_systolic_bp = Qty(systolic_bp, 'mmHg')
        q_diastolic_bp = Qty(diastolic_bp, 'mmHg')
        q_fasting_glucose = Qty(fasting_glucose, 'mg/dL')
        q_hb_alc = Qty(hb_alc, 'pct')
        q_total_cholesterol = Qty(total_cholesterol, 'mg/dL')
        q_triglycerides = Qty(triglycerides, 'mg/dL')
        q_hdl_cholesterol = Qty(hdl_cholesterol, 'mg/dL')
        q_ldl_cholesterol = Qty(ldl_cholesterol, 'mg/dL')

        response = ''

        if q_systolic_bp.val > 140 or q_diastolic_bp.val > 90:
            response +=  "High blood pressure. "
        if q_fasting_glucose.val > 126 or q_hb_alc.val > 6.5:
            response += "High blood sugar. "
        if q_total_cholesterol.val > 200 or q_triglycerides.val > 150 or q_hdl_cholesterol.val < 60 or q_ldl_cholesterol.val > 100:
            response += "High cholesterol levels. "
        if bmi > 25.0:
            response += "Overweight. "
        elif bmi > 30.0:
            response += "Obese, increased risk of heart disease. "
        if response == '':
            response = "Heart condition is normal."
        else:
            response += 'Please consult a Doctor.'
        return response
    except Exception as e:
        return "Error assessing heart condition. Please check input values."


