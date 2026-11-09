# SPDX-License-Identifier: MIT
# Copyright (c) 2026
"""Small in-memory table model for qCalc.

QTable stores ordinary Python lists/dicts in qtbl shape.  qdf remains the
separate, restricted pandas computation facade.
"""

from .qb_df_proxy import qdf
from .qc_qty import Qty
from .qd_data import is_empty_cell as _blank
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


_NAME_ALIASES = {'minimum': 'min', 'maximum': 'max', 'quantity': 'qty'}


def _name_words(value):
    """Split a column name into lowercase words, mapping common long forms to short ones."""
    return [_NAME_ALIASES.get(w, w) for w in re.findall(r'[a-z0-9]+', str(value).casefold())]


def _looks_like_alias(candidate, expected):
    """Return True if ``candidate`` is a near-miss spelling of ``expected`` (not an exact match)."""
    if str(candidate).strip().casefold() == str(expected).strip().casefold():
        return False
    c_words, e_words = _name_words(candidate), _name_words(expected)
    c_text, e_text = ''.join(c_words), ''.join(e_words)
    if not c_text or not e_text:
        return False
    key_words = [w for w in e_words if len(w) >= 2]
    return (c_text.startswith(e_text) or e_text.startswith(c_text)
            or bool(key_words) and all(w in c_words for w in key_words))


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

    Column names are always matched case-insensitively (as in most databases).
    ``case_sensitive`` only controls how *values* are compared by the
    ``assert_*`` checks (unique, foreign key, cross join, domain match).
    """

    def __init__(self, data=None, columns=None, schema=None, primary_key=None,
                 unique=None, name=None, validate=True, case_sensitive=False):
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
            # astype(object) keeps each column's own type (an int column must not become float)
            data = data[columns].astype(object).values.tolist()
        elif data and isinstance(data, (list, tuple)) and isinstance(data[0], dict):
            # Convert a list of row dictionaries into a list of row lists, using the specified columns or inferred columns.
            if columns is None:
                columns = list(dict.fromkeys(k for row in data for k in row))
            data = [[row.get(col) for col in columns] for row in data]

        self.name = name or 'table'
        self.case_sensitive = bool(case_sensitive)
        self.schema = deepcopy(schema or {})
        self.primary_key = _fields(primary_key) if primary_key is not None else []
        self.unique = _unique_specs(unique)
        self._columns = list(columns or self.schema.keys())
        self._data = deepcopy(list(data or []))
        if validate:
            self.validate(raise_exception=True)
        else:
            self._check_structure()

    @classmethod
    def optional(cls, value, **kwargs):
        """Build a validated table, or return None when the input is missing or has no rows.

        Use it for optional table inputs; ``kwargs`` are the usual ``QTable`` arguments.
        """
        if value is None:
            return None
        table = cls(value, validate=False, **kwargs)
        if not table.select():
            return None
        table.validate(raise_exception=True)
        return table

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
        """Return an iterator over the table's raw records as dictionaries."""
        return iter(self.select(skip_blank=False, skip_header=False, strip=False))

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
            spec.setdefault('required', True)
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

    def select(self, cols=None, where=None, *, skip_blank=True, skip_header=True,
               strip=True, **criteria):
        """Return records with a subset of columns and filtered rows (SQL SELECT ... WHERE).

        Args:
            cols: Columns to return, in the given order. Defaults to all columns.
            where: Optional predicate called with the full record dictionary
                (so it may use columns that are not selected); keep rows for
                which it returns true.
            skip_blank: Skip rows where all selected values are blank.
            skip_header: Skip repeated header rows present in the table data.
            strip: Trim leading/trailing spaces from string cell values.
            **criteria: Equality conditions combined with AND.

        Example:
            table.select(['Name', 'Salary'], Dept='IT')
            table.select(['Name'], where=lambda r: r['Salary'] >= 60)
        """
        cols = self.columns if cols is None else list(cols)
        for col in cols + list(criteria):
            self._index(col)
        whole = cols == self._columns
        result = []
        for row in self._data:
            rec = {c: v.strip() if strip and isinstance(v, str) else v for c, v in zip(self._columns, row)}
            picked = rec if whole else {c: rec[c] for c in cols}
            if skip_blank and all(_blank(v) for v in picked.values()):
                continue
            if skip_header and all(str(picked[c]).strip().casefold() == str(c).strip().casefold() for c in cols):
                continue
            if all(rec[k] == v for k, v in criteria.items()) and (where is None or where(rec)):
                result.append(picked)
        return result

    def to_map(self, key, value, unique=True):
        """Return ``{key: value}`` built from the table rows (multiple fields form tuples).

        Rows are read like ``select`` (blank and repeated header rows skipped). A blank
        key raises ``ValueError``; blank values are kept as they are. With ``unique=True``
        a duplicate key raises ``ValueError``.

        Example:
            table.to_map(['Category', 'Key'], ['Label', 'Factor'])
        """
        key_fields, value_fields = _fields(key), _fields(value)
        out = {}
        for rec in self.select(key_fields + value_fields):
            self._check_key_filled(rec, key_fields)
            map_key = _key([rec[k] for k in key_fields])
            if unique and map_key in out:
                raise ValueError(f'{self.name}: Duplicate key: {map_key}')
            out[map_key] = _key([rec[v] for v in value_fields])
        return out

    def _check_key_filled(self, rec, key_fields):
        """Raise when any key cell of a record is empty."""
        if any(_blank(rec[c]) for c in key_fields):
            raise ValueError(f'{self.name}: blank key {key_fields} in row {rec}')

    def sum_by(self, key, value):
        """Return ``{key: total}`` summing a column per key (SQL ``SUM ... GROUP BY``).

        Rows are read like ``select``; multiple key fields form tuple keys. A blank key
        raises ``ValueError``; blank values add nothing, as in SQL ``SUM``.

        Example:
            demand.sum_by(['Period', 'Product'], 'Demand')
        """
        key_fields = _fields(key)
        out = {}
        for rec in self.select(key_fields + [value]):
            self._check_key_filled(rec, key_fields)
            k = _key([rec[c] for c in key_fields])
            out[k] = out.get(k, 0) + (0 if _blank(rec[value]) else rec[value])
        return out

    def get(self, key):
        """Return the record matching the given primary key, or None if not found."""
        if not self.primary_key:
            raise ValueError(f'{self.name}: no primary key is defined')
        wanted = _fields(key) if len(self.primary_key) > 1 else [key]
        if len(wanted) != len(self.primary_key):
            raise ValueError('Incorrect primary-key value')
        for rec in self:
            if _key([rec[c] for c in self.primary_key]) == _key(wanted):
                return rec
        return None

    def find(self, **criteria):
        """Return the first raw record matching the given criteria, or None if not found."""
        rows = self.select(skip_blank=False, skip_header=False, strip=False, **criteria)
        return rows[0] if rows else None

    def _prepare(self, record):
        """Coerce and check one record against the schema; return the prepared record."""
        if not isinstance(record, dict):
            raise TypeError('A row must be a dictionary')
        unknown = set(record) - set(self._columns)
        if unknown:
            raise KeyError(f'{self.name}: Unknown column(s): {", ".join(map(str, unknown))}')
        rec = dict.fromkeys(self._columns)
        rec.update(record)
        for col, raw_spec in self.schema.items():
            spec = _spec(raw_spec)
            value = rec.get(col)
            typ = _spec_type(spec, self.name, col)
            if _blank(value):
                if 'default' in spec:
                    value = rec[col] = deepcopy(spec['default'])
                if spec.get('required', True) and _blank(value):
                    raise ValueError(f'{self.name}: {col} is required')
                if not spec.get('nullable', True) and _blank(value):
                    raise ValueError(f'{self.name}: {col} cannot be blank')
                if _blank(value):
                    rec[col] = '' if typ is str else None
                continue
            caster = spec.get('cast')
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
            if spec.get('strip', typ is str) and isinstance(value, str):
                value = rec[col] = value.strip()
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

    def _check_keys(self, rows):
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
        """Validate the table's structure, schema, and keys; return ``{'valid', 'errors'}``.

        Schema columns are required headers (unless the column is declared
        ``required: False``): they are matched case/space-insensitively
        and renamed to the schema's spelling before values are coerced and checked.
        Fully blank rows (the spare rows added in the input grid) are ignored, and
        with ``coerce=True`` they are removed from the table.
        """
        errors = []
        try:
            self._check_structure()
            if self.schema:
                required = [c for c, raw in self.schema.items() if _spec(raw).get('required', True)]
                self.assert_columns(required, [c for c in self.schema if c not in required])
            rows = []
            for i, values in enumerate(self._data):
                if all(_blank(v) for v in values):
                    continue
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

    @staticmethod
    def _normalize_token(value):
        return str(value).strip().casefold()

    def _vkey(self, value):
        """Return the comparison key for a cell value, honouring ``case_sensitive``."""
        text = str(value).strip()
        return text if self.case_sensitive else text.casefold()

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
        """Rename columns and keep the schema and key definitions in sync."""
        if not rename_map:
            return
        rename = lambda cols: [rename_map.get(c, c) for c in cols]
        self._columns = rename(self._columns)
        self.schema = {rename_map.get(col, col): spec for col, spec in self.schema.items()}
        self.primary_key = rename(self.primary_key)
        self.unique = [rename(spec) for spec in self.unique]

    def assert_columns(self, required_cols, optional_cols=None,
                        columns_can_grow=True, required_col_uoms=None):
        """Validate table headers against a required/optional schema.

        Header matching is always case-insensitive.

        Args:
            required_cols: Column names that must exist.
            optional_cols: Additional allowed columns (not mandatory).
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

            base_key = self._normalize_token(base_name)
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
                    if _looks_like_alias(lookup_base.get(actual_key, actual_col), opt_col):
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

    def assert_unique(self, column_name, ignore_blank=False):
        """Ensure a column has unique values and return canonical values.

        Useful for key columns such as Project, Item, Worker, Shift, etc.
        Values are compared per the table's ``case_sensitive`` setting.

        Example:
            canonical_values = table.assert_unique('Project', ignore_blank=True)
        """
        resolved = self.assert_columns([column_name])
        col = resolved.get(column_name, column_name)
        values = self.column(col)

        seen = {}
        duplicates = []
        ordered_keys = []
        for value in values:
            if _blank(value):
                if ignore_blank:
                    continue
                text = ''
            else:
                text = str(value).strip()
            key = self._vkey(text)
            if key in seen:
                duplicates.append((seen[key], text))
            else:
                seen[key] = text
                ordered_keys.append(key)

        if duplicates:
            preview = ', '.join(f"{left or '(blank)'}/{right or '(blank)'}" for left, right in duplicates[:10])
            raise ValueError(f"{self.name} '{col}' has duplicate value(s): {preview}")

        return [seen[key] for key in ordered_keys]

    def assert_unique_pairs(self, left_col, right_col):
        """Ensure each ``(left_col, right_col)`` combination appears at most once.

        A pair with an empty side is ignored, like a unique key containing NULL.

        Returns:
            Set of normalized pair keys suitable for downstream membership checks.

        Example:
            table.assert_unique_pairs('From', 'To')
        """
        resolved = self.assert_columns([left_col, right_col])
        left_name = resolved.get(left_col, left_col)
        right_name = resolved.get(right_col, right_col)

        left_values = self.column(left_name)
        right_values = self.column(right_name)

        pair_keys = []
        pair_display_by_key = {}
        pair_count = {}

        for left_raw, right_raw in zip(left_values, right_values):
            if _blank(left_raw) or _blank(right_raw):
                continue
            left_text = str(left_raw).strip()
            right_text = str(right_raw).strip()
            left_key = self._vkey(left_text)
            right_key = self._vkey(right_text)
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

    def _canonical_values(self, values, label):
        """Map each comparison key to the first-seen spelling; reject spellings that differ only by case."""
        canonical = {}
        for value in values:
            if _blank(value):
                continue
            first = canonical.setdefault(self._vkey(value), value)
            if str(first).strip() != str(value).strip():
                raise ValueError(
                    f"{self.name}: {label} are ambiguous when case is ignored: {first}, {value}"
                )
        return canonical

    def _use_canonical_spelling(self, col, canonical):
        """Rewrite cells that differ only by case to the canonical spelling (tolerant mode only)."""
        if self.case_sensitive:
            return
        idx = self._index(col)
        for row in self._data:
            if _blank(row[idx]):
                continue
            spelling = canonical.get(self._vkey(row[idx]))
            if spelling is not None and str(row[idx]).strip() != str(spelling).strip():
                row[idx] = spelling

    def assert_in(self, column_name, allowed, label=None):
        """Ensure each non-blank value of a column is one of the ``allowed`` values.

        Use it like SQL ``column IN (...)``. Values are compared per the table's
        ``case_sensitive`` setting. When case is ignored, matching cells are
        rewritten to the spelling used in ``allowed`` so later exact lookups work.

        Example:
            cost.assert_in('From', plants + dcs, label='plants or DCs')
        """
        col = self.assert_columns([column_name]).get(column_name, column_name)
        canonical = self._canonical_values(allowed, label or 'the allowed values')
        found = {self._vkey(v): str(v).strip() for v in self.column(col) if not _blank(v)}
        unknown = sorted(key for key in found if key not in canonical)
        if unknown:
            raise ValueError(
                f"{self.name} '{col}' has value(s) not found in {label or 'the allowed values'}: "
                f"{', '.join(found[key] for key in unknown[:10])}"
            )
        self._use_canonical_spelling(col, canonical)

    def assert_foreign_key(self, parent, child_col, parent_col):
        """Ensure each non-blank child value exists in the parent value set.

        Use this for foreign-key style checks between two input tables.
        Values are compared per this (child) table's ``case_sensitive`` setting.
        When case is ignored, the child column is rewritten to the parent's
        spelling (the parent table is never changed).

        Example:
            child_table.assert_foreign_key(
                parent=parent_table,
                child_col='Project',
                parent_col='Project',
            )
        """
        parent_col = parent.assert_columns([parent_col]).get(parent_col, parent_col)
        self.assert_in(child_col, parent.column(parent_col), label=f"{parent.name} '{parent_col}'")

    def assert_complete_cross_join(self, left_col, right_col, left_values,
                                   right_values, left_label=None,
                                   right_label=None):
        """Ensure the pair table contains the full Cartesian grid.

        Specifically, every combination from ``left_values x right_values`` must
        exist exactly once in ``(left_col, right_col)``. When case is ignored, the
        pair columns are rewritten to the spelling used in the supplied values.

        Example:
            table.assert_complete_cross_join(
                left_col='Source',
                right_col='Destination',
                left_values=sources,
                right_values=destinations,
            )
        """
        observed_pairs = self.assert_unique_pairs(left_col, right_col)

        left_lookup = self._canonical_values(left_values, f'{left_label or left_col} values')
        right_lookup = self._canonical_values(right_values, f'{right_label or right_col} values')

        missing = []
        for left_key, left_value in left_lookup.items():
            for right_key, right_value in right_lookup.items():
                if (left_key, right_key) not in observed_pairs:
                    missing.append(f'{str(left_value).strip()}-{str(right_value).strip()}')

        if missing:
            preview = ', '.join(missing[:10])
            left_title = left_label or left_col
            right_title = right_label or right_col
            raise ValueError(
                f"{self.name} missing {left_title}-{right_title} pair(s): {preview}"
            )

        resolved = self.assert_columns([left_col, right_col])
        self._use_canonical_spelling(resolved.get(left_col, left_col), left_lookup)
        self._use_canonical_spelling(resolved.get(right_col, right_col), right_lookup)

    def assert_columns_match_domain(self, master, master_value_col,
                              matrix_reserved_cols=None,
                              require_master_in_matrix=True,
                              require_matrix_in_master=True):
        """Validate matrix value-columns against a master key list.

        Typical use: matrix table where dynamic columns represent entities listed
        as row values in a master table key column (for example cost matrix
        columns vs facility master Location values). Column headers are compared
        to the master values per this table's ``case_sensitive`` setting;
        ``matrix_reserved_cols`` are fixed column names, matched case-insensitively.

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
        master_resolved = master.assert_columns([master_value_col])
        master_col_name = master_resolved.get(master_value_col, master_value_col)

        master_values = [
            str(value).strip()
            for value in master.column(master_col_name)
            if str(value).strip() != ''
        ]

        master_lookup = {}
        for value in master_values:
            key = self._vkey(value)
            if key in master_lookup and master_lookup[key] != value:
                raise ValueError(
                    f"Duplicate values in {master.name} '{master_col_name}': "
                    f"{master_lookup[key]}, {value}"
                )
            master_lookup[key] = value

        matrix_columns = self.columns
        reserved_keys = {self._normalize_token(col) for col in matrix_reserved_cols}

        matrix_lookup = {}
        for col in matrix_columns:
            col_text = str(col).strip()
            if self._normalize_token(col_text) in reserved_keys:
                continue
            key = self._vkey(col_text)
            if key in matrix_lookup and matrix_lookup[key] != col:
                raise ValueError(
                    f"Duplicate value columns in {self.name}: "
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

    def to_qdf(self):
        """Return qCalc's restricted qdf facade (never a raw DataFrame); safe for user calculators."""
        return qdf(self.to_dict())

    def to_df(self):
        """Return a new pandas DataFrame of the table (trusted, built-in calculators only).

        The method name is on the ``dangerous_attributes`` blocklist, so user
        calculators cannot call it; they use ``to_qdf()`` instead.
        """
        return pd.DataFrame(self.data, columns=self.columns)
