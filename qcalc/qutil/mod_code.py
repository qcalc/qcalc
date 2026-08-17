# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

import autopep8
import ast
import qconst


def extract_common_prefix(functions: list):
    if not functions:
        return ''

    prefix = ''
    for fname in functions:
        if '__' in fname:
            parts = fname.split('__')
            if not prefix:
                prefix = parts[0]
            elif prefix != parts[0]:
                raise Exception(f"Error (ECP): '{fname}' prefix '{parts[0]}' mismatches with '{prefix}'")

            meta = f'__{parts[-1]}'
            if meta not in qconst.KNOWN_METAS:
                raise Exception(f"Error (ECP): '{fname}' meta '{meta}' is not a known meta {qconst.KNOWN_METAS}")
    if prefix != '' and prefix not in functions:
        raise Exception(f"Error (ECP): Function '{prefix}' is not defined but meta '{prefix}__info' is defined")
    return prefix


def ensure_info_function(code: str, cal_name=''):
    """
    Ensure that the code contains a function named <last_function_name>__info().
    If not found, add the function to the code with a dummy implementation.

    Args:
        code (str): The original code as a string.
        cal_name (str): Calculator name

    Returns:
        str: The modified or unmodified code.
    """

    # Get the list of functions defined in the code
    if code == '':
        cal_name = 'newcal' if cal_name == '' else cal_name
        code = f"""
def {cal_name}(x=1.0, y=1.0):
    z = x + y
    return {{'result': z}}

def {cal_name}__info():
    return {{
        'title': 'Calculate newcal'
    }}
"""
    functions = get_functions(code)
    determined_name = extract_common_prefix(functions)
    if determined_name == '':
        if cal_name != '' and cal_name in functions:
            pass
        elif cal_name == '' and len(functions) == 1 and '__' not in functions[0]:
            cal_name = functions[0]
        elif cal_name == '':
            cal_name = 'newcal'
        determined_name = cal_name
    info_name = f"{determined_name}__info"

    if info_name in functions:
        return code, functions  # Return the original code if the function exists

    # Define the dummy __info function
    dummy_info_function = f"""
def {info_name}():
    return {{
        'title': 'Calculate {determined_name}'
    }}
"""
    # Add the dummy function to the original code
    modified_code = code + "\n" + dummy_info_function.strip()
    modified_functions = functions + [info_name]
    return modified_code, modified_functions


def format_py_code(code):
    formatted_code = autopep8.fix_code(
        code,
        options={
            'max_line_length': 79,  # Set maximum line length
            'aggressive': 1,  # Aggressiveness level (1 or 2)
            'indent_size': qconst.CODE_TAB,
        }
    )
    return formatted_code


def get_functions(code_string):
    tree = ast.parse(code_string)
    functions = [node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
    return functions
