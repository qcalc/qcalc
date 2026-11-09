# SPDX-License-Identifier: MIT
# Copyright (c) 2026
"""Relationships and grouped table orchestration for qCalc."""

from .qb_qtable import QTable, _blank, _fields, _key


__all__ = ['QRelation', 'QBase']


class QRelation:
    """A foreign-key relationship from a detail table to a master table."""

    def __init__(self, master, detail, master_key='id', detail_key=None,
                 relation_type='one-to-many', nullable=False):
        self.master = master
        self.detail = detail
        self.master_key = _fields(master_key)
        self.detail_key = _fields(detail_key or master_key)
        self.relation_type = relation_type
        self.nullable = nullable
        if len(self.master_key) != len(self.detail_key):
            raise ValueError('Master and detail keys must have the same number of columns')
        if relation_type not in ('one-to-one', 'one-to-many', 'many-to-one'):
            raise ValueError('Use a junction table for many-to-many relationships')

    def to_dict(self):
        """Return a dictionary representation of the relationship."""
        return {'master': self.master, 'detail': self.detail,
                'master_key': self.master_key[0] if len(self.master_key) == 1 else self.master_key,
                'detail_key': self.detail_key[0] if len(self.detail_key) == 1 else self.detail_key,
                'relation_type': self.relation_type, 'nullable': self.nullable}

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
        for i, row in enumerate(master, 1):
            vals = [row[c] for c in self.master_key]
            if any(_blank(v) for v in vals):
                raise ValueError(f'{master.name}: blank master key at row {i}')
            k = _key(vals)
            if k in parent:
                raise ValueError(f'{master.name}: duplicate master key {k!r}')
            parent.add(k)
        seen = set()
        for i, row in enumerate(detail):
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
        return [row for row in self[detail]
                if _key([row[c] for c in relation.detail_key]) == _key(wanted)]

    def to_dict(self):
        """Serialize tables (with schema and keys) and relationships."""
        return {'tables': {name: table.to_dict(full=True) for name, table in self._tables.items()},
                'relations': [r.to_dict() for r in self._relations]}
