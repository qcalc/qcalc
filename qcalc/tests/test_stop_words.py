# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha
# Tests generated with AI assistance. Reviewed and validated by the author.

from qutil import (
    CALCULATOR_SEARCH_STOP_WORDS,
    GENERAL_STOP_WORDS,
    get_wordcloud_stop_words,
)


def test_general_stop_words_use_central_profile():
    assert 'the' in GENERAL_STOP_WORDS


def test_calculator_search_profile_preserves_domain_terms():
    assert 'calculator' in CALCULATOR_SEARCH_STOP_WORDS
    assert 'please' in CALCULATOR_SEARCH_STOP_WORDS
    assert 'interest' not in CALCULATOR_SEARCH_STOP_WORDS
    assert 'date' not in CALCULATOR_SEARCH_STOP_WORDS
    assert 'amount' not in CALCULATOR_SEARCH_STOP_WORDS


def test_wordcloud_stop_words_are_exposed_as_immutable_profile():
    words = get_wordcloud_stop_words()

    assert isinstance(words, frozenset)
    assert 'the' in words
