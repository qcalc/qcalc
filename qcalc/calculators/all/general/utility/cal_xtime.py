# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

import timeit
from qcore import Qty
from calc import QCals


def xtime__info():
    return {
        'title': 'Function Execution Time',
        'schema': {'xpr': {'type': 'textarea'}}
    }


def xtime(xpr="sine('90 deg')", number_of_run=100):
    tot_xtime_s = timeit.timeit(stmt=xpr, globals=QCals.qfunc_dict, number=number_of_run)
    avg_xtime_ms = tot_xtime_s * 1000 / number_of_run
    return {
        'Total Execution Time': Qty(tot_xtime_s, 's'),
        'Average Execution Time': Qty(avg_xtime_ms, 'milli*s')
    }
