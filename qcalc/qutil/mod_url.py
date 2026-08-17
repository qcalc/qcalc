# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

import requests
from bs4 import BeautifulSoup
from bs4.element import Comment
from urllib.parse import urlparse
from urllib.parse import quote


def encode_url_param(url_part, encode=True):
    # Encode the URL part, specifying an empty string for `safe`
    # to encode all characters except for alphabets, decimal digits, and '-', '_', '.', and '~'.
    if encode:
        return quote(url_part, safe='')
    else:
        return url_part


def url2html(url):
    try:
        response = requests.get(url, timeout=(3, 15))
        response.raise_for_status()
        return response.content  # text, content
    except requests.exceptions.RequestException as e:
        e.args = (f"Error (U2H): Error fetching the page",)
        raise e


def url2text(url):
    html_content = url2html(url)
    return html2text(html_content)


def html2text(html):
    try:
        # Parse the HTML content
        soup = BeautifulSoup(html, 'html.parser')
        return soup2text(soup)
    except Exception as e:
        e.args = (f"Error (H2T): Error parsing the html",)
        raise e


def soup2text(soup):
    try:
        # Extract the pure text content
        for script_or_style in soup(['script', 'style', 'meta', 'head', 'header', 'footer', 'nav', 'aside']):
            script_or_style.decompose()  # Remove these tags and their content

        # Remove comments
        for comment in soup.find_all(string=lambda text: isinstance(text, Comment)):
            comment.extract()

        # Get the text and strip extra whitespace
        text = soup.get_text(separator=' ')
        clean_text = ' '.join(text.split())

        return clean_text

    except Exception as e:
        e.args = (f"Error (S2T): Error extracting text",)
        raise e


def is_absolute_url(url):
    """
    Checks if a URL is absolute.

    :param url: The URL to check.
    :return: True if the URL is absolute, False if it is relative.
    """
    parsed_url = urlparse(url)
    # A URL is considered absolute if it has a scheme (e.g., http or https) and a netloc (domain)
    return bool(parsed_url.scheme and parsed_url.netloc)


def is_relative_url(url):
    """
    Checks if a URL is relative.

    :param url: The URL to check.
    :return: True if the URL is relative, False if it is absolute.
    """
    return not is_absolute_url(url)

