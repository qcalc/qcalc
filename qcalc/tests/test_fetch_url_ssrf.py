# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha
# Tests generated with AI assistance. Reviewed and validated by the author.

import ipaddress
import os
from unittest import mock

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")

import pytest

from qutil import mod_url
from qutil.mod_url import fetch_url
from qcore.mod_qfile import qf2bio


class FakeResp:
    def __init__(self, status=200, headers=None, body=b'data'):
        self.status_code = status
        self.headers = headers or {}
        self.reason = 'X'
        self.encoding = 'utf-8'
        self._body = body
        self.is_redirect = status in (301, 302, 303, 307, 308)

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def iter_content(self, size):
        for i in range(0, len(self._body), size):
            yield self._body[i:i + size]


def _fake_getaddrinfo(host, port, **kw):
    try:
        ipaddress.ip_address(host)
        ip = host  # IP literals resolve to themselves
    except ValueError:
        ip = '93.184.216.34'  # any named host resolves to a public address
    return [(2, 1, 6, '', (ip, port))]


@pytest.fixture(autouse=True)
def production_mode():
    with mock.patch.object(mod_url, 'is_debug', return_value=False), \
            mock.patch.object(mod_url.socket, 'getaddrinfo', side_effect=_fake_getaddrinfo):
        yield


@pytest.mark.parametrize("url", [
    "http://127.0.0.1:8000/",
    "http://10.0.0.5/",
    "http://192.168.1.1/",
    "http://169.254.169.254/latest/meta-data/",
    "http://[::1]/",
    "http://[::ffff:127.0.0.1]/",
    "file:///etc/passwd",
    "ftp://example.com/x.png",
])
def test_non_public_or_non_http_urls_rejected(url):
    with mock.patch.object(mod_url.requests, 'get') as get:
        with pytest.raises(ValueError):
            fetch_url(url)
        with pytest.raises(ValueError):
            qf2bio(None, url)
        get.assert_not_called()


def test_redirect_to_private_address_rejected():
    resp = FakeResp(302, {'Location': 'http://127.0.0.1:8000/admin'})
    with mock.patch.object(mod_url.requests, 'get', return_value=resp) as get:
        with pytest.raises(ValueError):
            fetch_url('http://example.com/a.png')
        assert get.call_count == 1


def test_redirect_loop_rejected():
    resp = FakeResp(302, {'Location': 'http://example.com/again'})
    with mock.patch.object(mod_url.requests, 'get', return_value=resp):
        with pytest.raises(ValueError, match='too many redirects'):
            fetch_url('http://example.com/a')


def test_oversize_declared_length_rejected():
    resp = FakeResp(200, {'Content-Length': str(int(mod_url.max_file_mb() * 1024 * 1024) + 1)})
    with mock.patch.object(mod_url.requests, 'get', return_value=resp):
        with pytest.raises(ValueError, match='too large'):
            fetch_url('http://example.com/a.png')


def test_oversize_streamed_body_rejected():
    resp = FakeResp(200, body=b'x' * 200)
    with mock.patch.object(mod_url.requests, 'get', return_value=resp):
        with pytest.raises(ValueError, match='too large'):
            fetch_url('http://example.com/a.png', max_bytes=100)


def test_http_error_status_raises_by_default():
    with mock.patch.object(mod_url.requests, 'get', return_value=FakeResp(404)):
        with pytest.raises(mod_url.requests.HTTPError):
            fetch_url('http://example.com/a.png')


def test_check_status_false_returns_error_response():
    with mock.patch.object(mod_url.requests, 'get', return_value=FakeResp(404, body=b'nope')):
        resp = fetch_url('http://example.com/a', check_status=False)
    assert resp.status_code == 404
    assert resp.content == b'nope'


def test_public_url_downloads_and_decodes():
    with mock.patch.object(mod_url.requests, 'get', return_value=FakeResp(200, body=b'abc')):
        resp = fetch_url('https://example.com/a.txt')
        assert resp.content == b'abc'
        assert resp.text == 'abc'
        assert qf2bio(None, 'https://example.com/a.png').read() == b'abc'


def test_redirect_to_public_url_followed():
    responses = [FakeResp(301, {'Location': '/b'}), FakeResp(200, body=b'ok')]
    with mock.patch.object(mod_url.requests, 'get', side_effect=responses) as get:
        assert fetch_url('http://example.com/a').content == b'ok'
        assert get.call_args_list[1].args[0] == 'http://example.com/b'


def test_debug_mode_allows_localhost_but_not_other_schemes():
    with mock.patch.object(mod_url, 'is_debug', return_value=True):
        with mock.patch.object(mod_url.requests, 'get', return_value=FakeResp(200, body=b'abc')):
            assert fetch_url('http://127.0.0.1:8000/x.png').content == b'abc'
        with pytest.raises(ValueError):
            fetch_url('file:///etc/passwd')
