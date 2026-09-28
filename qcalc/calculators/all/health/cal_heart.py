# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

from qcore import Qty


def heart__info():
    return {
        'title': 'Heart Condition Assessment',
        'schema': {
            'systolic_bp': {
                'help_text': 'Normal adult resting systolic BP is typically about 90 to 119 mmHg; elevated risk starts at 140 mmHg or higher.'
            },
            'diastolic_bp': {
                'help_text': 'Normal adult resting diastolic BP is typically about 60 to 79 mmHg; elevated risk starts at 90 mmHg or higher.'
            },
            'fasting_glucose': {
                'help_text': 'Normal fasting plasma glucose is typically 70 to 99 mg/dL; diabetes threshold is 126 mg/dL or higher.'
            },
            'hb_alc': {
                'help_text': 'Normal HbA1c is generally below 5.7 percent; diabetes threshold is 6.5 percent or higher.'
            },
            'total_cholesterol': {
                'help_text': 'Desirable total cholesterol is below 200 mg/dL.'
            },
            'triglycerides': {
                'help_text': 'Normal fasting triglycerides are below 150 mg/dL.'
            },
            'hdl_cholesterol': {
                'help_text': 'Higher HDL is generally protective; 60 mg/dL or higher is typically considered desirable.'
            },
            'ldl_cholesterol': {
                'help_text': 'Optimal LDL cholesterol is below 100 mg/dL.'
            },
            'bmi': {
                'help_text': 'Normal BMI range is 18.5 to 24.9; 25.0 to 29.9 is overweight, and 30.0 or higher is obese.'
            },
        },
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
    try:
        q_systolic_bp = Qty(systolic_bp, 'mmHg')
        q_diastolic_bp = Qty(diastolic_bp, 'mmHg')
        q_fasting_glucose = Qty(fasting_glucose, 'mg/dL')
        q_hb_alc = Qty(hb_alc, 'pct')
        q_total_cholesterol = Qty(total_cholesterol, 'mg/dL')
        q_triglycerides = Qty(triglycerides, 'mg/dL')
        q_hdl_cholesterol = Qty(hdl_cholesterol, 'mg/dL')
        q_ldl_cholesterol = Qty(ldl_cholesterol, 'mg/dL')
        q_bmi = float(bmi)

        # Reject impossible or non-sensical values.
        if (
            q_systolic_bp.val <= 0 or
            q_diastolic_bp.val <= 0 or
            q_fasting_glucose.val <= 0 or
            q_hb_alc.val < 0 or
            q_total_cholesterol.val <= 0 or
            q_triglycerides.val <= 0 or
            q_hdl_cholesterol.val <= 0 or
            q_ldl_cholesterol.val <= 0 or
            q_bmi <= 0
        ):
            raise ValueError('Error (HEA): Lower-bound validation failed')

        has_high_bp = q_systolic_bp.val >= 140 or q_diastolic_bp.val >= 90
        has_low_bp = q_systolic_bp.val < 90 or q_diastolic_bp.val < 60
        has_high_sugar = q_fasting_glucose.val >= 126 or q_hb_alc.val >= 6.5
        has_low_sugar = q_fasting_glucose.val < 70

        lipid_findings = []
        if q_total_cholesterol.val >= 200:
            lipid_findings.append("high total cholesterol")
        if q_triglycerides.val >= 150:
            lipid_findings.append("high triglycerides")
        if q_hdl_cholesterol.val <= 60:
            lipid_findings.append("low HDL cholesterol")
        if q_ldl_cholesterol.val >= 100:
            lipid_findings.append("high LDL cholesterol")
        is_underweight = q_bmi < 18.5
        is_obese = q_bmi > 30.0
        is_overweight = q_bmi > 25.0 and not is_obese

        findings = []
        if has_high_bp:
            findings.append("High blood pressure.")
        if has_high_sugar:
            findings.append("High blood sugar.")
        if lipid_findings:
            findings.append("Lipid profile concerns: " + ", ".join(lipid_findings) + ".")
        if is_obese:
            findings.append("Obese, increased risk of heart disease.")
        if is_overweight:
            findings.append("Overweight.")
        if is_underweight:
            findings.append("Underweight.")
        if has_low_bp:
            findings.append("Low blood pressure.")
        if has_low_sugar:
            findings.append("Low blood sugar.")

        if not findings:
            response = "Heart condition is normal."
        else:
            response = " ".join(findings) + " Please consult a Doctor."
        return response
    except (TypeError, ValueError, AttributeError):
        return "Error (HEA): Error assessing heart condition. Please check input values."
