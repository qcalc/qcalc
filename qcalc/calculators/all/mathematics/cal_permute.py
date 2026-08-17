# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

import itertools
from qcore import qtexta, QScreen
from qutil import css2strs


def permute__info():
    return {
        'title': 'Compute Permutations of a list of values',
        'schema': {
            'n': {'attrs': {'max': 7, 'min': 1}}
        },
    }


def permute(values: qtexta = 'Apple, Orange, Banana', n: int = 2):
    lv = css2strs(values)
    if len(lv) >= n:
        plist = list(itertools.permutations(lv, n))
        out = QScreen()
        for i,lst in enumerate(plist):
            out.write(f"{i+1}. {', '.join(lst)}")
        return out.flush()
    else:
        return values
