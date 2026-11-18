# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

class DotDict(dict):
    """A dictionary whose entries can also be accessed as attributes.

    Use ``row.name`` as an alternative to ``row['name']``. Nested dictionaries
    are converted automatically, including dictionaries inside lists and tuples.
    This helper is also available as ``dd``.

    With ``readonly=True``, reading a missing attribute or calling ``key()`` for
    a missing entry raises an error instead of creating an empty entry.

    Example:
        ``DotDict({'name': 'Asha'}).name`` returns ``'Asha'``.
    """

    def __init__(self, *args, readonly=False, **kwargs):
        super().__init__()
        object.__setattr__(self, "_readonly", readonly)

        for key, value in dict(*args, **kwargs).items():
            self[key] = self._convert(value, readonly=readonly)

    @classmethod
    def _convert(cls, value, readonly=False):
        if isinstance(value, dict) and not isinstance(value, DotDict):
            return cls(value, readonly=readonly)
        if isinstance(value, list):
            return [cls._convert(item, readonly=readonly) for item in value]
        if isinstance(value, tuple):
            return tuple(cls._convert(item, readonly=readonly) for item in value)
        return value

    def __getattr__(self, key):
        # it will create if key is missing
        # to allow assignment to nonexistent key
        if key not in self:
            if self._readonly:
                raise AttributeError(key)
            self[key] = DotDict(readonly=self._readonly)
        return self[key]

    def __setattr__(self, key, value):
        if key.startswith("_"):
            object.__setattr__(self, key, value)
            return
        self[key] = self._convert(value, readonly=self._readonly)

    def key(self, key):
        """Access an entry whose key is not suitable for dot notation.

        A missing key creates an empty ``DotDict`` unless this object is readonly,
        in which case ``KeyError`` is raised.
        """
        # supports keys that can't use dot notation
        if key not in self:
            if self._readonly:
                raise KeyError(key)
            self[key] = DotDict(readonly=self._readonly)
        return self[key]

def dd_list(items, readonly=False):
    """Return a new list with each dictionary in ``items`` converted to ``DotDict``.

    Non-dictionary items are left unchanged. With ``readonly=True``, reading a
    missing attribute from a converted item raises an error instead of creating
    an empty entry.
    """
    return [
        DotDict(item, readonly=readonly) if isinstance(item, dict) else item
        for item in items
    ]