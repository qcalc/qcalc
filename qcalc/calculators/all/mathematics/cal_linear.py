# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

from qutil import xpr_coeffs
import numpy as np
from qcore.mod_anno import qlist
from sympy import symbols, Eq, solve, sympify
from sympy.abc import _clash1


def linear2__info(): return {
    'title': 'Solve Linear Equations with 2 Unknowns',
    'calculate': 'Solve'
}


def linear2(xpr1='4x+3y', rhs1_part=20.0, xpr2='-5x+9y', rhs2_part=26.0):
    """
    Solve Linear Equations with 2 unknowns

    :param xpr1: First linear expression, e.g. 4x+3y or simply 4, -3
    :param rhs1_part: Right hand side part of the first expression e.g. 20
    :param xpr2: Second linear expression, e.g. -5x+9y or simply -5, 9
    :param rhs2_part: Right hand side part of the second expression e.g. 26
    :return: 2 unknown values
    """
    coeffs1 = xpr_coeffs(xpr1)
    coeffs2 = xpr_coeffs(xpr2)
    # print(coeffs1, coeffs2)
    rhs = np.array([rhs1_part, rhs2_part])
    # print(rhs)
    lhs = np.array([coeffs1, coeffs2])
    # print(lhs, rhs)
    soln = np.linalg.solve(lhs, rhs)
    return list(soln)


def linear__info(): return {
    'title': 'Solve Linear Equations with N Unknowns',
    'calculate': 'Solve'
}


def linear(variables:str='x,y,z', equation: qlist[str] = ['x+y+z=1', 'x-y+2*z=1', '2*x-y+2*z=1']):
    vars_ = symbols(variables)
    len_var = len(vars_)
    len_equ = len(equation)
    if len_var != len_equ:
        return f'Error (LIN): Number of variables [{len_var}] and equations [{len_equ}] mismatch'

    eqns = ()  # tuple

    for i in range(len_equ):
        eq, rhs = equation[i].split('=')
        seqn = sympify(eq, locals=_clash1)
        # print(seqn)
        eqns += (Eq(seqn, float(rhs)),)
    # print(eqns)
    # print(vars_)
    result = solve(eqns, vars_)
    # print(result)
    result = {str(key): val for key, val in result.items()}
    # print(result)
    return result
