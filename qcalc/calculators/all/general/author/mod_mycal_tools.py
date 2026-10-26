# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

import re

from calc import QCals, QSearch, get_code
from qenv import PROJ_DIR
from qutil import (
    CALCULATOR_SEARCH_STOP_WORDS,
    css2strs,
    format_py_code,
    get_functions,
)

from .mod_mycal_validation import get_calculator_validation_report

_MAX_REFERENCE_CALS = 3
_MAX_REFERENCE_CODE_CHARS = 6000
_MAX_RELEVANT_CALS = 5
_SIMILAR_CALCULATOR_RESULTS = 10
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
    def _normalize_calculator_search(query):
        terms = re.findall(r'[a-z0-9_+-]+', str(query).lower())
        meaningful_terms = [
            term for term in terms
            if len(term) > 1
               and term not in CALCULATOR_SEARCH_STOP_WORDS
        ]
        return ' '.join(dict.fromkeys(meaningful_terms))

    @classmethod
    def find_relevant_calculators(cls, query, exclude_names=None):
        normalized_query = cls._normalize_calculator_search(query)
        if not normalized_query:
            return []

        excluded = {
            str(name).strip()
            for name in (exclude_names or [])
            if str(name).strip()
        }
        results = QSearch.perform_search(
            normalized_query,
            limit=_SIMILAR_CALCULATOR_RESULTS,
            node_types='c',
        )
        calculators = []

        for result in results:
            name = result['id']
            if name not in QCals.qc_user_list or name in excluded:
                continue

            code = get_code(name, show_meta=True, as_html=False)
            if not code:
                continue

            calculators.append({
                'found': True,
                'query': normalized_query,
                'name': name,
                'title': result.get('title', ''),
                'description': result.get('desc', ''),
                'tags': result.get('tags', ''),
                'score': result.get('score', 0.0),
                'code': code[:_MAX_REFERENCE_CODE_CHARS].strip(),
            })
            if len(calculators) >= _MAX_RELEVANT_CALS:
                break

        return calculators

    @classmethod
    def find_similar_calculator(cls, query, exclude_names=None):
        calculators = cls.find_relevant_calculators(query, exclude_names)
        if calculators:
            return calculators[0]

        return {
            'found': False,
            'query': cls._normalize_calculator_search(query),
            'name': '',
            'code': '',
        }

    @staticmethod
    def get_reference_calculators(reference_cals):
        names = list(dict.fromkeys(css2strs(reference_cals)))[:_MAX_REFERENCE_CALS]
        calculators = []
        missing = []

        for name in names:
            code = get_code(name, show_meta=True, as_html=False)
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
    def get_similar_calculator_context(calculator):
        if not calculator.get('found'):
            return ''
        return (
            f"# Automatically selected similar calculator: {calculator['name']}\n"
            f"# Title: {calculator['title']}\n"
            f"{calculator['code']}"
        )

    @staticmethod
    def format_calculator(code):
        formatted_code = format_py_code(code)
        return {
            'code': formatted_code,
            'functions': get_functions(formatted_code),
        }

    @staticmethod
    def validate_calculator(code):
        return get_calculator_validation_report(code)
