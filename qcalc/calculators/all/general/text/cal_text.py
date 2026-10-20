# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

import pandas as pd
from titlecase import titlecase
from qcore import qtexta, QScreen, qchar, qtable, as_qtable, qfile, qurl, qhtml
from wordcloud import STOPWORDS
from functools import partial
import math
import re
from qutil import get_synonyms, validated_col, demo_url, word_count, url2text, nzs

example_text = "Data science and data analysis help us understand big data through data visualization and data cleaning. "\
               "Modern data science relies on powerful Python code, libraries, and specialized Python tools to extract deep insights. "\
               "Furthermore, modern analysis requires clean code to build accurate machine learning models and predictive models."


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


def synonym(word: str = "god"):
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
        "List": qhtml(array),
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
    table = as_qtable(table)
    cols = table.columns
    col = validated_col(cols, 0, column)
    sep = separator.replace('_', ' ')
    string = sep.join(table[col])
    return {
        "String": string,
    }


def text_stats__info():
    return {
        'title': 'Text Statistics',
        'showhide': {
            'mode': {
                'fields': ['upload_text', 'text_url', 'text'],
                'callback': 'text_stats_mode_showhide',
            },
        },
        'schema': {
            'mode': {
                'type': 'choice',
                'choices': {'File': 'File', 'URL': 'URL', 'Text': 'Text'},
                'initial': 'Text',
                'help_text': 'Choose whether to analyze text from a file, URL, or direct text input.',
            },
        },
        'script': """
        function text_stats_mode_showhide(v){
            return [v === 'File', v === 'URL', v === 'Text'];
        }
        """,
    }


def text_stats(upload_text: qfile = None, text_url: qurl = demo_url('demo.txt'),
               text: qtexta = example_text, mode='Text'):
    mode = str(mode).strip().upper()
    if mode == 'TEXT':
        if nzs(text) == '':
            raise Exception('Error (TS): A valid Text is not found')
        text_content = text
    elif mode == 'URL':
        if not text_url:
            raise Exception('Error (TS): A valid URL is not found')
        text_content = url2text(text_url)
    elif mode == 'FILE':
        if upload_text is None:
            raise Exception('Error (TS): A valid Text File is not found')
        text_content = upload_text.text()
    else:
        raise Exception("Error (TS): mode must be one of 'File', 'URL', or 'Text'")

    char_count = len(text_content)
    char_count_no_space = len(re.sub(r'\s+', '', text_content))
    wc, _ = word_count(text_content)
    token_estimate = int(math.ceil(char_count_no_space / 4.0)) if char_count_no_space > 0 else 0

    return {
        'Character Count': char_count,
        'Character Count (No Space)': char_count_no_space,
        'Word Count': wc,
        'Token Estimate': token_estimate,
    }
