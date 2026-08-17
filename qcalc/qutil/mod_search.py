# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

# import nltk
from fuzzywuzzy import fuzz
# from nltk.corpus import wordnet as wn
import re

FzThold = 70  # 67 'bank' matches with 'an'


def _get_wordnet():
    from nltk.corpus import wordnet as wn
    return wn


def word_found(term, text_tosearch):
    raw_search_string = fr"\b{term}\b"
    return re.search(raw_search_string, text_tosearch) is not None


def match_this(term, text_to_search, fuzzy=False) -> bool:
    if not fuzzy:
        return term in text_to_search
    else:
        return fuzzy_match(term, text_to_search, threshold=FzThold)


def match_any(terms, text_to_search, fuzzy=False, semantic=False) -> bool:
    if not fuzzy:
        # return any(term in text_to_search for term in terms)
        return any(word_found(term, text_to_search) for term in terms)
    else:
        # print(terms, text_to_search, fuzzy)
        return any(fuzzy_match(term, text_to_search, threshold=FzThold, semantic=semantic)
                   for term in terms)


def fuzzy_match(term, sentence, threshold=FzThold, semantic=False):
    # Tokenize the sentence without assuming spaces between words
    words = re.findall(r'\b\w+\b', sentence)
    # Check fuzzy match for each word in the sentence
    for word in words:
        ratio = fuzz.ratio(term, word)
        if ratio >= threshold:
            return True
        if semantic:
            # Semantic similarity
            term_synonyms = get_synonyms(term)
            word_synonyms = get_synonyms(word)
            if term_synonyms.intersection(word_synonyms):
                return True
    return False


def get_synonyms(word):
    synonyms = set()
    try:
        wn = _get_wordnet()
        for syn in wn.synsets(word):
            for lemma in syn.lemmas():
                synonyms.add(lemma.name().lower())
    except LookupError:
        # If wordnet is missing, keep semantic matching non-fatal.
        return set()
    return synonyms


def find_matched_variables(expression, variable_list):
    # | Define a regular expression pattern to match variables
    variable_pattern = r'[a-zA-Z_][a-zA-Z0-9_]*'
    # | Find all matches of variables in the expression
    variables_in_expression = re.findall(variable_pattern, expression)
    # | Check if any variable from the variable_list exists in the expression
    vars_ = []
    for var in variable_list:
        if var in variables_in_expression:
            vars_.append(var)
    return vars_


def download_nltk_resources():
    import nltk
    # Check if the wordnet resource is available, if not, download it
    not_found_downloaded = False
    try:
        nltk.data.find('corpora/wordnet.zip')
    except LookupError:
        not_found_downloaded = True
        nltk.download('wordnet')

    # Check if the sentiwordnet resource is available, if not, download it
    try:
        nltk.data.find('corpora/sentiwordnet.zip')
    except LookupError:
        not_found_downloaded = True
        nltk.download('sentiwordnet')

    return not_found_downloaded


if __name__ == '__main__':
    download_nltk_resources()
    text = 'jwellery items'
    term = 'jewlry'
    print(fuzz.ratio(term, text))
    print(term in text)
    print(match_this(term, text, fuzzy=True))
    print(match_any([term, 'xyz'], text, fuzzy=True))

    term_to_match = "happy"
    sentence_to_search = "This is a joyful sentence, with some happiness."
    result = fuzzy_match(term_to_match, sentence_to_search, semantic=True)
    print(f'synonym of {term_to_match}: {get_synonyms(term_to_match)}')
    print(result)
