# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

from calc import update_currency, redis_publish_action


def upcur__info():
    return {'title': 'Update Currency Rates'}


def upcur():
    update_msg = update_currency(update_now=True)
    redis_publish_action(
        channel="qcalc_channel",
        action="update_currency",
        update_now=False  # update_now False=already downloaded, upload only
    )
    return update_msg
