# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

import pandas as pd
import pandera as pa
from qcore import Qty, qformat_q, str_type
from datetime import date
from qutil import is_str_date, nzs


class QTable:
    def __init__(self, df: pd.DataFrame, schema: pa.DataFrameSchema = None):
        self.df: pd.DataFrame = df
        self.schema: pa.DataFrameSchema = schema

    def titles(self):
        return list(self.df.columns)

    def types(self):
        if self.schema:
            dtypes = self.schema.dtypes
        else:
            dtypes = {}
            for col in self.titles():
                val = self.df[col][0]  # | determine type from first value
                dtypes[col] = _table_val2type(val)
        return dtypes

    def format(self):
        dtypes = self.types()
        for col in dtypes:
            if dtypes[col] == 'qtystr':
                # | self.df[col] = self.df[col].apply(qformat_q)
                for index, row in self.df.iterrows():
                    self.df.iloc[index][col] = qformat_q(Qty(row[col])) if nzs(row[col]) != '' else ''
            elif dtypes[col] == 'qty':
                # | self.df[col] = self.df[col].apply(qformat_q)
                for index, row in self.df.iterrows():
                    self.df.iloc[index][col] = qformat_q(row[col]) if nzs(row[col]) != '' else ''


def _table_val2type(val):
    if val is None:
        return 'unknown'
    elif isinstance(val, float):
        return 'float'
    elif isinstance(val, Qty):
        return 'qty'
    elif isinstance(val, bool):
        return 'bool'
    elif isinstance(val, int):
        return 'int'
    elif isinstance(val, date):
        return 'date'
    elif isinstance(val, str):
        return _table_str2type(val)
    else:
        return 'unknown'


def _table_str2type(value):
    value = value.strip()
    otype, sunit, ln = str_type(value)
    if otype == 'uom':
        return 'uom'
    elif otype == 'qty':
        return 'qtystr'
    elif is_str_date(value):
        return 'date'
    else:
        return 'str'
