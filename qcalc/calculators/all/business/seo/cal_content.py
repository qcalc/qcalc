# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

from wordcloud import WordCloud, STOPWORDS
import matplotlib.pyplot as plt
import yake
from qcore import QChart
from qcore.mod_anno import *
from qutil import word_count, text2words, url2text, qaddr
import pandas as pd

example_text = "Data science and data analysis help us understand big data through data visualization and data cleaning. "\
        "Modern data science relies on powerful Python code, libraries, and specialized Python tools to extract deep insights. "\
        "Furthermore, modern analysis requires clean code to build accurate machine learning models and predictive models."

def word_freq__info():
    return {
        'title': 'Word Frequency Analysis'
    }


def word_freq(text: qtexta = example_text, url: qurl = qaddr(), top=20):
    def cal_pct(sorted_count_list, word_cnt):
        for i in range(len(sorted_count_list)):
            sorted_count_list[i] = list(sorted_count_list[i])
            sorted_count_list[i].append(round(sorted_count_list[i][1] * 100 / word_cnt, 2))
        return sorted_count_list

    count_words = dict()

    if text:
        text_content = text
    elif url:
        text_content = url2text(url)
    else:
        return 'Error (WF): Enter text or url'

    cnt, words = word_count(text_content)

    for word in words:
        if word in count_words:
            count_words[word] += 1
        else:
            count_words[word] = 1

    sorted_count = sorted(count_words.items(), key=lambda kv: kv[1], reverse=True)[0:top]
    sorted_count = cal_pct(sorted_count, cnt)

    count_words2 = dict()
    cnt2 = 0
    old_word = words[0]
    for word in words:
        if cnt2 != 0:
            if old_word + " " + word in count_words2:
                count_words2[old_word + " " + word] += 1
            else:
                count_words2[old_word + " " + word] = 1
        old_word = word
        cnt2 = cnt2 + 1

    sorted_count2 = sorted(count_words2.items(), key=lambda kv: kv[1], reverse=True)[0:top]
    sorted_count2 = cal_pct(sorted_count2, cnt2)
    slist = sorted_count + sorted_count2
    df = pd.DataFrame(slist, columns=['Word', 'Count', 'Freq%'])
    return {
        'Single Word Count': cnt,
        'Double Word Count': cnt2 - 1,
        'Top Words': df
    }


def word_cloud__info():
    return {
        'title': 'Generate Word Cloud',
        'kins': 'html_reader, csv_reader',
        'outcol': ['chart__r'],
    }


def word_cloud(
    text:qtexta = example_text,
    url: str = qaddr()
):
    if text:
        text_content = text
    elif url:
        text_content = url2text(url)
    else:
        return 'Error (WC): Enter text or url'

    words = text2words(text_content)
    stopwords = set(STOPWORDS)

    comment_words = ''
    for i in range(len(words)):
        words[i] = words[i].lower()

    comment_words += " ".join(words) + " "
    chart = QChart()
    wd = int(chart.figsize[0] * 100)
    ht = int(chart.figsize[1] * 100)
    wordcloud = WordCloud(
        width=wd, height=ht,
        background_color='white',
        stopwords=stopwords,
        min_font_size=10
    ).generate(comment_words)

    # fig, ax = plt.subplots(figsize=chart.figsize, facecolor=None)
    fig, ax = chart.create_figure()
    ax.imshow(wordcloud)
    ax.axis("off")
    fig.tight_layout(pad=0)
    chart.render_done()
    return {'chart': chart}


def keywords__info():
    return {
        'title': 'Keyword Extractor',
        'desc': 'The lower the score, the more relevant the keyword is',
        'kins': 'html_reader, csv_reader',
        # 'template': 'v4.21'
    }


def keywords(text: qtexta = example_text, top=20, language: qchar = 'en'):
    kw_extractor = yake.KeywordExtractor(lan=language, top=top)
    """
    kw_extractor = yake.KeywordExtractor(
        lan=language,
        n=max_ngram_size,
        dedupLim=deduplication_threshold,
        dedupFunc=deduplication_algo,
        windowsSize=windowSize,
        top=numOfKeywords,
        features=None
    )
    """
    keywords = kw_extractor.extract_keywords(text)
    df = pd.DataFrame(keywords, columns=['Keyword', 'Relevancy'])
    return df
