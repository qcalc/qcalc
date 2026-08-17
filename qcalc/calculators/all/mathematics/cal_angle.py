# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

import numpy as np

from qcore import Qty


def sine__info(): return {'title': 'Sine of an Angle'}


def sine(x='90.0 deg'):
    """ Calculate Sine() of an angle """
    x_rad = Qty(x, 'rad')
    return np.sin(x_rad)
