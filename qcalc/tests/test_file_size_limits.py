import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")

import pytest
from django.core.exceptions import ValidationError
from django.test import override_settings

from qcore.mod_qfvalidators import validate_file_size
from qutil.mod_settings import max_file_mb


class FakeFile:
    def __init__(self, size):
        self.size = size


@override_settings(QCALC_MAX_FILE_MB=10.0, QCALC_MAX_FILE_MB_CEILING=45.0)
def test_default_and_override_and_ceiling():
    assert max_file_mb() == 10.0
    assert max_file_mb('') == 10.0
    assert max_file_mb('5') == 5.0
    assert max_file_mb(100) == 45.0  # field cannot exceed the ceiling


@override_settings(QCALC_MAX_FILE_MB=2.0, QCALC_MAX_FILE_MB_CEILING=45.0)
def test_validator_uses_shared_default():
    check = validate_file_size()
    check(FakeFile(2 * 1024 * 1024))
    with pytest.raises(ValidationError):
        check(FakeFile(2 * 1024 * 1024 + 1))


@override_settings(QCALC_MAX_FILE_MB=10.0, QCALC_MAX_FILE_MB_CEILING=20.0)
def test_validator_clamps_to_ceiling():
    check = validate_file_size(100)
    check(FakeFile(20 * 1024 * 1024))
    with pytest.raises(ValidationError):
        check(FakeFile(20 * 1024 * 1024 + 1))


@override_settings(QCALC_MAX_FILE_MB=1.0, QCALC_MAX_FILE_MB_CEILING=45.0)
def test_fetch_url_default_limit_follows_setting():
    from unittest import mock
    from qutil import mod_url

    class Resp:
        status_code, reason, encoding, is_redirect = 200, 'OK', 'utf-8', False
        headers = {}

        def __enter__(self): return self

        def __exit__(self, *a): return False

        def iter_content(self, n): yield b'x' * (1024 * 1024 + 1)

    with mock.patch.object(mod_url, 'is_debug', return_value=True), \
            mock.patch.object(mod_url.requests, 'get', return_value=Resp()):
        with pytest.raises(ValueError, match='too large'):
            mod_url.fetch_url('http://example.com/a')
