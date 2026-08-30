# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

import ast
import importlib
import qconst

preloaded_modules = ['qapi', 'math', 'statistics']

# Optional: allow-list of standard-library modules suitable for calculators.
allowed_modules = [
    'array', 'base64', 'binascii', 'bisect', 'calendar', 'cmath',
    'collections', 'csv', 'datetime', 'decimal', 'fractions', 'functools',
    'heapq', 'itertools', 'json', 'math', 'operator', 'random', 're',
    'statistics', 'string', 'textwrap', 'unicodedata',
]

# Disallow-list (modules explicitly disallowed for security reasons)
disallowed_modules = [
    'os', 'sys', 'subprocess', 'shutil', 'pickle', 'marshal', 'socket',
    'multiprocessing', 'threading', 'ctypes', 'resource',
    'selectors', 'asyncio', 'asyncore', 'queue'
]

dangerous_keywords = [
    'exec', 'eval', 'open', 'compile', 'globals', 'locals', 'vars', 'dir', 'help',
    'getattr', 'setattr', 'delattr', 'hasattr', 'type', 'super', '__builtins__',
    'QThread', 'qreq'
]

allowed_keywords = ['__info'] # parameter to __info()

dangerous_attributes = {
    '__class__', '__mro__', '__bases__', '__subclasses__', '__globals__', '__dict__', '__code__',
    '__func__', '__self__', '__annotations__', '__closure__', '__defaults__', '__kwdefaults__',
    '__module__', '__qualname__', '__init__', '__new__', '__getattribute__', '__getattr__',
    '__setattr__', '__delattr__', '__getstate__', '__setstate__', '__reduce__', '__reduce_ex__',
    '__slots__', '__weakref__', '__iter__', '__next__', '__call__', '__getitem__', '__setitem__',
    '__delitem__', '__contains__', '__enter__', '__exit__', '__await__', '__aenter__', '__aexit__',
    '__class_getitem__', '__subclasshook__', '__instancecheck__', '__hash__', '__str__', '__repr__',
    '__format__', '__len__', '__bool__', '__int__', '__float__', '__index__', '__complex__',
    '__abs__', '__round__', '__floor__', '__ceil__', '__trunc__', '__invert__', '__neg__', '__pos__',
    '__add__', '__sub__', '__mul__', '__matmul__', '__truediv__', '__floordiv__', '__mod__',
    '__divmod__', '__pow__', '__lshift__', '__rshift__', '__and__', '__xor__', '__or__',
    '__radd__', '__rsub__', '__rmul__', '__rmatmul__', '__rtruediv__', '__rfloordiv__',
    '__rmod__', '__rdivmod__', '__rpow__', '__rlshift__', '__rrshift__', '__rand__', '__rxor__', '__ror__',
}


def validate_expression_security(code, gdict=None):
    """Common AST-based security validation shared across evaluator entry points."""
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        raise ValueError(f"Syntax error in code: {str(e)}") from e

    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            if node.id in allowed_keywords:
                continue
            if node.id in dangerous_keywords or node.id.startswith('__'):
                raise UnsafeCodeError(node.id)

        if isinstance(node, ast.Attribute):
            if node.attr in dangerous_attributes or node.attr.startswith('_'):
                raise UnsafeCodeError(node.attr)

        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name) and (func.id in dangerous_keywords or func.id.startswith('__')):
                raise UnsafeCodeError(func.id)
            if isinstance(func, ast.Attribute) and (func.attr in dangerous_attributes or func.attr.startswith('_')):
                raise UnsafeCodeError(func.attr)

        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name in disallowed_modules:
                    raise ImportError(f"Importing '{alias.name}' is disallowed.")
        elif isinstance(node, ast.ImportFrom):
            if node.module in disallowed_modules:
                raise ImportError(f"Importing from '{node.module}' is disallowed.")

    return True


class UnsafeCodeError(Exception):
    """Custom exception to handle unsafe code detection."""

    def __init__(self, keyword):
        self.keyword = keyword
        super().__init__(f"Unsafe code detected: '{keyword}' is not allowed.")


def is_code_safe(code, gdict):
    """Check if the provided code is safe to execute."""

    def safe_import(name, *args, **kwargs):
        # Check if module is explicitly disallowed
        if name in disallowed_modules:
            raise ImportError(f"Import of '{name}' is disallowed for security reasons.")

        if not qconst.ALLOW_UNSAFE_USER_CALCULATOR_IMPORTS and name not in preloaded_modules + allowed_modules:
            raise ImportError(f"Import of '{name}' is not allowed.")

        return importlib.import_module(name)

    # Preload modules and the calculator API's explicit public names into globals.
    for module_name in preloaded_modules:
        module = importlib.import_module(module_name)
        gdict[module_name] = module
        if module_name == 'qapi':
            gdict.update({name: getattr(module, name) for name in module.__all__})

    # Restrict imports to allowed modules only
    gdict['__builtins__'] = {'__import__': safe_import}

    # Shared security validation across evaluator entry points.
    validate_expression_security(code, gdict)

    return True


def safe_execute(code, safe_globals=None, safe_locals=None):
    """Main function to sanitize and execute code in a restricted environment."""
    if safe_globals is None:
        safe_globals = {}

    if safe_locals is None:
        safe_locals = {}

    if is_code_safe(code, safe_globals):
        exec(code, safe_globals, safe_locals)
        return safe_locals
    else:
        raise ValueError("Unsafe code detected")


if __name__ == '__main__':
    # Example usage
    code = """
import os

def my_function(x):
    return x + 2
"""
    try:
        mylocals = safe_execute(code)
        print(mylocals.get('my_function')(5))  # Test the function
    except (ValueError, ImportError, UnsafeCodeError) as e:
        print(e)
