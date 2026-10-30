# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

import io
import ipaddress
import socket
import time
import requests
from bs4 import BeautifulSoup
from bs4.element import Comment
from urllib.parse import urlparse, urlsplit, urljoin
from urllib.parse import quote
from qutil.mod_settings import is_debug, max_file_mb

_MAX_REDIRECTS = 3
_FETCH_TOTAL_TIMEOUT_S = 20  # per-chunk read timeouts alone don't stop a slow-drip response
# Default library user agents (python-requests, Python-urllib) are rejected with 403 by Cloudflare
# bot protection; a stable custom UA also lets a Cloudflare WAF skip rule target the server's own fetches.
_FETCH_HEADERS = {'User-Agent': 'Mozilla/5.0 (compatible; QCalcFetcher/1.0; +https://qcalc.org)'}


def assert_public_http_url(url: str):
    # SSRF guard: the server fetches user-supplied URLs (and URLs found inside fetched pages),
    # so reject anything that could reach internal services (localhost, private ranges,
    # cloud metadata 169.254.169.254) or use a non-http scheme (file://, ftp://).
    # The address check is skipped in debug so the dev server can fetch from localhost.
    parts = urlsplit(url)
    if parts.scheme not in ('http', 'https') or not parts.hostname:
        raise ValueError('Error (FURL): only http(s) URLs are allowed')
    if is_debug():
        return
    port = parts.port or (443 if parts.scheme == 'https' else 80)
    try:
        infos = socket.getaddrinfo(parts.hostname, port, type=socket.SOCK_STREAM)
    except socket.gaierror:
        raise ValueError('Error (FURL): host could not be resolved')
    for info in infos:
        ip = ipaddress.ip_address(info[4][0].split('%')[0])
        ip = getattr(ip, 'ipv4_mapped', None) or ip  # ::ffff:127.0.0.1
        if not ip.is_global:  # private, loopback, link-local, reserved, ...
            raise ValueError('Error (FURL): URL points to a non-public address')


def fetch_url(url: str, *, max_bytes: int | None = None, check_status: bool = True) -> requests.Response:
    """Safely GET a remote URL and return a ``requests.Response`` (``.content``, ``.text``, ``.status_code``).

    Use this instead of ``requests.get`` for any URL that is user-supplied or comes from fetched content.
    Redirects are followed manually so every hop is re-validated (a public URL must not bounce to an
    internal one), and the body is streamed with a size and total-time cap to avoid memory/worker
    exhaustion. ``max_bytes`` defaults to the same per-file limit as uploads (QCALC_MAX_FILE_MB).
    With ``check_status=False`` HTTP 4xx/5xx responses are returned instead of raised
    (e.g. for link checkers).
    """
    if max_bytes is None:
        max_bytes = int(max_file_mb() * 1024 * 1024)
    deadline = time.monotonic() + _FETCH_TOTAL_TIMEOUT_S
    for _ in range(_MAX_REDIRECTS + 1):
        assert_public_http_url(url)  # re-validated on every redirect hop
        with requests.get(url, headers=_FETCH_HEADERS, timeout=(3, 15), stream=True, allow_redirects=False) as resp:
            if resp.is_redirect:
                url = urljoin(url, resp.headers['Location'])
                continue
            declared = resp.headers.get('Content-Length', '')
            if declared.isdigit() and int(declared) > max_bytes:
                raise ValueError('Error (FURL): remote file too large')
            buf = io.BytesIO()
            for chunk in resp.iter_content(64 * 1024):
                buf.write(chunk)
                if buf.tell() > max_bytes:
                    raise ValueError('Error (FURL): remote file too large')
                if time.monotonic() > deadline:
                    raise TimeoutError('Error (FURL): download took too long')
            result = requests.Response()
            result.status_code = resp.status_code
            result.headers = resp.headers
            result.url = url
            result.reason = resp.reason
            result.encoding = resp.encoding
            result._content = buf.getvalue()
            if check_status:
                result.raise_for_status()
            return result
    raise ValueError('Error (FURL): too many redirects')


def encode_url_param(url_part, encode=True):
    # Encode the URL part, specifying an empty string for `safe`
    # to encode all characters except for alphabets, decimal digits, and '-', '_', '.', and '~'.
    if encode:
        return quote(url_part, safe='')
    else:
        return url_part


def url2html(url):
    try:
        return fetch_url(url).content  # text, content
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
    """
    parsed_url = urlparse(url)
    # A URL is considered absolute if it has a scheme (e.g., http or https) and a netloc (domain)
    return bool(parsed_url.scheme and parsed_url.netloc)


def is_relative_url(url):
    """
    Checks if a URL is relative.
    """
    return not is_absolute_url(url)
