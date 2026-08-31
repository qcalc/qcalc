# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

class DotDict(dict):

    def __init__(self, *args, **kwargs):
        super().__init__()

        for key, value in dict(*args, **kwargs).items():
            self[key] = self._convert(value)

    @classmethod
    def _convert(cls, value):
        if isinstance(value, dict) and not isinstance(value, DotDict):
            return cls(value)
        return value

    def __getattr__(self, key):
        if key not in self:
            self[key] = DotDict()
        return self[key]

    def __setattr__(self, key, value):
        self[key] = self._convert(value)

    def key(self, key):
        if key not in self:
            self[key] = DotDict()
        return self[key]
