# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

import pandas as pd


def resize_df(df: pd.DataFrame, nrow: int, ncol: int, keep_last_ncol: int = 0) -> pd.DataFrame:
    to_be_ncol = max(min(int(ncol), 100), 0)
    to_be_nrow = max(min(int(nrow), int(10000 / to_be_ncol)), 0)
    as_is_nrow = len(df)
    as_is_ncol = len(df.columns) - keep_last_ncol
    add_row = 0
    add_col = 0

    if to_be_nrow > 0:
        add_row = to_be_nrow - as_is_nrow

    if to_be_ncol > 0:
        add_col = to_be_ncol - as_is_ncol

    if add_row > 0:
        # add row
        # https://stackoverflow.com/questions/41764226/append-empty-rows-to-dataframe-in-pandas
        df = df.reindex(df.index.union([r for r in range(as_is_nrow, as_is_nrow + add_row)]))
    elif add_row < 0:
        # del row
        df = df.drop([r for r in range(as_is_nrow + add_row, as_is_nrow)])

    if add_col > 0:
        # add col
        # https://stackoverflow.com/questions/30926670/add-multiple-empty-columns-to-pandas-dataframe
        cols = [f'C{c}' for c in range(as_is_ncol + 1, as_is_ncol + add_col + 1)]
        df = pd.concat([df, pd.DataFrame(columns=cols)])
    elif add_col < 0:
        # del col
        cols = df.columns[[c for c in range(as_is_ncol + add_col, as_is_ncol)]]
        df = df.drop(columns=cols)

    return df


def to_df(buff_or_url, delimiter=',', quoting='1'):
    if quoting == '9':  # remove anyway
        quoting = '1'
        anyway = True
    else:
        anyway = False

    if buff_or_url:
        df = pd.read_csv(buff_or_url, delimiter=delimiter, quotechar='"', quoting=int(quoting), thousands=',')
        df = df.astype(object)
        df.fillna('', inplace=True)
        # example url: https://raw.githubusercontent.com/npradaschnor/Pima-Indians-Diabetes-Dataset/master/diabetes.csv
    else:
        raise Exception(f'Error (CD): Not a valid CSV format')

    if anyway:
        # claenup qoutes
        # https://stackoverflow.com/questions/72043503/python-pandas-read-csv-quote-issue-impossible-to-separate-data
        df.columns = df.columns.str.replace('"', '')
        for i, col in enumerate(df.columns):
            try:
                df.iloc[:, i] = df.iloc[:, i].str.replace('"', '')
            except:
                pass
    return df


def validated_col(cols: list, idx: int, cname: str = '') -> str:
    c = cols[idx] if cname == '' else cname
    if c in cols:
        return c
    else:
        raise Exception(f"Column [{c}] not found in the table")
