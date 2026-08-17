# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

import pandas as pd
from titlecase import titlecase
from qcore import qtexta, QScreen, qchar, qtable
from wordcloud import STOPWORDS
from functools import partial
import re
from qutil import get_synonyms, validated_col


def textcase__info():
    return {
        'title': 'Text Formatting',
        'schema': {
            'format': {
                'type': 'choice',
                'choices': [
                    ('t', 'Title Case'),
                    ('l', 'lower case'),
                    ('u', 'UPPER CASE'),
                    ('f', 'Sentence case'),
                    ('c', 'CamelCase'),
                    ('s', 'snake_case'),
                ]
            }
        },
        'showhide': {
            'format': {
                'fields': ['ignore_stopwords', 'abbreviations'],
                'callback': "'@'=='t'"
            }
        },
    }


def textcase(
    text: qtexta = "hey do you know, how to convert a string to title case "
                   "or to sentence case correctly? FYI, I need to figure it out ASAP. "
                   "It shouldn't be that difficult.",
    format='t',
    ignore_stopwords=False,
    abbreviations: qtexta = 'FYI, ASAP, i.e.'
):
    if format == 't':
        avlist = []
        if abbreviations != '':
            # avlist = abbreviations.replace(' ','').split(',')
            avlist = re.findall(r'\w+', abbreviations)

        if not ignore_stopwords:
            ftxt = titlecase(text, callback=partial(case_check, ignore=False, avlist=avlist))
        else:
            ftxt = titlecase(text, callback=partial(case_check, ignore=True, avlist=avlist))
        # Always capitalize first letter irrespective
        ftxt = ftxt[0].upper() + ftxt[1:]
    elif format == 'c':
        ftxt = text.title().replace(' ', '')
        ftxt = re.sub(r'[^\w\s]', '', ftxt)  # remove punctuations
    elif format == 'l':
        ftxt = text.lower()
    elif format == 'u':
        ftxt = text.upper()
    elif format == 'f':
        ftxt = sentence_case(text)  # text.capitalize()
    elif format == 's':
        ftxt = text.lower().replace(' ', '_')
        ftxt = re.sub(r'[^\w\s]', '', ftxt)  # remove punctuations
    else:
        ftxt = text

    return ftxt


def case_check(word, **kwargs):
    wt = word.title()
    wl = re.findall(r'\w+', word)[0].lower()  # word AsAP. becomes asap
    # print(word)
    if kwargs['ignore'] and wl in STOPWORDS:
        wt = word.lower()
    avlist = kwargs['avlist']
    # print(avlist)
    for wa in avlist:
        if wl == wa.lower():
            # print(wa)
            wt = word.lower().replace(wl, wa)  # e.g. word AsAP. becomes ASAP.
            break
    return wt


def sentence_case(text):
    # https://ideone.com/fvTezY
    # Split into sentences. Therefore, find all text that ends
    # with punctuation followed by white space or end of string.
    pattern = r'[^.!?]+[.!?](?:\s|\Z)'
    sentences = re.findall(pattern, text)
    if len(sentences) > 0:
        # Capitalize the first letter of each sentence
        sentences = [x.capitalize() for x in sentences]
        # Combine sentences
        res = ''.join(sentences)
    else:  # if there is no punctuation mark, cosider it as one sentence
        res = text.capitalize()
    return res


def synonym__info():
    return {'title': 'English Synonym of an Word'}


def synonym(word: str):
    synonym_of_the_word = get_synonyms(word)
    return synonym_of_the_word


def string2list__info():
    return {
        'title': 'String to List',
        'schema': {
            'separator': {
                'help_text': 'Use underscore (_) to denote a space',
            }
        }
    }


def string2list(string: qtexta = 'Jan, Feb, Mar, Apr, May, Jun, Jul, Aug, Sep, Oct, Nov, Dec',
                separator: qchar = ','):
    sep = separator.replace('_', ' ')
    slist = [x.strip() for x in string.split(sep)]
    df = pd.DataFrame(data={'Value': slist})
    out = QScreen()
    out.write(slist)
    array = out.flush()
    return {
        "List": array,
        "Table": df
    }


def list2string__info():
    return {
        'title': 'List to String',
        'schema': {
            'separator': {
                'help_text': 'Use underscore (_) to denote a space',
            }
        }
    }


def list2string(table: qtable = pd.DataFrame(
    {'Value': ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']}),
    separator: qchar = ',_', column: qchar = ''):
    cols = table.columns
    col = validated_col(cols, 0, column)
    sep = separator.replace('_', ' ')
    string = sep.join(table[col])
    return {
        "String": string,
    }
