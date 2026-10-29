# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

import ast
import inspect
import re

from jsonschema import Draft202012Validator

from calc import QCals
from qutil import (
    UnsafeCodeError,
    extract_calculator_name,
    validate_expression_security,
)

FRACTION_SCHEMA = {
    'type': 'number',
    'minimum': 0,
    'maximum': 1,
}

FIELD_SELECTOR_SCHEMA = {
    'anyOf': [
        {'type': 'string'},
        {
            'type': 'array',
            'items': {'type': 'string'},
        },
        FRACTION_SCHEMA,
    ]
}

ANYOF_SCHEMA = {
    'type': 'object',
    'additionalProperties': {
        'type': 'object',
        'properties': {
            'fields': FIELD_SELECTOR_SCHEMA,
        },
        'required': ['fields'],
        'additionalProperties': True,
    },
}

AUTOFILL_SCHEMA = {
    'type': 'object',
    'additionalProperties': {
        'type': 'object',
        'properties': {
            'fields': FIELD_SELECTOR_SCHEMA,
            'autofill': {
                'type': 'object',
                'additionalProperties': True,
            },
        },
        'required': ['fields'],
        'additionalProperties': True,
    },
}

# `related.fields` is a mapping of field names to initial values, not a selector list.
RELATED_SCHEMA = {
    'type': 'object',
    'additionalProperties': {
        'type': 'object',
        'properties': {
            'fields': {
                'type': 'object',
                'additionalProperties': True,
            },
            'relation': {
                'type': 'object',
                'additionalProperties': True,
            },
        },
        'required': ['fields'],
        'additionalProperties': True,
    },
}

SHOWHIDE_SCHEMA = {
    'type': 'object',
    'additionalProperties': {
        'type': 'object',
        'properties': {
            'fields': FIELD_SELECTOR_SCHEMA,
            'callback': {'type': 'string'},
        },
        'required': ['fields'],
        'additionalProperties': True,
    },
}

SHARED_DATA_SCHEMA = {
    'type': 'object',
    'properties': {
        'dataset_type': {'type': 'string'},
        'dataset_key': {'type': 'string'},
    },
    'additionalProperties': True,
}

TAB_SCHEMA = {
    'type': 'object',
    'additionalProperties': False,
    'properties': {
        'title': {'type': 'string'},
        'fields': FIELD_SELECTOR_SCHEMA,
    },
    'required': ['fields'],
}

BLOCK_SCHEMA = {
    'type': 'object',
    'additionalProperties': False,
    'properties': {
        'kind': {'type': 'string', 'enum': ['fields', 'tabs']},
        'column': {'type': 'integer', 'enum': [1, 2]},
        'fields': FIELD_SELECTOR_SCHEMA,
        'tabs': {
            'type': 'array',
            'items': TAB_SCHEMA,
        },
    },
}

_INFO_PROPERTY_SCHEMAS = {
    'title': {'type': 'string'},
    'desc': {'type': 'string'},
    'calculate': {'type': 'string'},
    'schema': {
        'type': 'object',
        'additionalProperties': {
            'type': 'object',
            'properties': {
                'type': {'type': 'string'},
            },
            'additionalProperties': True,
        },
    },
    'interactive': {'type': 'boolean'},
    'anyof': ANYOF_SCHEMA,
    'autofill': AUTOFILL_SCHEMA,
    'related': RELATED_SCHEMA,
    'showhide': SHOWHIDE_SCHEMA,
    'images': {'type': 'object'},
    'layout': {
        'type': 'string',
        'enum': ['lr', 'tb'],
    },
    'inp1': FIELD_SELECTOR_SCHEMA,
    'out1': FIELD_SELECTOR_SCHEMA,
    'input_columns': {'type': 'integer', 'enum': [1, 2]},
    'output_columns': {'type': 'integer', 'enum': [1, 2]},
    'input_blocks': {
        'type': 'array',
        'items': BLOCK_SCHEMA,
    },
    'output_blocks': {
        'type': 'array',
        'items': BLOCK_SCHEMA,
    },
    'onsubmit': {'type': 'string'},
    'script': {'type': 'string'},
    'kins': {'type': 'string'},
    'tags': {'type': 'string'},
    'proper': {'type': 'string'},
    'inserts': {'type': 'object'},
    'step2': {
        'type': 'array',
        'items': {
            'type': 'object',
            'properties': {
                'step': {'type': 'string'},
                'func': {'type': 'string'},
                'caption': {'type': 'string'},
                'spec': {'type': ['object', 'string']},
            },
            'required': ['step'],
            'additionalProperties': True,
        },
    },
    'single_instance': {'type': 'boolean'},
    'single_instance_key': {'type': 'string'},
    'provides_data': SHARED_DATA_SCHEMA,
    'consumes_data': SHARED_DATA_SCHEMA,
    'remember': {'type': 'boolean'},
    'table_out_all': {'type': 'boolean'},
    'api': {'type': 'boolean'},
    'fargs': {'type': 'object'},
}

# The accepted keys are the public keys of qutil.mod_info_keys plus the legacy inp1/out1 (see test_info_keys.py).
INFO_SCHEMA = {
    'type': 'object',
    'additionalProperties': False,
    'properties': _INFO_PROPERTY_SCHEMAS,
}

INFO_VALIDATOR = Draft202012Validator(INFO_SCHEMA)
CALCULATOR_VALIDATION_CHECKS = (
    'syntax',
    'security',
    'structure',
    'execution',
    'metadata',
    'default_execution',
)


class CalculatorValidationError(ValueError):
    def __init__(self, check, error):
        message = str(error)
        if isinstance(error, SyntaxError):
            message = re.sub(
                r' \(detected at line \d+\)$',
                '',
                error.msg,
            )
        super().__init__(message)
        self.check = check
        self.error_type = type(error).__name__
        self.line = getattr(error, 'lineno', None)
        self.column = getattr(error, 'offset', None)


def _validate_calculator_default_execution(local_dict, calculator_name):
    function = local_dict.get(calculator_name)
    if not inspect.isfunction(function):
        raise ValueError(f"Calculator function '{calculator_name}' was not found.")

    required = [
        parameter.name
        for parameter in inspect.signature(function).parameters.values()
        if parameter.default is inspect.Parameter.empty
           and parameter.kind in (
               inspect.Parameter.POSITIONAL_ONLY,
               inspect.Parameter.POSITIONAL_OR_KEYWORD,
               inspect.Parameter.KEYWORD_ONLY,
           )
    ]
    if required:
        raise ValueError(
            f"Cannot validate '{calculator_name}': required input(s): {', '.join(required)}."
        )

    try:
        function()
    except Exception as error:
        raise ValueError(
            f"Default values for '{calculator_name}' failed: {error}"
        ) from error


def _validate_calculator_info(local_dict, calculator_name):
    info_name = f'{calculator_name}__info'
    info_function = local_dict.get(info_name)
    if not inspect.isfunction(info_function):
        raise ValueError(f"Missing metadata function: '{info_name}'.")

    info_signature = inspect.signature(info_function)
    if len(info_signature.parameters) > 1:
        raise ValueError(f"'{info_name}' must accept zero or one argument.")

    try:
        info = (
            info_function()
            if len(info_signature.parameters) == 0
            else info_function(None)
        )
    except Exception as error:
        raise ValueError(
            f"'{info_name}' failed while building metadata: {error}"
        ) from error

    if not isinstance(info, dict):
        raise ValueError(f"'{info_name}' must return a dict.")

    errors = sorted(
        INFO_VALIDATOR.iter_errors(info),
        key=lambda error: list(error.absolute_path),
    )
    if errors:
        error = errors[0]
        path = ' / '.join(str(part) for part in error.absolute_path)
        location = f" at '{path}'" if path else ''
        raise ValueError(
            f"'{info_name}' failed validation{location}: {error.message}"
        )


def _identify_calculator(functions):
    calculator_name = extract_calculator_name(functions)
    if calculator_name:
        return calculator_name

    ordinary_functions = [
        name for name in functions if '__' not in name
    ]
    if len(ordinary_functions) == 1:
        return ordinary_functions[0]
    if not ordinary_functions:
        raise ValueError('No calculator function was found.')
    raise ValueError(
        'Cannot determine the main calculator function from '
        f'{ordinary_functions}. Define a matching __info function.'
    )


def validate_calculator_stages(user_code):
    try:
        tree = ast.parse(user_code)
    except Exception as error:
        raise CalculatorValidationError('syntax', error) from error

    try:
        validate_expression_security(user_code)
    except Exception as error:
        raise CalculatorValidationError('security', error) from error

    try:
        functions = [
            node.name
            for node in ast.walk(tree)
            if isinstance(node, ast.FunctionDef)
        ]
        calculator_name = _identify_calculator(functions)
    except Exception as error:
        raise CalculatorValidationError('structure', error) from error

    try:
        local_dict = QCals.safe_exec(user_code)
    except (ImportError, UnsafeCodeError) as error:
        raise CalculatorValidationError('security', error) from error
    except Exception as error:
        raise CalculatorValidationError('execution', error) from error

    try:
        _validate_calculator_info(local_dict, calculator_name)
    except Exception as error:
        raise CalculatorValidationError('metadata', error) from error

    try:
        _validate_calculator_default_execution(local_dict, calculator_name)
    except Exception as error:
        raise CalculatorValidationError('default_execution', error) from error

    return calculator_name


def get_calculator_validation_report(user_code):
    try:
        calculator_name = validate_calculator_stages(user_code)
    except CalculatorValidationError as error:
        failed_index = CALCULATOR_VALIDATION_CHECKS.index(error.check)
        checks = [
            {'name': name, 'passed': True, 'message': ''}
            for name in CALCULATOR_VALIDATION_CHECKS[:failed_index]
        ]
        checks.append({
            'name': error.check,
            'passed': False,
            'error_type': error.error_type,
            'message': str(error),
            'line': error.line,
            'column': error.column,
        })
        return {
            'valid': False,
            'calculator_name': '',
            'failed_check': error.check,
            'checks': checks,
            'error': str(error),
        }

    return {
        'valid': True,
        'calculator_name': calculator_name,
        'failed_check': '',
        'checks': [
            {'name': name, 'passed': True, 'message': ''}
            for name in CALCULATOR_VALIDATION_CHECKS
        ],
        'error': '',
    }


def format_calculator_validation_report(report):
    if report['valid']:
        return f"Validation successful: {report['calculator_name']}"

    failed_check = report['checks'][-1]
    stage = report['failed_check'].replace('_', ' ').title()
    lines = [
        f'Validation failed ({stage})',
        f"{failed_check['error_type']}: {failed_check['message']}",
    ]
    if failed_check.get('line') is not None:
        location = f"line {failed_check['line']}"
        if failed_check.get('column') is not None:
            location += f", column {failed_check['column']}"
        lines.append(f'Location: {location}')

    passed = [
        check['name'].replace('_', ' ').title()
        for check in report['checks']
        if check['passed']
    ]
    if passed:
        lines.append(f"Passed checks: {', '.join(passed)}")
    return '\n'.join(lines)
