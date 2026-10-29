# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha
# Tests generated with AI assistance. Reviewed and validated by the author.

import qsett

qsett.init()

from qutil import css2dict


def test_css2dict_basic_and_whitespace():
    assert css2dict(" a = 1 , b=two ,c=3") == {"a": "1", "b": "two", "c": "3"}


def test_css2dict_blank_and_none():
    assert css2dict("") == {}
    assert css2dict("   ") == {}
    assert css2dict(None) == {}


def test_css2dict_skips_empty_items_and_empty_keys():
    assert css2dict("a=1,,=5, ,b=2,") == {"a": "1", "b": "2"}


def test_css2dict_item_without_separator_maps_to_empty_string():
    assert css2dict("a=1,flag") == {"a": "1", "flag": ""}


def test_css2dict_value_may_contain_pair_separator_and_last_duplicate_wins():
    assert css2dict("url=a=b,k=1,k=2") == {"url": "a=b", "k": "2"}


def test_css2dict_custom_separators_and_dict_passthrough():
    assert css2dict("a:1;b:2", separator=";", pair_separator=":") == {"a": "1", "b": "2"}
    source = {"x": "1"}
    assert css2dict(source) is source
