# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha


import re


def _normalize_token(value):
    """Normalize identifiers for case-insensitive, whitespace-tolerant matching."""
    return str(value).strip().casefold()


def _compact_token(value):
    """Normalize identifier by keeping only alphanumeric characters."""
    return ''.join(ch for ch in str(value).casefold() if ch.isalnum())


def _is_strict_table_input_enabled():
    """Read strict table validation preference from thread-local request context."""
    try:
        from .timed_thread import QThread
        return bool(QThread.get_pref('strict_table_input', False))
    except Exception:
        return False


def _optional_name_words(value):
    words = [w for w in re.split(r'[^a-z0-9]+', str(value).casefold()) if w]
    alias_map = {
        'minimum': 'min',
        'min': 'min',
        'maximum': 'max',
        'max': 'max',
        'quantity': 'qty',
        'qty': 'qty',
    }
    return [alias_map.get(w, w) for w in words]


def _looks_like_optional_alias(candidate, optional_name):
    candidate_norm = _normalize_token(candidate)
    optional_norm = _normalize_token(optional_name)
    if candidate_norm == optional_norm:
        return False

    candidate_compact = _compact_token(candidate)
    optional_compact = _compact_token(optional_name)
    if not candidate_compact or not optional_compact:
        return False

    if candidate_compact == optional_compact:
        return True
    if candidate_compact.startswith(optional_compact) or optional_compact.startswith(candidate_compact):
        return True

    c_words = _optional_name_words(candidate)
    o_words = _optional_name_words(optional_name)
    if not c_words or not o_words:
        return False

    # Suspicious if each optional token has a close word-level prefix match.
    for ow in o_words:
        if len(ow) < 2:
            continue
        if not any(cw.startswith(ow[:3]) or ow.startswith(cw[:3]) for cw in c_words if len(cw) >= 2):
            return False
    return True


def _table_columns(table):
    """Return column names from either a DataFrame-like table or a qtbl dict."""
    if isinstance(table, dict):
        cols = table.get('columns')
        if not isinstance(cols, list):
            raise Exception("Table dict must contain a list under key 'columns'")
        return cols
    if hasattr(table, 'columns'):
        return list(table.columns)
    raise Exception('Unsupported table type. Expected DataFrame-like or qtbl dict table.')


def _column_lookup(table):
    """Build normalized->actual column map and reject ambiguous near-duplicate names."""
    columns = _table_columns(table)
    lookup = {}
    ambiguous = []
    for col in columns:
        key = _normalize_token(col)
        if key in lookup and lookup[key] != col:
            ambiguous.append((lookup[key], col))
            continue
        lookup[key] = col
    if ambiguous:
        pairs = ', '.join(f"'{left}' vs '{right}'" for left, right in ambiguous)
        raise Exception(
            f"Ambiguous column names detected (differ only by case/spacing): {pairs}. "
            'Please keep one canonical version.'
        )
    return lookup


def _rename_columns(table, rename_map):
    """Rename columns in-place for DataFrame-like or qtbl dict tables."""
    if not rename_map:
        return
    if isinstance(table, dict):
        cols = list(table.get('columns', []))
        table['columns'] = [rename_map.get(col, col) for col in cols]
        return
    table.rename(columns=rename_map, inplace=True)


def _table_column_values(table, column_name):
    """Read one column as a list of values from either supported table shape."""
    if isinstance(table, dict):
        cols = table.get('columns', [])
        if column_name not in cols:
            raise Exception(f"Column not found: {column_name}")
        idx = cols.index(column_name)
        values = []
        for row in table.get('data', []):
            if isinstance(row, (list, tuple)) and idx < len(row):
                values.append(row[idx])
            else:
                values.append(None)
        return values
    return table[column_name].tolist()


def require_columns(
    df,
    table_name,
    required_cols,
    optional_cols=None,
    case_sensitive=False,
    columns_can_grow=True,
):
    """Ensure required columns exist; optionally canonicalize known column names in-place.

    Under Strict Table Input mode, set columns_can_grow=False for
    fixed-schema/master tables so unknown columns raise an error.
    """
    optional_cols = optional_cols or []
    expected_cols = list(required_cols) + [col for col in optional_cols if col not in required_cols]
    actual_cols = _table_columns(df)

    if case_sensitive:
        missing = [col for col in required_cols if col not in actual_cols]
        if missing:
            expected = ', '.join(expected_cols)
            raise Exception(
                f"{table_name} missing required column(s): {', '.join(missing)}. "
                f"Expected columns: {expected}."
            )
        return {col: col for col in expected_cols if col in actual_cols}

    lookup = _column_lookup(df)
    missing = [col for col in required_cols if _normalize_token(col) not in lookup]
    if missing:
        expected = ', '.join(expected_cols)
        raise Exception(
            f"{table_name} missing required column(s): {', '.join(missing)}. "
            f"Expected columns: {expected}."
        )

    strict_mode = _is_strict_table_input_enabled()

    if optional_cols and strict_mode:
        expected_keys = {_normalize_token(col) for col in expected_cols}
        suspicious = []
        for actual_col in actual_cols:
            actual_key = _normalize_token(actual_col)
            if actual_key in expected_keys:
                continue
            for opt_col in optional_cols:
                if _looks_like_optional_alias(actual_col, opt_col):
                    suspicious.append((actual_col, opt_col))
                    break
        if suspicious:
            preview = ', '.join(f"'{actual}' ~ '{expected}'" for actual, expected in suspicious[:10])
            expected = ', '.join(expected_cols)
            raise Exception(
                f"{table_name} has suspicious column name(s) under Strict Table Input mode: {preview}. "
                f"Rename these columns to the expected canonical names. Expected columns: {expected}."
            )

    if strict_mode and not columns_can_grow:
        expected_keys = {_normalize_token(col) for col in expected_cols}
        unexpected = [
            str(col)
            for col in actual_cols
            if _normalize_token(col) not in expected_keys
        ]
        if unexpected:
            allowed = ', '.join(expected_cols)
            found = ', '.join(unexpected[:10])
            raise Exception(
                f"{table_name} has unexpected column(s) under Strict Table Input mode: {found}. "
                f"Allowed columns: {allowed}."
            )

    rename_map = {}
    resolved = {}
    for col in expected_cols:
        actual = lookup.get(_normalize_token(col))
        if actual is None:
            continue
        resolved[col] = col
        if actual != col:
            rename_map[actual] = col

    _rename_columns(df, rename_map)
    return resolved


def require_values_subset(
    child_df,
    child_table,
    child_col,
    parent_df,
    parent_table,
    parent_col,
    case_sensitive=False,
):
    """Ensure child column values are a subset of parent column values."""
    require_columns(child_df, child_table, [child_col], case_sensitive=case_sensitive)
    require_columns(parent_df, parent_table, [parent_col], case_sensitive=case_sensitive)

    parent_values = {
        str(value).strip(): value
        for value in _table_column_values(parent_df, parent_col)
        if str(value).strip() != ''
    }
    if case_sensitive:
        parent_keys = set(parent_values.keys())
        child_keys = [
            str(value).strip() for value in _table_column_values(child_df, child_col) if str(value).strip() != ''
        ]
    else:
        parent_keys = {_normalize_token(value) for value in parent_values.keys()}
        child_keys = [
            _normalize_token(value) for value in _table_column_values(child_df, child_col) if str(value).strip() != ''
        ]

    unknown = sorted({key for key in child_keys if key not in parent_keys})
    if unknown:
        unknown_preview = ', '.join(unknown[:10])
        raise Exception(
            f"{child_table}.{child_col} contains value(s) not present in "
            f"{parent_table}.{parent_col}: {unknown_preview}"
        )


def require_unique_values(
    table,
    table_name,
    column_name,
    case_sensitive=False,
    ignore_blank=False,
):
    """Ensure a column has unique values and return normalized keys.

    Useful for key columns such as Project, Item, Worker, Shift, etc.
    """
    require_columns(table, table_name, [column_name], case_sensitive=case_sensitive)
    values = _table_column_values(table, column_name)

    seen = {}
    duplicates = []
    ordered_keys = []
    for value in values:
        text = str(value).strip()
        if ignore_blank and text == '':
            continue
        key = text if case_sensitive else _normalize_token(text)
        if key in seen:
            duplicates.append((seen[key], text))
        else:
            seen[key] = text
            ordered_keys.append(key)

    if duplicates:
        preview = ', '.join(f"{left}/{right}" for left, right in duplicates[:10])
        raise Exception(f"{table_name}.{column_name} contains duplicate value(s): {preview}")

    return [seen[key] for key in ordered_keys]


def parse_optional_number(value, field_name, cast=float):
    """Parse optional scalar number, returning None for blank input.

    `cast` can be `float`, `int`, or any callable that accepts one value.
    """
    if value in ('', None):
        return None
    try:
        return cast(value)
    except Exception as e:
        raise Exception(f"Invalid numeric value for {field_name}: {value}") from e


def require_unique_pairs(
    table,
    table_name,
    left_col,
    right_col,
    case_sensitive=False,
):
    """Ensure (left_col, right_col) pairs are unique and return normalized keys."""
    require_columns(table, table_name, [left_col, right_col], case_sensitive=case_sensitive)

    left_values = _table_column_values(table, left_col)
    right_values = _table_column_values(table, right_col)

    pair_keys = []
    pair_display_by_key = {}
    pair_count = {}

    for left_raw, right_raw in zip(left_values, right_values):
        left_text = str(left_raw).strip()
        right_text = str(right_raw).strip()
        left_key = left_text if case_sensitive else _normalize_token(left_text)
        right_key = right_text if case_sensitive else _normalize_token(right_text)
        key = (left_key, right_key)
        pair_keys.append(key)
        pair_display_by_key.setdefault(key, (left_text, right_text))
        pair_count[key] = pair_count.get(key, 0) + 1

    duplicate_keys = [key for key, count in pair_count.items() if count > 1]
    if duplicate_keys:
        preview = ', '.join(
            f"{pair_display_by_key[key][0]}-{pair_display_by_key[key][1]}"
            for key in duplicate_keys[:10]
        )
        raise Exception(f"{table_name} contains duplicate pair row(s): {preview}")

    return set(pair_keys)


def require_complete_pair_grid(
    pair_table,
    pair_table_name,
    left_col,
    right_col,
    left_values,
    right_values,
    left_label=None,
    right_label=None,
    case_sensitive=False,
):
    """Ensure pair table contains every combination of left_values x right_values."""
    observed_pairs = require_unique_pairs(
        pair_table,
        pair_table_name,
        left_col,
        right_col,
        case_sensitive=case_sensitive,
    )

    left_lookup = {}
    for value in left_values:
        text = str(value).strip()
        key = text if case_sensitive else _normalize_token(text)
        left_lookup[key] = text

    right_lookup = {}
    for value in right_values:
        text = str(value).strip()
        key = text if case_sensitive else _normalize_token(text)
        right_lookup[key] = text

    missing = []
    for left_key, left_text in left_lookup.items():
        for right_key, right_text in right_lookup.items():
            if (left_key, right_key) not in observed_pairs:
                missing.append(f'{left_text}-{right_text}')

    if missing:
        preview = ', '.join(missing[:10])
        left_title = left_label or left_col
        right_title = right_label or right_col
        raise Exception(
            f"{pair_table_name} missing {left_title}-{right_title} pair(s): {preview}"
        )


def validate_value_columns_against_master(
    matrix_table,
    matrix_table_name,
    master_table,
    master_table_name,
    master_value_col,
    matrix_reserved_cols=None,
    require_master_in_matrix=True,
    require_matrix_in_master=True,
    case_sensitive=False,
):
    """Validate matrix value-columns against a master key column and canonicalize names.

    Typical use: matrix table where dynamic columns represent entities listed as
    row values in a master table key column (for example cost matrix columns vs
    facility master Location values).
    """
    matrix_reserved_cols = matrix_reserved_cols or []
    require_columns(master_table, master_table_name, [master_value_col], case_sensitive=case_sensitive)

    master_values = [
        str(value).strip()
        for value in _table_column_values(master_table, master_value_col)
        if str(value).strip() != ''
    ]

    master_lookup = {}
    for value in master_values:
        key = value if case_sensitive else _normalize_token(value)
        if key in master_lookup and master_lookup[key] != value:
            raise Exception(
                f"Duplicate values in {master_table_name}.{master_value_col} (case-insensitive): "
                f"{master_lookup[key]}, {value}"
            )
        master_lookup[key] = value

    matrix_columns = _table_columns(matrix_table)
    reserved_keys = {
        col if case_sensitive else _normalize_token(col)
        for col in matrix_reserved_cols
    }

    matrix_lookup = {}
    for col in matrix_columns:
        col_text = str(col).strip()
        key = col_text if case_sensitive else _normalize_token(col_text)
        if key in reserved_keys:
            continue
        if key in matrix_lookup and matrix_lookup[key] != col:
            raise Exception(
                f"Duplicate value columns in {matrix_table_name} (case-insensitive): "
                f"{matrix_lookup[key]}, {col}"
            )
        matrix_lookup[key] = col

    if require_master_in_matrix:
        missing = [
            master_lookup[key]
            for key in master_lookup
            if key not in matrix_lookup
        ]
        if missing:
            raise Exception(
                f"Values from {master_table_name}.{master_value_col} must exist as columns in "
                f"{matrix_table_name}. Missing column(s): {', '.join(missing)}"
            )

    if require_matrix_in_master:
        unknown = [
            matrix_lookup[key]
            for key in matrix_lookup
            if key not in master_lookup
        ]
        if unknown:
            raise Exception(
                f"Value column(s) in {matrix_table_name} must exist in "
                f"{master_table_name}.{master_value_col}. Unknown column(s): {', '.join(unknown)}"
            )

    rename_map = {
        matrix_lookup[key]: master_lookup[key]
        for key in matrix_lookup
        if key in master_lookup and matrix_lookup[key] != master_lookup[key]
    }
    _rename_columns(matrix_table, rename_map)

    return {
        'master_values': [master_lookup[key] for key in master_lookup],
        'renamed_columns': rename_map,
    }


def _usage_examples():
    """Usage examples for reusable table validators.

    Matrix columns against master key column:
        matched = validate_value_columns_against_master(
            matrix_table=cost,
            matrix_table_name='cost',
            master_table=facility,
            master_table_name='facility',
            master_value_col='Location',
            matrix_reserved_cols=['Location', 'Demand'],
        )

    Pair table full Cartesian coverage:
        require_complete_pair_grid(
            pair_table=ship_cost,
            pair_table_name='ship_cost',
            left_col='Source',
            right_col='Destination',
            left_values=sources,
            right_values=destinations,
        )

    Unique key constraints:
        projects = require_unique_values(projects, 'projects', 'Project')
        require_unique_pairs(cost, 'cost', 'From', 'To')

    Optional scalar numeric parsing:
        budget = parse_optional_number(budget_limit, 'budget_limit', float)
        max_selected = parse_optional_number(project_max_selected, 'project_max_selected', int)
    """
    return None