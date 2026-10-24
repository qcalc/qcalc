# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

from django.core.exceptions import ValidationError
from qutil.mod_settings import max_file_mb


def validate_file_size(max_mb: float | None = None):
    # max_mb=None -> QCALC_MAX_FILE_MB; values are capped at QCALC_MAX_FILE_MB_CEILING
    limit_mb = max_file_mb(max_mb)

    def _validate_file_size(value):
        if value.size > int(limit_mb * 1024 * 1024):
            raise ValidationError(f"The maximum file size that can be uploaded is {limit_mb:g} MB")
    return _validate_file_size
