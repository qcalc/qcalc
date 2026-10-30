# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

import io

import pytest
from django.contrib.auth.models import AnonymousUser
from django.contrib.sessions.middleware import SessionMiddleware
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.test import RequestFactory

from calc import QPref
from qcore import QFile
from qcore.mod_qforms import RememberedFileInput
from qutil.timed_thread import QThread


def _qfile(name='demo.txt', data=b'hello world'):
    upload = InMemoryUploadedFile(io.BytesIO(data), 'f', name, 'text/plain', len(data), None)
    return QFile('f', upload)


def test_remembered_file_name_is_rendered():
    html = RememberedFileInput().render('upload_file', _qfile())
    assert '<input type="file"' in html
    assert 'Remembered: demo.txt (11\xa0bytes)' in html


def test_remembered_file_name_is_escaped():
    html = RememberedFileInput().render('upload_file', _qfile(name='<b>x.txt'))
    assert '<b>x' not in html
    assert '&lt;b&gt;x.txt' in html


def test_no_label_without_remembered_file():
    for value in (None, ''):
        assert 'remembered-file' not in RememberedFileInput().render('upload_file', value)


@pytest.fixture
def mem_request():
    request = RequestFactory().get('/')
    SessionMiddleware(lambda r: None).process_request(request)
    request.session.save()
    request.user = AnonymousUser()
    QThread.set_req(request)
    yield request
    QThread.set_req(None)


def _remember(sfunc, kb, size):
    from calc import QMem
    QPref.setp1('remember_file_kb', kb)
    mem = {'upload_file': _qfile(data=b'x' * size)}
    QMem.setf(sfunc, mem)
    return QMem.getf(sfunc)['upload_file']


def test_remember_limit_default_is_300_kb(mem_request):
    from calc import QMem
    assert QMem.file_limit_bytes() == 300 * 1024


def test_file_within_limit_is_remembered(mem_request):
    assert isinstance(_remember('f1', 400, 400 * 1024), QFile)


def test_file_over_limit_is_not_remembered(mem_request):
    assert _remember('f2', 400, 400 * 1024 + 1) == ''


def test_zero_limit_never_remembers_files(mem_request):
    assert _remember('f3', 0, 10) == ''
