# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

import requests
from bs4 import BeautifulSoup
from qcore import qurl, qtexta
import re
import pandas as pd
from urllib.parse import urljoin
import time
from qutil import word_count as get_word_count, url2html, soup2text, qaddr


def seo_score__info():
    return {
        'title': 'Measure SEO Score of a web page'
    }


def seo_score(url: qurl = qaddr(), keyword: str = 'calculator'):
    """
    This function parses the HTML content and measures the SEO score based on the number of page titles,
    headings, paragraphs, meta tags, images, and links found on the page.
    """
    # Send a GET request to the URL
    html_content = url2html(url)

    # Create a BeautifulSoup object to parse the HTML
    soup = BeautifulSoup(html_content, 'html.parser')

    # Page title score 10
    # | soup.title.string is a NavigableString object and is not serializable by memcache
    # | using str() to convert to string
    title = str(soup.title.string)

    ln = len(title)
    if 70 >= ln >= 50:
        title_score = 10
    elif 90 >= ln >= 30:
        title_score = 5
    else:
        title_score = int(ln / 6)

    # Meta Description 10
    meta_description = soup.find('meta', {'name': 'description'})
    meta_description = meta_description.get('content', '') if meta_description else ''
    lndesc = len(meta_description)
    desc_score = 0
    if 160 >= lndesc >= 60:
        desc_score = 10
    elif 200 >= lndesc >= 30:
        desc_score = 5

    # Heading score 10
    headings = soup.find_all(['h1', 'h2', 'h3'])
    heading_score = min(len(headings) * 2, 10)  # Max score for headers is 10

    # Paragraph score 10
    paragraphs = soup.find_all('p')
    paragraph_score = min(len(paragraphs) * 2, 10)

    # Meta tag score 10
    meta_tags = soup.find_all('meta')
    meta_score = min(len(meta_tags) * 2, 10)

    # Image score 10
    images = soup.find_all('img')
    image_score = min(len(images) * 4, 10)

    # Link score 10
    links = soup.find_all('a')
    link_score = min(len(links) * 2, 10)

    # keyword density analysis 10
    text_content = soup2text(soup)
    kw = keyword.strip().lower()
    text_content_lower = text_content.lower()
    wc, words = get_word_count(text_content_lower)
    if kw and wc > 0:
        # if single word
        if len(kw.split()) == 1:
            keyword_density = words.count(kw) / wc * 100
        else:
            keyword_density = text_content_lower.count(kw) / wc * 100

    else:
        keyword_density = 0
    keyword_density = round(keyword_density, 2)

    keyword_score = 0
    if 3.5 >= keyword_density >= 2:
        keyword_score = 10
    elif keyword_density > 1:
        keyword_score = 5

    # word count 10
    word_count = len(re.findall(r'\w+', text_content))
    wcount_score = 0
    if 4000 >= word_count > 1500:
        wcount_score = 10
    elif 1500 >= word_count > 500:
        wcount_score = 5 + int((word_count - 500) / 200)
    elif word_count <= 500:
        wcount_score = int(word_count / 100)
    elif word_count > 4000:
        wcount_score = int(10 - (word_count - 4000) / 300)
    wcount_score = 0 if wcount_score < 0 else wcount_score
    wcount_score = 10 if wcount_score > 10 else wcount_score

    # Calculate overall SEO score
    seo_score = int((title_score + heading_score + paragraph_score +
                     meta_score + image_score + link_score + keyword_score + wcount_score +
                     desc_score) * 100 / 90)
    result = {
        "Element": ["Page Title", "Description", "Heading", "Paragraph", "Meta Tag", "Image", "Link", "Keyword",
                    "Word"],
        "Measure": ["Length", "Length", "Count", "Count", "Count", "Count", "Count", "Density", "Count"],
        "Value": [ln, lndesc, len(headings), len(paragraphs), len(meta_tags), len(images), len(links), keyword_density,
                  word_count],
        "Recommended": ["50-70", "60-160", 5, 5, 5, 3, 5, "2-3.5", "1500-4000"],
        "Score": [title_score, desc_score, heading_score, paragraph_score, meta_score, image_score, link_score,
                  keyword_score, wcount_score],
    }
    df = pd.DataFrame(result)
    # df = df.apply(lambda col: col.map(df_formatter))
    pd.options.display.float_format = '{:.1f}'.format
    return {
        "Title": title,
        "Description": meta_description,
        "Overall SEO Score (%)": seo_score,
        "Score Sheet": df,
        "Text Content": text_content
    }


def pgsize__info():
    return {
        'title': 'Measure Page Size of Web Pages'
    }


def pgsize(urls: qtexta = qaddr()):
    def pg_sizes(url):
        # Fetch the HTML content of the web page
        start_time = time.time()
        html_content = url2html(url)
        end_time = time.time()
        page_load_time = (end_time - start_time) * 1000  # 'ms'
        # Print the page load time in seconds

        soup = BeautifulSoup(html_content, 'html.parser')

        # Find all the tags that may contain assets (e.g., img, script, link)
        asset_tags = soup.find_all(tags)

        # Extract URLs of assets
        asset_urls = []
        for tag in asset_tags:
            # print(tag.name, tag.get('src','no-src'), tag.get('rel','no-rel'), ": ", tag)
            if tag.name == 'img' and tag.get('src', '') != '':
                asset_urls.append((tag.name, tag['src']))
            elif tag.name == 'script' and tag.get('src', '') != '':
                asset_urls.append((tag.name, tag['src']))
            elif tag.name == 'link' and tag.get('rel', '') == ['stylesheet']:
                asset_urls.append((tag.name, tag['href']))
            elif tag.name == 'link' and tag.get('rel', '') == ['icon']:
                asset_urls.append((tag.name, tag['href']))

        # print(asset_urls)
        # Calculate the total size of the web page content and its assets
        total_size = len(html_content) / 1024
        sizes = {"Html": total_size}
        for tag in tags:
            sizes[tags[tag]] = 0
        # print(sizes)
        for tag, asset_url in asset_urls:
            asset_url = urljoin(url, asset_url)
            asset_response = requests.get(asset_url, timeout=(3, 15))
            ln_asset = len(asset_response.content) / 1024
            total_size += ln_asset
            sizes[tags[tag]] += ln_asset
        sizes["Total"] = total_size
        return sizes, page_load_time

    url_list = urls.strip().split('\r\n')
    tags = {'img': 'Image', 'script': 'JavaScript', 'link': 'StyleSheet'}

    log = ''
    response_data = []
    sizes: dict = {}
    page_load_time = 0
    for url in url_list:
        sizes: dict = {}
        page_load_time = 0
        try:
            sizes, page_load_time = pg_sizes(url)
        except Exception as e:
            log += f"{type(e).__name__}: fetching page [{url}]\r\n"

        if len(url_list) > 1:
            response_data.append([
                url,
                sizes.get('Html', 0),
                sizes.get('Image', 0),
                sizes.get('JavaScript', 0),
                sizes.get('StyleSheet', 0),
                sizes.get('Total', 0),
                page_load_time,
            ])

    if len(url_list) == 1:
        result = {
            "Content Type": sizes.keys(),
            "Size (KB)": sizes.values(),
        }
        df = pd.DataFrame(result)
        return {
            "Page Load Time (ms)": page_load_time,
            "Page Size Analysis": df,
            "log": log if log else 'No error',
        }
    else:
        cols = ['URL', 'Html (KB)', 'Image (KB)', 'JavaScript (KB)', 'StyleSheet (KB)',
                'Total (KB)', 'Page Load Time (ms)']
        df = pd.DataFrame(data=response_data, columns=cols)
        return {
            "Page Size Analysis": df,
            "Log": log if log else 'No error',
        }
