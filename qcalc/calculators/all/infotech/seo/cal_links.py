# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

import requests
from bs4 import BeautifulSoup
from qcore.mod_anno import qtexta
from qutil import qaddr
from urllib.parse import urljoin, urlparse
import re


def is_valid_url(url):
    """
    Checks whether `url` is a valid URL.
    """
    if url.startswith('javascript:'):
        return False
    else:
        result = urlparse(url)
        return result.scheme and result.netloc


def xurls__info():
    return {
        'title': 'Extract all URLs from a Webpage',
    }


def xurls(page_url: qtexta = qaddr(), page_content: qtexta = ''):
    # https://www.geeksforgeeks.org/extract-all-the-urls-from-the-webpage-using-python/
    # https://faun.pub/extract-all-website-links-in-python-48f07619db95
    webpage_url = page_url.strip()
    page_content = page_content.strip()
    if webpage_url and not is_valid_url(webpage_url):
        return "Eneter a valid url"

    mode = ''
    domain_name = ''
    content = ''
    if webpage_url and page_content == '':
        domain_name = urlparse(webpage_url).netloc
        resp = requests.get(webpage_url, timeout=(3, 15))
        content = resp.content
        mode = 'url'
    elif page_content:
        content = page_content
        mode = 'text'

    internal_urls = set()
    external_urls = set()

    def store_link(href):
        if not is_valid_url(href):
            return
        if href in internal_urls:
            return
        if domain_name:
            if domain_name not in href:
                if href not in external_urls:
                    external_urls.add(href)
                return
            else:
                internal_urls.add(href)
        else:
            external_urls.add(href)
        return

    href = ''
    if mode == 'url':
        soup = BeautifulSoup(content, 'html.parser')
        for link in soup.find_all('a'):
            href = link.get('href')
            if href == "" or href is None:
                continue
            # join the URL if it's relative (not absolute link)
            href = urljoin(webpage_url, href)
            parsed_href = urlparse(href)
            # remove URL GET parameters, URL fragments, etc.
            href = parsed_href.scheme + "://" + parsed_href.netloc + parsed_href.path
            store_link(href)
    else:
        urls = re.findall(
            'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*(),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+',
            content
        )
        for link in urls:
            parsed_href = urlparse(link)
            # remove URL GET parameters, URL fragments, etc.
            href = parsed_href.scheme + "://" + parsed_href.netloc + parsed_href.path
            store_link(href)

    internal_url_count = len(internal_urls)
    external_url_count = len(external_urls)
    total_url_count = internal_url_count + external_url_count
    return {
        "Webpage Url": webpage_url,
        "Domain Name": domain_name,
        "Total Url Count": int(total_url_count),
        "Internal Url Count": internal_url_count,
        "External Url Count": external_url_count,
        "Internal Url List": internal_urls,  # set
        "External Url List": external_urls,  # set
        "Page Content": content
    }


def broken_links__info():
    return {
        "title": "Broken Link Checker",
        "schema": {"max_urls_to_check": {'attrs': {'max': '100', 'min': '1'}}}
    }


def broken_links(url: qtexta = qaddr(),
                 max_urls_to_check: int = 25):
    broken_links = []
    active_links = []
    error = 'None'
    link_url = ''
    try:
        response = requests.get(url, timeout=(3, 15))
        response.raise_for_status()

        urls = xurls(url)
        allurls = list(urls["Internal Url List"]) + list(urls["External Url List"])
        i = 0
        for link_url in allurls:
            i += 1
            if i > max_urls_to_check:
                break
            if link_url.startswith('javascript'):
                continue
            link_response = requests.get(link_url, timeout=(3, 15))
            if link_response.status_code >= 400:
                broken_links.append(link_url)
            else:
                active_links.append(link_url)
    except Exception as e:
        broken_links.append(link_url)
        error = f"{e}:{link_url}"

    return {
        "Error": error,
        "Broken Links": broken_links,
        "Good Links": active_links
    }
