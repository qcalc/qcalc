# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

import pandas as pd

import qsett

qsett.init()

from qcore import as_qtable


def test_as_qtable_trims_dataframe_column_edges():
    df = pd.DataFrame({
        ' Opening Inventory   ': [10],
        'Product  ': ['A'],
    })

    out = as_qtable(df)

    assert out is df
    assert 'Opening Inventory' in out.columns
    assert 'Product' in out.columns
    assert ' Opening Inventory   ' not in out.columns
    assert 'Product  ' not in out.columns


def test_as_qtable_trims_qtbl_dict_column_edges():
    table = {
        'columns': [' Product ', ' Opening Inventory   '],
        'data': [['A', 10]],
    }

    out = as_qtable(table)

    assert list(out.columns) == ['Product', 'Opening Inventory']
