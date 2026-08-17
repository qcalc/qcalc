# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

from django.core.exceptions import ValidationError


def validate_file_size(max_mb: float = 10.0):
    def _validate_file_size(value):
        filesize = value.size
        if filesize > int(max_mb * 1024 * 1024):  # 10MB
            raise ValidationError(f"The maximum file size that can be uploaded is {max_mb} MB")
    return _validate_file_size
