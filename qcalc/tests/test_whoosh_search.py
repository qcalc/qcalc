# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha
# Tests generated with AI assistance. Reviewed and validated by the author.

import qsett

qsett.init()

from calc import QSearch


def setup_module():
    QSearch('m', True)


def test_search_filters_by_node_type_before_limiting():
    results = QSearch.perform_search(
        'mass',
        limit=5,
        node_types={'c'},
    )

    assert results
    assert len(results) <= 5
    assert all(result['node_type'] == 'c' for result in results)


def test_search_accepts_single_node_type_string():
    results = QSearch.perform_search(
        'mass',
        limit=5,
        node_types='u',
    )

    assert results
    assert all(result['node_type'] == 'u' for result in results)


def test_search_respects_custom_limit():
    results = QSearch.perform_search('interest', limit=3)

    assert len(results) <= 3


def test_body_mass_index_ranks_bmi_first():
    results = QSearch.perform_search(
        'body mass index height weight',
        node_types='c',
    )

    assert results[0]['id'] == 'bmi'


def test_search_handles_query_punctuation():
    results = QSearch.perform_search(
        'loan (payment: monthly)',
        node_types='c',
    )

    assert isinstance(results, list)


def test_search_rejects_non_positive_limit():
    try:
        QSearch.perform_search('mass', limit=0)
    except ValueError as error:
        assert str(error) == 'Search limit must be at least 1'
    else:
        raise AssertionError('Expected ValueError')
