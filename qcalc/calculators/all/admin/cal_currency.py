# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

from calc import update_currency


def upcur__info():
    return {'title': 'Update Currency Rates'}


def upcur():
    update_msg = update_currency()
    return update_msg
