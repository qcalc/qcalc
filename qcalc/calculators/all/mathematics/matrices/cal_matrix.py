# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

import numpy
import pandas as pd
import random
from qcore import qtable
from calc import QCals

mat_dict = {
    'det': numpy.linalg.det,
    'dot': numpy.dot,
    'inv': numpy.linalg.inv,
    'msum': numpy.sum,
    'prod': numpy.prod,
    'tr': numpy.transpose,
}


def np2df(np_arr):
    if isinstance(np_arr, numpy.ndarray):
        cols = [f'C{j + 1}' for j in range(np_arr.shape[1])]
        return pd.DataFrame(np_arr, columns=cols)
    else:
        return np_arr


def mat_eva(expr, x, y=None):
    expr = expr.strip()
    if expr:
        return np2df(QCals.safe_eval(expr, gdict=mat_dict, ldict={'x': x, 'y': y}))
    else:
        return 'Enter a valid matrix expression'


def bmatrix__info():
    df1 = pd.DataFrame(columns=['C1', 'C2', 'C3'],
                       data=[[i + j + random.randint(1, 10) for i in range(3)]
                             for j in range(3)])
    df2 = pd.DataFrame(columns=['C1', 'C2', 'C3'],
                       data=[[i + j + random.randint(1, 10) for i in range(3)]
                             for j in range(3)])
    return {
        'title': 'Matrix Binary Operations',
        'schema': {
            'x': {'initial': df1},
            'y': {'initial': df2},
            'operation': {
                'type': 'choice',
                'choices': ['Add', 'Subtract', 'Multiply', 'Divide', 'Expression']
            },
        }
    }


def bmatrix(x: qtable, y: qtable, operation='Add', expression: str = 'x*y-5*x+17'):
    x = x.to_numpy()
    y = y.to_numpy()
    x = x.astype(float)
    y = y.astype(float)
    z = None
    if operation == 'Add':
        z = numpy.add(x, y)
    elif operation == 'Subtract':
        z = numpy.subtract(x, y)
    elif operation == 'Multiply':
        z = numpy.multiply(x, y)
    elif operation == 'Divide':
        z = numpy.divide(x, y)
    elif operation == 'Expression':
        z = mat_eva(expression, x, y)

    return {
        'Operation': operation,
        'Result': np2df(z)
    }


def umatrix__info():
    df1 = pd.DataFrame(columns=['C1', 'C2', 'C3'],
                       data=[[i + j + random.randint(1, 10) for i in range(3)]
                             for j in range(3)])
    return {
        'title': 'Matrix Unary Operations',
        'schema': {
            'x': {'initial': df1},
            'operation': {
                'type': 'choice',
                'choices': ['Sum', 'Transpose', 'Determinant', 'Expression']
            },
        }
    }


def umatrix(x: qtable, operation='Sum', expression: str = 'x^2-5*x+17'):
    """
    You can use the follwoing matrix opeartor functions in the expression:
    |    det() - Determinant
    |    dot() - Dot Product
    |    inv() - Inverse
    |    msum() - Sum total
    |    prod() - Product
    |    tr() - Transpose
    |
    |In addition to the above you can use other usual mathmatical operators and functions
     """
    x = x.to_numpy()
    x = x.astype(float)
    z = ''
    if operation == 'Sum':
        z = numpy.sum(x)
    elif operation == 'Transpose':
        z = np2df(numpy.transpose(x))
    elif operation == 'Determinant':
        z = np2df(numpy.linalg.det(x))
    elif operation == 'Expression':
        z = mat_eva(expression, x)

    return {
        'Operation': operation,
        'Result': z
    }
