# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

class DotDict(dict):

    def __init__(self, data=None, **kwargs):
        super().__init__()

        if data:
            for key, value in data.items():
                self[key] = self._convert(value)

        for key, value in kwargs.items():
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
