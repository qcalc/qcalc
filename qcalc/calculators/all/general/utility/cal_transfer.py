# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

import pandas as pd
from qcore import qtable


def trans__info():
    return {
        'initial': 'Data Transfer between Functions'
    }


def trans(transfer_queue: qtable = pd.DataFrame(
    {'Source Func': ['csv_reader'], 'Source Field': ['table'],
     'Dest Func': ['pie2_chart'], 'Dest Field': ['data']})
):
    return transfer_queue
