# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

from calc import QSearch, print_search_result
from qcore import qtexta


def search__info():
    return {
        'title': 'Search Catalog'
    }


def search(search_string:qtexta=''):
    results = QSearch.perform_search(search_string)
    return print_search_result(results)
