# SPDX-License-Identifier: MIT
# Copyright (c) 2026
"""Small in-memory tables and relationships for qCalc.

QTable stores ordinary Python lists/dicts in qtbl shape.  qdf remains the
separate, restricted pandas computation facade.
"""

from .qb_qdf import qkeymap, qdf
from .qb_table_validate import (require_columns, require_unique_values, require_unique_pairs,
                                require_values_subset, require_complete_pair_grid,
                                validate_value_columns_against_master)
from copy import deepcopy


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
        if isinstance(data, dict):
            if 'columns' not in data or 'data' not in data:
                raise TypeError("A table dictionary must contain 'columns' and 'data'")
            if columns is not None:
                raise ValueError('Do not pass columns when data is a qtbl.')
            schema = data.get('schema') if schema is None else schema
            primary_key = data.get('primary_key') if primary_key is None else primary_key
            unique = data.get('unique') if unique is None else unique
            columns, data = data['columns'], data['data']
        elif data and isinstance(data, (list, tuple)) and isinstance(data[0], dict):
            if columns is None:
                columns = list(dict.fromkeys(k for row in data for k in row))
            data = [[row.get(col) for col in columns] for row in data]

        self.name = name or 'table'
        self.schema = deepcopy(schema or {})
        self.primary_key = _fields(primary_key) if primary_key is not None else []
        self.unique = _unique_specs(unique)
        self._columns = list(columns or self.schema.keys())
        self._data = deepcopy(list(data or []))
        self._check_structure()
        if validate:
            self.validate(raise_exception=True)

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

    def require_columns(self, required_cols, optional_cols=None,
                        case_sensitive=False, columns_can_grow=True,
                        required_col_uoms=None):
        """Require specific columns to be present, optionally allowing additional columns.

        Retains qCalc's existing case/spacing, strict-input and UOM rules.
        """
        payload = self.to_dict()
        old_columns = list(payload["columns"])
        result = require_columns(
            payload, self.name, required_cols, optional_cols,
            case_sensitive=case_sensitive,
            columns_can_grow=columns_can_grow,
            required_col_uoms=required_col_uoms,
        )
        self._sync_validation_columns(payload, old_columns)
        return result

    def require_unique(self, column_name, case_sensitive=False, ignore_blank=False):
        """Require unique values in one column; return canonical values."""
        payload = self.to_dict()
        old_columns = list(payload["columns"])
        result = require_unique_values(
            payload, self.name, column_name,
            case_sensitive=case_sensitive, ignore_blank=ignore_blank,
        )
        self._sync_validation_columns(payload, old_columns)
        return result

    def require_unique_pairs(self, left_col, right_col, case_sensitive=False):
        """Require unique pairs and return their normalized pair-key set."""
        payload = self.to_dict()
        old_columns = list(payload["columns"])
        result = require_unique_pairs(
            payload, self.name, left_col, right_col,
            case_sensitive=case_sensitive,
        )
        self._sync_validation_columns(payload, old_columns)
        return result

    def require_values_subset(self, parent, child_col, parent_col,
                              case_sensitive=False):
        """Require this table's values to exist in a parent table."""
        child_payload, parent_payload = self.to_dict(), parent.to_dict()
        child_columns = list(child_payload["columns"])
        parent_columns = list(parent_payload["columns"])
        result = require_values_subset(
            child_payload, self.name, child_col,
            parent_payload, parent.name, parent_col,
            case_sensitive=case_sensitive,
        )
        self._sync_validation_columns(child_payload, child_columns)
        parent._sync_validation_columns(parent_payload, parent_columns)
        return result

    def require_complete_pair_grid(self, left_col, right_col, left_values,
                                   right_values, left_label=None,
                                   right_label=None, case_sensitive=False):
        """Require every combination of left_values × right_values exactly once."""
        payload = self.to_dict()
        old_columns = list(payload["columns"])
        result = require_complete_pair_grid(
            payload, self.name, left_col, right_col,
            left_values, right_values,
            left_label=left_label, right_label=right_label,
            case_sensitive=case_sensitive,
        )
        self._sync_validation_columns(payload, old_columns)
        return result

    def require_value_columns(self, master, master_value_col,
                              matrix_reserved_cols=None,
                              require_master_in_matrix=True,
                              require_matrix_in_master=True,
                              case_sensitive=False):
        """Validate dynamic matrix headers against values in a master table."""
        matrix_payload, master_payload = self.to_dict(), master.to_dict()
        matrix_columns = list(matrix_payload["columns"])
        master_columns = list(master_payload["columns"])
        result = validate_value_columns_against_master(
            matrix_payload, self.name,
            master_payload, master.name, master_value_col,
            matrix_reserved_cols=matrix_reserved_cols,
            require_master_in_matrix=require_master_in_matrix,
            require_matrix_in_master=require_matrix_in_master,
            case_sensitive=case_sensitive,
        )
        self._sync_validation_columns(matrix_payload, matrix_columns)
        master._sync_validation_columns(master_payload, master_columns)
        return result

    # Explicit legacy-name aliases ease migration from mod_table_validate.
    require_unique_values = require_unique
    validate_value_columns_against_master = require_value_columns

    def df(self):
        """Return qCalc's restricted qdf facade (never a raw DataFrame)."""
        return qdf(self.to_dict())


class QRelation:
    """A foreign-key relationship from a detail table to a master table."""

    def __init__(self, master, detail, master_key='id', detail_key=None,
                 relation_type='one-to-many', on_delete='restrict', nullable=False):
        self.master = master
        self.detail = detail
        self.master_key = _fields(master_key)
        self.detail_key = _fields(detail_key or master_key)
        self.relation_type = relation_type
        self.on_delete = on_delete
        self.nullable = nullable
        if len(self.master_key) != len(self.detail_key):
            raise ValueError('Master and detail keys must have the same number of columns')
        if relation_type not in ('one-to-one', 'one-to-many', 'many-to-one'):
            raise ValueError('Use a junction table for many-to-many relationships')
        if on_delete not in ('restrict', 'cascade', 'set_null'):
            raise ValueError("on_delete must be 'restrict', 'cascade', or 'set_null'")

    def to_dict(self):
        """Return a dictionary representation of the relationship."""
        return {'master': self.master, 'detail': self.detail,
                'master_key': self.master_key[0] if len(self.master_key) == 1 else self.master_key,
                'detail_key': self.detail_key[0] if len(self.detail_key) == 1 else self.detail_key,
                'relation_type': self.relation_type, 'on_delete': self.on_delete,
                'nullable': self.nullable}

    def validate(self, db):
        """Validate the relationship against the given database, checking for key consistency and referential integrity."""
        master, detail = db[self.master], db[self.detail]
        for col in self.master_key:
            if col not in master.columns:
                raise ValueError(f'{master.name}: relationship column not found: {col}')
        for col in self.detail_key:
            if col not in detail.columns:
                raise ValueError(f'{detail.name}: relationship column not found: {col}')
        parent = set()
        for i, row in enumerate(master.records(skip_blank=False, skip_header=False, strip=False), 1):
            vals = [row[c] for c in self.master_key]
            if any(_blank(v) for v in vals):
                raise ValueError(f'{master.name}: blank master key at row {i}')
            k = _key(vals)
            if k in parent:
                raise ValueError(f'{master.name}: duplicate master key {k!r}')
            parent.add(k)
        seen = set()
        for i, row in enumerate(detail.records(skip_blank=False, skip_header=False, strip=False)):
            vals = [row[c] for c in self.detail_key]
            if all(_blank(v) for v in vals) and self.nullable:
                continue
            if any(_blank(v) for v in vals):
                raise ValueError(f'{detail.name}: incomplete/blank foreign key at row {i + 1}')
            k = _key(vals)
            if k not in parent:
                raise ValueError(f'{detail.name}: foreign key {k!r} at row {i + 1} not found in {master.name}')
            if self.relation_type == 'one-to-one':
                if k in seen:
                    raise ValueError(f'{detail.name}: duplicate one-to-one reference {k!r}')
                seen.add(k)


class QBase:
    """Registry and integrity coordinator for a small group of QTables."""

    def __init__(self, tables=None, relations=None):
        self._tables = {}
        self._relations = []
        for name, table in (tables or {}).items():
            self.register(name, table)
        for relation in relations or []:
            self.relate(**(relation.to_dict() if isinstance(relation, QRelation) else relation))

    def __getitem__(self, name):
        return self._tables[name]

    def __contains__(self, name):
        return name in self._tables

    def __iter__(self):
        return iter(self._tables.values())

    @property
    def tables(self):
        """Return a dictionary of all registered tables keyed by their names."""
        return dict(self._tables)

    @property
    def relations(self):
        """Return a list of all defined relationships."""
        return list(self._relations)

    @property
    def table_names(self):
        """Return a list of all registered table names."""
        return list(self._tables)

    def table(self, name):
        """Return the table registered under the given name."""
        return self[name]

    def register(self, name, table):
        """Register a new table under the given name."""
        if name in self._tables:
            raise ValueError(f'Table already registered: {name}')
        if not isinstance(table, QTable):
            table = QTable(table, name=name)
        table.name = name
        self._tables[name] = table
        return table

    def unregister(self, name):
        """Unregister the table with the given name, ensuring it has no relationships."""
        if any(name in (r.master, r.detail) for r in self._relations):
            raise ValueError(f'{name}: remove its relationships first')
        return self._tables.pop(name)

    def relate(self, master, detail, **kwargs):
        """Define a relationship between the master and detail tables."""
        if master not in self._tables or detail not in self._tables:
            raise KeyError('Register both tables before defining their relationship')
        relation = QRelation(master, detail, **kwargs)
        self._relations.append(relation)
        return relation

    def validate(self, raise_exception=False):
        """Validate all tables and relationships in the database."""
        errors = {}
        for name, table in self._tables.items():
            result = table.validate()
            if not result['valid']:
                errors[name] = result['errors']
        for i, relation in enumerate(self._relations, 1):
            try:
                relation.validate(self)
            except Exception as exc:
                errors[f'relation_{i}'] = [str(exc)]
        result = {'valid': not errors, 'errors': errors}
        if errors and raise_exception:
            raise ValueError(errors)
        return result

    def master_detail(self, master, detail, master_key):
        """Return detail records matching one master key (or composite key) in the master table."""
        relation = next((r for r in self._relations
                         if r.master == master and r.detail == detail), None)
        if relation is None:
            raise KeyError(f'No relationship: {master} -> {detail}')
        wanted = _fields(master_key) if len(relation.master_key) > 1 else [master_key]
        return [row for row in self[detail].records(skip_blank=False, skip_header=False, strip=False)
                if _key([row[c] for c in relation.detail_key]) == _key(wanted)]

    def delete(self, table_name, key):
        """Delete a master row, applying on-delete rules through every level of related tables."""
        table = self[table_name]
        record = table.get(key)
        if record is None:
            return False
        snapshots = {name: t.data for name, t in self._tables.items()}
        try:
            self._apply_delete_rules(table_name, record, set())
            table.delete(key)
        except Exception:
            for name, data in snapshots.items():
                self._tables[name]._data = data
            raise
        return True

    def _apply_delete_rules(self, table_name, record, visited):
        """Restrict/cascade/set-null the rows that reference ``record`` in related tables."""
        for i, relation in enumerate(self._relations):
            if relation.master != table_name:
                continue
            master_key = _key([record[c] for c in relation.master_key])
            if (i, master_key) in visited:
                continue
            visited.add((i, master_key))
            children = self[relation.detail]
            rows = children.records(skip_blank=False, skip_header=False, strip=False)
            matches = [r for r in rows if _key([r[c] for c in relation.detail_key]) == master_key]
            if not matches:
                continue
            if relation.on_delete == 'restrict':
                raise ValueError(f'Cannot delete {table_name} {master_key!r}: referenced by {relation.detail}')
            if relation.on_delete == 'cascade':
                for match in matches:
                    self._apply_delete_rules(relation.detail, match, visited)
                rows = children.records(skip_blank=False, skip_header=False, strip=False)
                children._commit([r for r in rows
                                  if _key([r[c] for c in relation.detail_key]) != master_key])
            else:
                if not relation.nullable:
                    raise ValueError(f'{relation.detail}: set_null requires nullable=True')
                for row in rows:
                    if _key([row[c] for c in relation.detail_key]) == master_key:
                        row.update({c: None for c in relation.detail_key})
                children._commit(rows)

    def to_dict(self):
        """Serialize tables (with schema and keys) and relationships."""
        return {'tables': {name: table.to_dict(full=True) for name, table in self._tables.items()},
                'relations': [r.to_dict() for r in self._relations]}
