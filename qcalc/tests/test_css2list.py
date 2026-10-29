# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha
# Tests generated with AI assistance. Reviewed and validated by the author.

from qutil import css2list, css2strs


def test_css2list_basic_and_whitespace():
    assert css2list(" a , b ,c") == ["a", "b", "c"]
    assert css2list("a") == ["a"]


def test_css2list_blank_like_input_gives_empty_list():
    for blank in (None, "", "   ", float("nan"), "none", "NA", "null"):
        assert css2list(blank) == []


def test_css2list_skips_empty_items_unlike_css2strs():
    assert css2strs("a, ,b") == ["a", "", "b"]
    assert css2list("a, ,b,") == ["a", "b"]


def test_css2list_splits_on_newlines_too():
    assert css2list("a, b\nc\r\n d,,\n") == ["a", "b", "c", "d"]


def test_css2list_lists_and_tuples_are_cleaned_and_stringified():
    assert css2list([" a ", 1, "", None]) == ["a", "1", "None"]
    assert css2list(("x", " y ")) == ["x", "y"]
    assert css2list([]) == []


def test_css2list_custom_separator():
    assert css2list("a;b; ;c", separator=";") == ["a", "b", "c"]
