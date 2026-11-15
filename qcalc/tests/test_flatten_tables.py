# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha
# Tests generated with AI assistance. Reviewed and validated by the author.

import pandas as pd

import qsett

qsett.init()

from calc import flatten_tables


def _tables():
    items = pd.DataFrame(
        columns=['item', 'price', 'size', 'qty'],
        data=[
            ['sugar', 130, 'medium', 13],
            ['tea', 50, 'large', 10],
            ['condensed milk', 90, 'large', 2],
            ['milk', 80, 'small', 5],
        ],
    )
    income_statement = pd.DataFrame(
        [
            ['Sales', '', 100.0],
            ['Selling, General and Administrative', 'SG&A', 10.0],
            ['', '', ''],
            ['Earnings Before Interest and Taxes', 'EBIT', 30.0],
        ],
        columns=['Line Item', 'Acronym', 'Period'],
    )
    return {'x': items, 'Income Statement': income_statement}


def test_single_value_column_omits_column_name():
    items = pd.DataFrame(
        columns=['item', 'price'],
        data=[['sugar', 130], ['tea', 50]],
    )

    assert flatten_tables({'x': items}, 'x') == {
        'x: sugar': 130,
        'x: tea': 50,
    }


def test_multiple_value_columns_include_names_and_support_wildcard_rows():
    tables = _tables()
    tables['x'] = tables['x'].drop(columns='size')

    assert flatten_tables(tables, 'x') == {
        'x: sugar: price': 130,
        'x: sugar: qty': 13,
        'x: tea: price': 50,
        'x: tea: qty': 10,
        'x: condensed milk: price': 90,
        'x: condensed milk: qty': 2,
        'x: milk: price': 80,
        'x: milk: qty': 5,
    }
    assert flatten_tables(tables, 'x:*milk*') == {
        'x: condensed milk: price': 90,
        'x: condensed milk: qty': 2,
        'x: milk: price': 80,
        'x: milk: qty': 5,
    }


def test_table_row_labels_skip_blank_rows_and_match_acronyms():
    tables = _tables()

    assert flatten_tables(tables, 'Income Statement') == {
        'Income Statement: Sales': 100.0,
        'Income Statement: Selling, General and Administrative': 10.0,
        'Income Statement: Earnings Before Interest and Taxes': 30.0,
    }
    assert flatten_tables(tables, 'Income Statement:EBIT') == {
        'Income Statement: Earnings Before Interest and Taxes': 30.0,
    }


def test_rows_match_names_wildcards_and_any_label_column():
    tables = _tables()
    milk = {
        'x: condensed milk: price': 90,
        'x: condensed milk: qty': 2,
        'x: milk: price': 80,
        'x: milk: qty': 5,
    }

    assert flatten_tables(tables, 'x:*milk*') == milk
    assert flatten_tables(tables, 'x:small') == {
        'x: milk: price': 80,
        'x: milk: qty': 5,
    }
    assert flatten_tables(tables, 'x:milk') == {
        'x: milk: price': 80,
        'x: milk: qty': 5,
    }
    assert flatten_tables(tables, 'x:large') == {
        'x: tea: price': 50,
        'x: tea: qty': 10,
        'x: condensed milk: price': 90,
        'x: condensed milk: qty': 2,
    }


def test_column_selection_only_returns_numeric_columns():
    tables = _tables()

    assert flatten_tables(tables, 'x:milk:size') == {}
    assert flatten_tables(tables, 'x:milk:small') == {}
    assert flatten_tables(tables, 'x:milk:qty') == {'x: milk: qty': 5}


def test_row_numbers_are_one_based_and_accept_ranges():
    tables = _tables()

    assert flatten_tables(tables, 'x:2') == {
        'x: tea: price': 50,
        'x: tea: qty': 10,
    }
    assert flatten_tables(tables, 'x:1-2') == {
        'x: sugar: price': 130,
        'x: sugar: qty': 13,
        'x: tea: price': 50,
        'x: tea: qty': 10,
    }
    assert flatten_tables(tables, 'x:130') == {}
