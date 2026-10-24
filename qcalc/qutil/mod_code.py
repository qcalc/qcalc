# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

import autopep8
import ast
import qconst


def extract_calculator_name(functions: list):
    if not functions:
        return ''

    metadata_functions = []
    for fname in functions:
        if '__' not in fname:
            continue  # Main calculator or ordinary helper function.

        function_prefix, _, meta_name = fname.rpartition('__')
        meta = f'__{meta_name}'
        if meta not in qconst.KNOWN_METAS:
            raise Exception(f"Error (ECP): '{fname}' meta '{meta}' is not a known meta {qconst.KNOWN_METAS}")
        metadata_functions.append((fname, function_prefix, meta))

    info_functions = [
        item for item in metadata_functions if item[2] == '__info'
    ]
    if not info_functions:
        return ''
    if len(info_functions) > 1:
        raise Exception(
            f"Error (ECP): Multiple calculator info functions found: "
            f"{[item[0] for item in info_functions]}"
        )

    prefix = info_functions[0][1]
    if prefix not in functions:
        raise Exception(f"Error (ECP): Function '{prefix}' is not defined but meta '{prefix}__info' is defined")

    for fname, function_prefix, _ in metadata_functions:
        if function_prefix != prefix:
            raise Exception(
                f"Error (ECP): '{fname}' prefix '{function_prefix}' mismatches with '{prefix}'"
            )

    return prefix


def ensure_calculator_info(code: str, cal_name=''):
    """
    Ensure that the code contains a function named <calculator_name>__info().
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
    determined_name = extract_calculator_name(functions)
    if determined_name == '':
        if cal_name:
            if cal_name not in functions:
                raise Exception(
                    f"Error (EIF): Specified calculator function '{cal_name}' is not defined"
                )
            determined_name = cal_name
        else:
            ordinary_functions = [
                fname for fname in functions if '__' not in fname
            ]
            if len(ordinary_functions) == 1:
                determined_name = ordinary_functions[0]
            elif not ordinary_functions:
                raise Exception(
                    "Error (EIF): No calculator function is defined"
                )
            else:
                raise Exception(
                    "Error (EIF): Cannot determine the main calculator "
                    f"function from {ordinary_functions}. Define an "
                    "'<calculator>__info' function or specify cal_name."
                )
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
