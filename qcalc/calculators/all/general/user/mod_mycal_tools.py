# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

from calc import get_code
from qenv import PROJ_DIR
from qutil import css2strs, ensure_info_function, format_py_code

from .cal_mycal import validate_calculator_defaults, validate_calculator_info

_MAX_REFERENCE_CALS = 3
_MAX_REFERENCE_CODE_CHARS = 6000
_CREATION_SPEC_PATH = PROJ_DIR.path(
    'qcalc_res', 'train', 'qcalc-calculator-creation-spec.md'
)

with open(str(_CREATION_SPEC_PATH), encoding='utf-8') as _creation_spec_file:
    _CALCULATOR_CREATION_SPEC = _creation_spec_file.read().strip()


class MyCalTools:
    @staticmethod
    def get_creation_spec():
        return _CALCULATOR_CREATION_SPEC

    @staticmethod
    def get_reference_calculators(reference_cals):
        names = list(dict.fromkeys(css2strs(reference_cals)))[:_MAX_REFERENCE_CALS]
        calculators = []
        missing = []

        for name in names:
            code = get_code(name, show_meta=True)
            if not code:
                missing.append(name)
                continue
            calculators.append({
                'name': name,
                'code': code[:_MAX_REFERENCE_CODE_CHARS].strip(),
            })

        return {
            'requested': names,
            'calculators': calculators,
            'missing': missing,
        }

    @classmethod
    def get_reference_context(cls, reference_cals):
        result = cls.get_reference_calculators(reference_cals)
        calculators = result['calculators']
        missing = result['missing']

        if not result['requested']:
            return ''
        if not calculators:
            missing_text = ', '.join(missing or result['requested'])
            return f'Reference calculators requested but not found: {missing_text}'

        blocks = [
            f"# Reference calculator: {calculator['name']}\n{calculator['code']}"
            for calculator in calculators
        ]
        context = '\n\n'.join(blocks)
        if missing:
            context += f"\n\n# Missing reference calculators: {', '.join(missing)}"
        return context

    @staticmethod
    def prepare_calculator(code, cal_name_hint=''):
        prepared_code, functions = ensure_info_function(code, cal_name_hint)
        return {
            'code': format_py_code(prepared_code),
            'functions': functions,
        }

    @staticmethod
    def validate_calculator(code):
        checks = []
        validators = (
            ('metadata', validate_calculator_info),
            ('default_execution', validate_calculator_defaults),
        )

        for name, validator in validators:
            try:
                validator(code)
            except Exception as error:
                checks.append({
                    'name': name,
                    'passed': False,
                    'message': str(error),
                })
                return {
                    'valid': False,
                    'checks': checks,
                    'error': str(error),
                }
            checks.append({
                'name': name,
                'passed': True,
                'message': '',
            })

        return {
            'valid': True,
            'checks': checks,
            'error': '',
        }
