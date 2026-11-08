# SPDX-License-Identifier: MIT
# Copyright (c) 2026
"""Small in-memory table model for qCalc.

QTable stores ordinary Python lists/dicts in qtbl shape.  qdf remains the
separate, restricted pandas computation facade.
"""

from .qb_df_proxy import qkeymap, qdf
from .qc_qty import Qty
from .qf_anno import is_qtbl
import qconst
import re
from copy import deepcopy
import pandas as pd

__all__ = ['QTable']


_TYPE_NAMES = {'integer': int, 'number': float, 'string': str, 'boolean': bool}
_TYPE_LABELS = {int: 'integer', float: 'number', str: 'string', bool: 'boolean'}


def _spec(raw):
    return {'type': raw} if isinstance(raw, type) else dict(raw)


def _spec_type(spec, name='table', col=''):
    """Return the Python type of a schema spec (``type`` may be a JSON type name)."""
    typ = spec.get('type')
    if isinstance(typ, str):
        if typ not in _TYPE_NAMES:
            raise ValueError(f'{name}: unknown schema type for {col}: {typ!r}')
        return _TYPE_NAMES[typ]
    return typ


def _fields(value):
    """Normalize a column or list of columns into a list of strings."""
    return [value] if isinstance(value, str) else list(value)


def _blank(value):
    """Check if a value is considered blank (None or empty string)."""
    return value is None or (isinstance(value, str) and not value.strip())


def _key(values):
    """Return a key tuple for the given list of values, using a single value if only one element is present."""
    return values[0] if len(values) == 1 else tuple(values)


def _unique_specs(unique):
    """Normalize the unique constraint specification into a list of lists of column names."""
    if unique is None:
        return []
    if isinstance(unique, str):
        return [[unique]]
    values = list(unique)
    if not values:
        return []
    if all(isinstance(v, str) for v in values):
        return [[v] for v in values]
    return [_fields(v) for v in values]


class QTable:
    """A compact, schema-aware table backed by native Python data.

    ``data`` accepts a qtbl dictionary, a list of row dictionaries, or a list
    of row lists (when ``columns`` is supplied).  A qtbl produced by
    ``to_dict(full=True)`` also restores its schema and key definitions.
    """

    def __init__(self, data=None, columns=None, schema=None, primary_key=None,
                 unique=None, name=None, validate=False):
        """Initialize a QTable instance with the given data, columns, schema, and constraints."""
        if isinstance(data, dict):
            # If the data is a dictionary, it should represent a qtbl with 'columns' and 'data' keys.
            if not is_qtbl(data):
                raise TypeError("A table dictionary must contain 'columns' and 'data'")
            if columns is not None:
                raise ValueError('Do not pass columns when data is a qtbl.')
            schema = data.get('schema') if schema is None else schema
            primary_key = data.get('primary_key') if primary_key is None else primary_key
            unique = data.get('unique') if unique is None else unique
            columns, data = data['columns'], data['data']
        elif isinstance(data, pd.DataFrame):
            # If the data is a pandas DataFrame, ensure the specified columns (if any) exist and convert to a list of lists.
            if columns is None:
                columns = list(data.columns)
            else:
                columns = list(columns)
            missing_cols = [col for col in columns if col not in data.columns]
            if missing_cols:
                table_name = name or 'table'
                raise ValueError(
                    f"{table_name}: column(s) not found in DataFrame: {', '.join(map(str, missing_cols))}"
                )
            data = data[columns].values.tolist()
        elif data and isinstance(data, (list, tuple)) and isinstance(data[0], dict):
            # Convert a list of row dictionaries into a list of row lists, using the specified columns or inferred columns.
            if columns is None:
                columns = list(dict.fromkeys(k for row in data for k in row))
            data = [[row.get(col) for col in columns] for row in data]

        self.name = name or 'table'
        self.schema = deepcopy(schema or {})
        self.primary_key = _fields(primary_key) if primary_key is not None else []
        self.unique = _unique_specs(unique)
        self._columns = list(columns or self.schema.keys())
        self._data = deepcopy(list(data or []))
        if validate:
            self.validate(raise_exception=True)
        else:
            self._check_structure()

    def _check_structure(self):
        """Check the table's structure for consistency, including column names, row lengths, and key constraints."""
        if not all(isinstance(c, str) and c for c in self._columns):
            raise TypeError(f'{self.name}: column names must be non-empty strings')
        if len(set(self._columns)) != len(self._columns):
            raise ValueError(f'{self.name}: column names must be unique')
        if not isinstance(self._data, list):
            raise TypeError(f'{self.name}: data must be a list')
        for i, row in enumerate(self._data):
            if not isinstance(row, (list, tuple)) or len(row) != len(self._columns):
                raise ValueError(f'{self.name}: row {i + 1} must contain {len(self._columns)} values')
            self._data[i] = list(row)
        for col in self.primary_key + [c for spec in self.unique for c in spec]:
            if col not in self._columns:
                raise ValueError(f'{self.name}: key column not found: {col}')
        for col, raw in self.schema.items():
            _spec_type(_spec(raw), self.name, col)

    def _index(self, col):
        """Return the index of the specified column in the table."""
        try:
            return self._columns.index(col)
        except ValueError:
            raise KeyError(f'{self.name}: Unknown column: {col}') from None

    @property
    def columns(self):
        """Return the list of column names in the table."""
        return list(self._columns)

    @property
    def data(self):
        """Return a deep copy of the table's data as a list of rows."""
        return deepcopy(self._data)

    @property
    def shape(self):
        """Return a tuple (nrows, ncols) representing the table's dimensions."""
        return len(self._data), len(self._columns)

    @property
    def nrows(self):
        """Return the number of rows in the table."""
        return len(self._data)

    @property
    def ncols(self):
        """Return the number of columns in the table."""
        return len(self._columns)

    def __len__(self):
        """Return the number of rows in the table."""
        return self.nrows

    def __iter__(self):
        """Return an iterator over the table's records as dictionaries."""
        return iter(self.records(skip_blank=False, skip_header=False, strip=False))

    def __repr__(self):
        """Return a string representation of the table."""
        return f'QTable(name={self.name!r}, shape={self.shape})'

    def to_dict(self, full=False):
        """Return a detached qtbl-compatible ``{columns, data}`` payload.

        ``full=True`` also includes the JSON-friendly schema, primary key and
        unique keys so the table can be rebuilt with ``QTable(payload)``
        (custom ``cast``/``validator`` callables are not serialized).
        """
        out = {'columns': self.columns, 'data': self.data}
        if full:
            out.update(schema=self.schema_dict(), primary_key=list(self.primary_key),
                       unique=[list(spec) for spec in self.unique])
        return out

    def schema_dict(self):
        """Return JSON-friendly schema metadata for a frontend editor."""
        out = {}
        for col, raw in self.schema.items():
            spec = _spec(raw)
            typ = _spec_type(spec, self.name, col) or str
            spec['type'] = _TYPE_LABELS.get(typ, 'string')
            spec.pop('cast', None)
            spec.pop('validator', None)
            out[col] = spec
        return out

    def row(self, index):
        """Return the row at the given index as a list."""
        return list(self._data[index])

    def column(self, name):
        """Return the column with the given name as a list."""
        idx = self._index(name)
        return [row[idx] for row in self._data]

    def records(self, cols=None, skip_blank=True, skip_header=True, strip=True):
        """Return the table as a list of dictionaries, optionally filtered by columns."""
        cols = list(cols) if cols is not None else self.columns
        indexes = [self._index(c) for c in cols]
        result = []
        for row in self._data:
            rec = {}
            for col, idx in zip(cols, indexes):
                value = row[idx]
                rec[col] = value.strip() if strip and isinstance(value, str) else value
            if skip_blank and all(_blank(v) for v in rec.values()):
                continue
            if skip_header and all(str(rec[c]).strip().casefold() == str(c).strip().casefold() for c in cols):
                continue
            result.append(rec)
        return result

    def read(self, cols=None, casts=None, key=None, value=None, unique=True,
             skip_blank=True, skip_header=True, strip=True):
        """Read normalized records, optionally as a key/value mapping based on the primary key."""
        rows = self.records(cols, skip_blank, skip_header, strip)
        casts = casts or {}
        for i, rec in enumerate(rows):
            for col, caster in casts.items():
                if col not in rec:
                    raise KeyError(f'{self.name}: Unknown cast column: {col}')
                try:
                    rec[col] = caster(rec[col])
                except Exception as exc:
                    raise ValueError(f'{self.name}: Invalid value at row {i + 1}, column {col}: {exc}') from exc
        if key is None and value is None:
            return rows
        if key is None or value is None:
            raise ValueError(f'{self.name}: Both key and value must be provided for mapping output.')
        try:
            return qkeymap(rows, key, value, unique=unique)
        except Exception as exc:
            raise ValueError(f'{self.name}: {exc}') from exc

    def get(self, key):
        """Return the record matching the given primary key, or None if not found."""
        if not self.primary_key:
            raise ValueError(f'{self.name}: no primary key is defined')
        wanted = _fields(key) if len(self.primary_key) > 1 else [key]
        if len(wanted) != len(self.primary_key):
            raise ValueError('Incorrect primary-key value')
        for rec in self.records(skip_blank=False, skip_header=False, strip=False):
            if _key([rec[c] for c in self.primary_key]) == _key(wanted):
                return rec
        return None

    def _check_criteria(self, criteria):
        """Ensure that all keys in the criteria exist as columns."""
        for k in criteria:
            self._index(k)

    def find(self, **criteria):
        """Return the first record matching the given criteria, or None if not found."""
        self._check_criteria(criteria)
        for rec in self.records(skip_blank=False, skip_header=False, strip=False):
            if all(rec[k] == v for k, v in criteria.items()):
                return rec
        return None

    def filter(self, **criteria):
        """Return all records matching the given criteria."""
        self._check_criteria(criteria)
        return [r for r in self.records(skip_blank=False, skip_header=False, strip=False)
                if all(r[k] == v for k, v in criteria.items())]

    def _prepare(self, record, base=None):
        """Prepare a record for insertion or update, ensuring it conforms to the schema."""
        if not isinstance(record, dict):
            raise TypeError('A row must be a dictionary')
        unknown = set(record) - set(self._columns)
        if unknown:
            raise KeyError(f'{self.name}: Unknown column(s): {", ".join(map(str, unknown))}')
        rec = dict(base or {c: None for c in self._columns})
        rec.update(record)
        for col, raw_spec in self.schema.items():
            spec = _spec(raw_spec)
            value = rec.get(col)
            if _blank(value):
                if 'default' in spec and value is None:
                    value = rec[col] = deepcopy(spec['default'])
                if spec.get('required') and _blank(value):
                    raise ValueError(f'{self.name}: {col} is required')
                if not spec.get('nullable', True) and _blank(value):
                    raise ValueError(f'{self.name}: {col} cannot be blank')
                continue
            caster = spec.get('cast')
            typ = _spec_type(spec, self.name, col)
            try:
                if caster:
                    value = caster(value)
                elif typ is int and isinstance(value, float):
                    if value != int(value):
                        raise ValueError('not a whole number')
                    value = int(value)
                elif typ and not isinstance(value, typ):
                    if typ is bool and isinstance(value, str):
                        value = value.strip().casefold() in ('1', 'true', 'yes', 'on')
                    else:
                        value = typ(value)
            except Exception as exc:
                raise ValueError(f'{self.name}: invalid {col}: {value!r} ({exc})') from exc
            rec[col] = value
            if 'min' in spec and value < spec['min']:
                raise ValueError(f'{self.name}: {col} must be at least {spec["min"]}')
            if 'max' in spec and value > spec['max']:
                raise ValueError(f'{self.name}: {col} must be at most {spec["max"]}')
            if 'max_length' in spec and len(value) > spec['max_length']:
                raise ValueError(f'{self.name}: {col} exceeds {spec["max_length"]} characters')
            if 'choices' in spec and value not in spec['choices']:
                raise ValueError(f'{self.name}: invalid {col}: {value!r}')
            if spec.get('validator') and spec['validator'](value) is False:
                raise ValueError(f'{self.name}: invalid value for {col}: {value!r}')
        return rec

    def _check_keys(self, rows, ignore=None):
        """Check for duplicate keys in the given rows based on primary and unique keys."""
        specs = ([self.primary_key] if self.primary_key else []) + self.unique
        for spec in specs:
            seen = set()
            for i, rec in enumerate(rows):
                vals = [rec[c] for c in spec]
                if any(_blank(v) for v in vals):
                    if spec == self.primary_key:
                        raise ValueError(f'{self.name}: primary key {spec} cannot be blank (row {i + 1})')
                    continue
                k = _key(vals)
                if k in seen:
                    raise ValueError(f'{self.name}: duplicate key {k!r} for {spec}')
                seen.add(k)

    def validate(self, coerce=True, raise_exception=False):
        """Validate the table's structure, schema, and keys; return ``{'valid', 'errors'}``."""
        errors = []
        try:
            self._check_structure()
            missing = set(self.schema) - set(self._columns)
            if missing:
                raise ValueError(f'Missing schema column(s): {", ".join(sorted(missing))}')
            rows = []
            for i, values in enumerate(self._data):
                raw = dict(zip(self._columns, values))
                try:
                    rows.append(self._prepare(raw))
                except Exception as exc:
                    raise ValueError(f'row {i + 1}: {exc}') from exc
            self._check_keys(rows)
            if coerce:
                self._data = [[r[c] for c in self._columns] for r in rows]
        except Exception as exc:
            errors.append(str(exc))
        if errors and raise_exception:
            raise ValueError('; '.join(errors))
        return {'valid': not errors, 'errors': errors}

    def _commit(self, rows):
        """Commit the given rows to the table, ensuring key constraints are satisfied."""
        self._check_keys(rows)
        self._data = [[row[c] for c in self._columns] for row in rows]

    def add(self, record):
        """Add a single record to the table, ensuring key constraints are satisfied."""
        rec = self._prepare(record)
        rows = self.records(skip_blank=False, skip_header=False, strip=False) + [rec]
        self._commit(rows)
        return rec

    def add_many(self, records):
        """Add multiple records to the table, ensuring key constraints are satisfied."""
        rows = self.records(skip_blank=False, skip_header=False, strip=False)
        new_rows = [self._prepare(rec) for rec in records]
        self._commit(rows + new_rows)
        return new_rows

    def update(self, key, changes):
        """Update the record matching the given primary key with the specified changes."""
        if not self.primary_key:
            raise ValueError(f'{self.name}: no primary key is defined')
        rows = self.records(skip_blank=False, skip_header=False, strip=False)
        wanted = _fields(key) if len(self.primary_key) > 1 else [key]
        for i, rec in enumerate(rows):
            if _key([rec[c] for c in self.primary_key]) == _key(wanted):
                rows[i] = self._prepare(changes, rec)
                self._commit(rows)
                return rows[i]
        raise KeyError(f'{self.name}: record not found: {key!r}')

    def delete(self, key):
        """Delete the record matching the given primary key; return True if deleted, False if not found."""
        if not self.primary_key:
            raise ValueError(f'{self.name}: no primary key is defined')
        wanted = _fields(key) if len(self.primary_key) > 1 else [key]
        rows = self.records(skip_blank=False, skip_header=False, strip=False)
        kept = [r for r in rows if _key([r[c] for c in self.primary_key]) != _key(wanted)]
        if len(kept) == len(rows):
            return False
        self._commit(kept)
        return True

    def clear(self):
        """Clear all records from the table."""
        self._data = []

    def _sync_validation_columns(self, payload, old_columns):
        """Synchronize the table's columns with the canonical header names after validation."""
        new_columns = list(payload["columns"])
        if new_columns == old_columns:
            return
        rename = dict(zip(old_columns, new_columns))
        self._columns = new_columns
        self.schema = {rename.get(col, col): spec for col, spec in self.schema.items()}
        self.primary_key = [rename.get(col, col) for col in self.primary_key]
        self.unique = [[rename.get(col, col) for col in spec] for spec in self.unique]

    @staticmethod
    def _normalize_token(value):
        return str(value).strip().casefold()

    @staticmethod
    def _compact_token(value):
        return ''.join(ch for ch in str(value).casefold() if ch.isalnum())

    def _optional_name_words(self, value):
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

    def _looks_like_optional_alias(self, candidate, optional_name):
        candidate_norm = self._normalize_token(candidate)
        optional_norm = self._normalize_token(optional_name)
        if candidate_norm == optional_norm:
            return False

        candidate_compact = self._compact_token(candidate)
        optional_compact = self._compact_token(optional_name)
        if not candidate_compact or not optional_compact:
            return False

        if candidate_compact == optional_compact:
            return True
        if candidate_compact.startswith(optional_compact) or optional_compact.startswith(candidate_compact):
            return True

        c_words = self._optional_name_words(candidate)
        o_words = self._optional_name_words(optional_name)
        if not c_words or not o_words:
            return False

        for ow in o_words:
            if len(ow) < 2:
                continue
            if not any(cw.startswith(ow[:3]) or ow.startswith(cw[:3]) for cw in c_words if len(cw) >= 2):
                return False
        return True

    @staticmethod
    def _strict_table_input_enabled():
        try:
            from qutil import QThread
            return bool(QThread.get_pref('strict_table_input', False))
        except Exception:
            return False

    @staticmethod
    def _split_column_title_uom(column_name, uom_sep=qconst.TBL_UOM_SEP):
        text = str(column_name).strip()
        if uom_sep not in text:
            return text, None
        base_name, header_uom = text.split(uom_sep, 1)
        return base_name.strip(), header_uom.strip()

    def _apply_column_renames(self, rename_map):
        if not rename_map:
            return
        old_columns = self.columns
        payload = {'columns': [rename_map.get(col, col) for col in old_columns]}
        self._sync_validation_columns(payload, old_columns)

    def assert_columns(self, required_cols, optional_cols=None,
                        case_sensitive=False, columns_can_grow=True,
                        required_col_uoms=None):
        """Validate table headers against a required/optional schema.

        Args:
            required_cols: Column names that must exist.
            optional_cols: Additional allowed columns (not mandatory).
            case_sensitive: Whether header matching is case-sensitive.
            columns_can_grow: When False (with Strict Table Input mode enabled),
                unknown columns are rejected.
            required_col_uoms: Optional ``{column: expected_uom}`` map to allow
                unitized headers like ``"Flow :: m3/hr"`` and verify unit
                compatibility.

        Returns:
            Mapping of canonical expected names to actual/resolved column names.

        Example:
            a) table.assert_columns(['Customer', 'Demand'])

            b) table.assert_columns(
                required_cols=['Project', 'Budget'],
                optional_cols=['Manager'],
                case_sensitive=False,
                columns_can_grow=True,
                required_col_uoms={'Budget': 'USD'},
            )

        Notes:
            The method may rename columns in-place to canonical names (for
            example fixing case/spacing or preserving a validated header unit).
        """
        optional_cols = optional_cols or []
        expected_cols = list(required_cols) + [col for col in optional_cols if col not in required_cols]
        actual_cols = self.columns
        required_col_uoms = required_col_uoms or None

        actual_meta = []
        base_seen = {}
        duplicate_bases = []
        unitized_cols = []

        for col in actual_cols:
            base_name, header_uom = self._split_column_title_uom(col)
            has_uom = qconst.TBL_UOM_SEP in str(col)
            if has_uom:
                unitized_cols.append(str(col))

            base_key = base_name if case_sensitive else self._normalize_token(base_name)
            if base_key in base_seen and base_seen[base_key] != col:
                duplicate_bases.append((base_seen[base_key], col))
                continue

            base_seen[base_key] = col
            actual_meta.append({
                'actual': col,
                'base': base_name,
                'uom': header_uom,
                'has_uom': has_uom,
                'key': base_key,
            })

        if duplicate_bases:
            pairs = ', '.join(f"'{left}' vs '{right}'" for left, right in duplicate_bases)
            raise ValueError(
                f"Ambiguous column names detected (same base name after trimming/unit split): {pairs}. "
                'Please keep one canonical version.'
            )

        if required_col_uoms is None and unitized_cols:
            preview = ', '.join(f"'{name}'" for name in unitized_cols[:10])
            raise ValueError(
                f"{self.name}: One or more column headers include a unit using '{qconst.TBL_UOM_SEP}'. "
                f"This table expects plain header names without units in the title. "
                f"Please remove the unit from these header(s): {preview}."
            )

        if required_col_uoms is not None:
            canonical_required_uoms = {
                self._normalize_token(k): (str(k).strip(), str(v).strip())
                for k, v in required_col_uoms.items()
            }
            for item in actual_meta:
                if not item['has_uom']:
                    continue
                base_name = item['base']
                header_uom = item['uom']
                base_key = self._normalize_token(base_name)
                if base_key not in canonical_required_uoms:
                    raise ValueError(
                        f"{self.name} column '{item['actual']}' does not allow units in the header title. "
                        f"Expected plain header names unless explicitly configured in required_col_uoms."
                    )
                _, expected_uom = canonical_required_uoms[base_key]
                try:
                    Qty(1.0, header_uom, expected_uom)
                except Exception as e:
                    raise ValueError(
                        f"{self.name} column '{item['actual']}' unit '{header_uom}' is not compatible with "
                        f"expected unit '{expected_uom}' for '{base_name}'."
                    ) from e

        actual_bases = [item['base'] for item in actual_meta]
        if case_sensitive:
            missing = [col for col in required_cols if col not in actual_bases]
            if missing:
                expected = ', '.join(expected_cols)
                raise ValueError(
                    f"{self.name} missing required column(s): {', '.join(missing)}. "
                    f"Expected columns: {expected}."
                )
            return {
                col: next(item['actual'] for item in actual_meta if item['base'] == col)
                for col in expected_cols
                if col in actual_bases
            }

        lookup = {item['key']: item['actual'] for item in actual_meta}
        lookup_base = {item['key']: item['base'] for item in actual_meta}

        missing = [col for col in required_cols if self._normalize_token(col) not in lookup]
        if missing:
            expected = ', '.join(expected_cols)
            raise ValueError(
                f"{self.name} missing required column(s): {', '.join(missing)}. "
                f"Expected columns: {expected}."
            )

        strict_mode = self._strict_table_input_enabled()
        if optional_cols and strict_mode:
            expected_keys = {self._normalize_token(col) for col in expected_cols}
            suspicious = []
            for item in actual_meta:
                actual_col = item['actual']
                actual_key = item['key']
                if actual_key in expected_keys:
                    continue
                for opt_col in optional_cols:
                    if self._looks_like_optional_alias(lookup_base.get(actual_key, actual_col), opt_col):
                        suspicious.append((actual_col, opt_col))
                        break
            if suspicious:
                preview = ', '.join(f"'{actual}' ~ '{expected}'" for actual, expected in suspicious[:10])
                expected = ', '.join(expected_cols)
                raise ValueError(
                    f"{self.name} has suspicious column name(s) under Strict Table Input mode: {preview}. "
                    f"Rename these columns to the expected canonical names. Expected columns: {expected}."
                )

        if strict_mode and not columns_can_grow:
            expected_keys = {self._normalize_token(col) for col in expected_cols}
            unexpected = [
                str(item['actual'])
                for item in actual_meta
                if item['key'] not in expected_keys
            ]
            if unexpected:
                allowed = ', '.join(expected_cols)
                found = ', '.join(unexpected[:10])
                raise ValueError(
                    f"{self.name} has unexpected column(s) under Strict Table Input mode: {found}. "
                    f"Allowed columns: {allowed}."
                )

        rename_map = {}
        resolved = {}
        for col in expected_cols:
            key = self._normalize_token(col)
            actual = lookup.get(key)
            if actual is None:
                continue
            actual_base = lookup_base.get(key, col)
            _, header_uom = self._split_column_title_uom(actual)

            resolved[col] = actual
            if header_uom:
                canonical = f'{col} {qconst.TBL_UOM_SEP} {header_uom}'
            elif actual_base != col or actual != actual_base:
                canonical = col
            else:
                canonical = actual

            if actual != canonical:
                rename_map[actual] = canonical
                resolved[col] = canonical

        self._apply_column_renames(rename_map)
        return resolved

    def assert_unique(self, column_name, case_sensitive=False, ignore_blank=False):
        """Ensure a column has unique values and return canonical values.

        Useful for key columns such as Project, Item, Worker, Shift, etc.

        Example:
            canonical_values = table.assert_unique(
                column_name='Project',
                case_sensitive=False,
                ignore_blank=True,
            )
        """
        resolved = self.assert_columns([column_name], case_sensitive=case_sensitive)
        col = resolved.get(column_name, column_name)
        values = self.column(col)

        seen = {}
        duplicates = []
        ordered_keys = []
        for value in values:
            text = str(value).strip()
            if ignore_blank and text == '':
                continue
            key = text if case_sensitive else self._normalize_token(text)
            if key in seen:
                duplicates.append((seen[key], text))
            else:
                seen[key] = text
                ordered_keys.append(key)

        if duplicates:
            preview = ', '.join(f"{left}/{right}" for left, right in duplicates[:10])
            raise ValueError(f"{self.name} '{col}' has duplicate value(s): {preview}")

        return [seen[key] for key in ordered_keys]

    def assert_unique_pairs(self, left_col, right_col, case_sensitive=False):
        """Ensure each ``(left_col, right_col)`` combination appears at most once.

        Returns:
            Set of normalized pair keys suitable for downstream membership checks.

        Example:
            table.assert_unique_pairs(
                left_col='From',
                right_col='To',
                case_sensitive=False,
            )
        """
        resolved = self.assert_columns([left_col, right_col], case_sensitive=case_sensitive)
        left_name = resolved.get(left_col, left_col)
        right_name = resolved.get(right_col, right_col)

        left_values = self.column(left_name)
        right_values = self.column(right_name)

        pair_keys = []
        pair_display_by_key = {}
        pair_count = {}

        for left_raw, right_raw in zip(left_values, right_values):
            left_text = str(left_raw).strip()
            right_text = str(right_raw).strip()
            left_key = left_text if case_sensitive else self._normalize_token(left_text)
            right_key = right_text if case_sensitive else self._normalize_token(right_text)
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
            raise ValueError(f"{self.name} contains duplicate pair row(s): {preview}")

        return set(pair_keys)

    def assert_foreign_key(self, parent, child_col, parent_col,
                              case_sensitive=False):
        """Ensure each non-blank child value exists in the parent value set.

        Use this for foreign-key style checks between two input tables.

        Example:
            child_table.assert_foreign_key(
                parent=parent_table,
                child_col='Project',
                parent_col='Project',
                case_sensitive=False,
            )
        """
        child_resolved = self.assert_columns([child_col], case_sensitive=case_sensitive)
        parent_resolved = parent.assert_columns([parent_col], case_sensitive=case_sensitive)
        child_name = child_resolved.get(child_col, child_col)
        parent_name = parent_resolved.get(parent_col, parent_col)

        parent_values = {
            str(value).strip(): value
            for value in parent.column(parent_name)
            if str(value).strip() != ''
        }
        if case_sensitive:
            parent_keys = set(parent_values.keys())
            child_keys = [str(value).strip() for value in self.column(child_name) if str(value).strip() != '']
        else:
            parent_keys = {self._normalize_token(value) for value in parent_values.keys()}
            child_keys = [
                self._normalize_token(value)
                for value in self.column(child_name)
                if str(value).strip() != ''
            ]

        unknown = sorted({key for key in child_keys if key not in parent_keys})
        if unknown:
            typed = {self._normalize_token(v): str(v).strip() for v in self.column(child_name)}
            unknown_preview = ', '.join(typed.get(key, key) for key in unknown[:10])
            raise ValueError(
                f"{self.name} '{child_name}' has value(s) not found in "
                f"{parent.name} '{parent_name}': {unknown_preview}"
            )

    def assert_complete_cross_join(self, left_col, right_col, left_values,
                                   right_values, left_label=None,
                                   right_label=None, case_sensitive=False):
        """Ensure the pair table contains the full Cartesian grid.

        Specifically, every combination from ``left_values Ãƒâ€” right_values`` must
        exist exactly once in ``(left_col, right_col)``.

        Example:
            table.assert_complete_cross_join(
                left_col='Source',
                right_col='Destination',
                left_values=sources,
                right_values=destinations,
            )
        """
        observed_pairs = self.assert_unique_pairs(left_col, right_col, case_sensitive=case_sensitive)

        left_lookup = {}
        for value in left_values:
            text = str(value).strip()
            key = text if case_sensitive else self._normalize_token(text)
            left_lookup[key] = text

        right_lookup = {}
        for value in right_values:
            text = str(value).strip()
            key = text if case_sensitive else self._normalize_token(text)
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
            raise ValueError(
                f"{self.name} missing {left_title}-{right_title} pair(s): {preview}"
            )

    def assert_columns_match_domain(self, master, master_value_col,
                              matrix_reserved_cols=None,
                              require_master_in_matrix=True,
                              require_matrix_in_master=True,
                              case_sensitive=False):
        """Validate matrix value-columns against a master key list.

        Typical use: matrix table where dynamic columns represent entities listed
        as row values in a master table key column (for example cost matrix
        columns vs facility master Location values).

        Returns:
            Dict containing canonical ``master_values`` and ``renamed_columns``
            applied to the matrix table.

        Example:
            matched = matrix.assert_columns_match_domain(
                master=facility,
                master_value_col='Location',
                matrix_reserved_cols=['Location', 'Demand'],
            )
        """
        matrix_reserved_cols = matrix_reserved_cols or []
        master_resolved = master.assert_columns([master_value_col], case_sensitive=case_sensitive)
        master_col_name = master_resolved.get(master_value_col, master_value_col)

        master_values = [
            str(value).strip()
            for value in master.column(master_col_name)
            if str(value).strip() != ''
        ]

        master_lookup = {}
        for value in master_values:
            key = value if case_sensitive else self._normalize_token(value)
            if key in master_lookup and master_lookup[key] != value:
                raise ValueError(
                    f"Duplicate values in {master.name} '{master_col_name}' (case-insensitive): "
                    f"{master_lookup[key]}, {value}"
                )
            master_lookup[key] = value

        matrix_columns = self.columns
        reserved_keys = {
            col if case_sensitive else self._normalize_token(col)
            for col in matrix_reserved_cols
        }

        matrix_lookup = {}
        for col in matrix_columns:
            col_text = str(col).strip()
            key = col_text if case_sensitive else self._normalize_token(col_text)
            if key in reserved_keys:
                continue
            if key in matrix_lookup and matrix_lookup[key] != col:
                raise ValueError(
                    f"Duplicate value columns in {self.name} (case-insensitive): "
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
                raise ValueError(
                    f"Values from {master.name} '{master_col_name}' must exist as columns in "
                    f"{self.name}. Missing column(s): {', '.join(missing)}"
                )

        if require_matrix_in_master:
            unknown = [
                matrix_lookup[key]
                for key in matrix_lookup
                if key not in master_lookup
            ]
            if unknown:
                raise ValueError(
                    f"Value column(s) in {self.name} must exist in "
                    f"{master.name} '{master_col_name}'. Unknown column(s): {', '.join(unknown)}"
                )

        rename_map = {
            matrix_lookup[key]: master_lookup[key]
            for key in matrix_lookup
            if key in master_lookup and matrix_lookup[key] != master_lookup[key]
        }
        self._apply_column_renames(rename_map)

        return {
            'master_values': [master_lookup[key] for key in master_lookup],
            'renamed_columns': rename_map,
        }

    def df(self):
        """Return qCalc's restricted qdf facade (never a raw DataFrame)."""
        return qdf(self.to_dict())
