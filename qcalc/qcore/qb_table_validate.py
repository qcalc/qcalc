# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

import json

import pandas as pd
from django.core.exceptions import ValidationError

from .qf_anno import as_qtable


class QTableValidationError(ValueError):
    """Validation error for user-correctable table input issues."""


def _coerce_table_for_validation(value, field_name):
    """Convert posted table payload into a DataFrame for schema validators."""
    if isinstance(value, str):
        text = value.strip()
        if text in {'', 'null', 'None'}:
            return pd.DataFrame()
        try:
            parsed = json.loads(text)
        except Exception as e:
            raise ValidationError(f"Invalid table payload for {field_name}") from e
        value = parsed

    try:
        return as_qtable(value)
    except Exception as e:
        raise ValidationError(f"Invalid table payload for {field_name}") from e


def table_columns_validator(field_name, required_cols=None, optional_cols=None, schema=None):
    """Return a reusable validator for a table input.

    Pass ``schema`` (a QTable schema) to check headers and values, or ``required_cols`` /
    ``optional_cols`` to check headers only.
    """
    optional_cols = optional_cols or []

    def _validator(value):
        table = _coerce_table_for_validation(value, field_name)
        try:
            from .qb_qtable import QTable
            table_qt = QTable(table, name=field_name, schema=schema, validate=bool(schema))
            if not schema:
                table_qt.assert_columns(list(required_cols), optional_cols=list(optional_cols))
        except (QTableValidationError, ValueError) as e:
            raise ValidationError(str(e)) from e

    return _validator
