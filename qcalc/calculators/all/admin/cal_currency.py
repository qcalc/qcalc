# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

from calc import StdList, load_currency, cur_as_of
from qcore import add_currencies

def upcur__info():
    return {'title': 'Update Currency Rates'}


def upcur():
    cl = load_currency(update_now=True)
    StdList.currency_list.update(cl)  # update the global list
    add_currencies(StdList.currency_list, StdList.currency_desc)
    return "Currency updated as of: " + cur_as_of()
