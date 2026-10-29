# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

"""Single source of truth for the keys of a calculator's ``info`` (``<name>__info()`` / qfunc_info.json).

Kinds:
- public:   set by the calculator author
- legacy:   still honored, superseded by ``input_blocks`` / ``output_blocks``
- internal: set by qcalc itself

Columns:
- override: ``q1141_read_func_meta`` copies it from ``__info()`` / qfunc_info.json into the request ``info``
            (``images`` is merged separately, ``api`` and ``fargs`` are read by their own code paths, and a few
            internal keys are overridable for compatibility)

The info generator (mod_code_info) produces every public key except ``api``, in registry order. ``api`` opts a
calculator into the public API, so a draft must not set it silently.

The metadata validation of user-authored calculators (mod_mycal_validation) owns the value schemas. It accepts the
public keys and ``inp1`` / ``out1``, never the internal keys; tests/test_info_keys.py enforces that every public key
has a schema.
"""

from typing import NamedTuple

__all__ = [
    'INFO_KEYS', 'PUBLIC_KEYS', 'LEGACY_KEYS', 'INTERNAL_KEYS', 'ALL_INFO_KEYS', 'INFO_OVERRIDE_KEYS',
]


class InfoKey(NamedTuple):
    kind: str
    override: bool


def _key(kind, override=True):
    return InfoKey(kind, override)


INFO_KEYS = {
    # public
    'title': _key('public'),
    'desc': _key('public'),
    'calculate': _key('public'),
    'layout': _key('public'),
    'interactive': _key('public'),
    'input_columns': _key('public'),
    'output_columns': _key('public'),
    'input_blocks': _key('public'),
    'output_blocks': _key('public'),
    'showhide': _key('public'),
    'anyof': _key('public'),
    'autofill': _key('public'),
    'related': _key('public'),
    'images': _key('public', override=False),
    'onsubmit': _key('public'),
    'script': _key('public'),
    'inserts': _key('public'),
    'step2': _key('public'),
    'single_instance': _key('public'),
    'single_instance_key': _key('public'),
    'provides_data': _key('public'),
    'consumes_data': _key('public'),
    'schema': _key('public'),
    'kins': _key('public'),
    'tags': _key('public'),
    'proper': _key('public'),
    'remember': _key('public'),
    'table_out_all': _key('public'),
    'api': _key('public', override=False),  # read by qapi (mod_api_core)
    'fargs': _key('public', override=False),  # read by mod_mfunc (COMBINE_FINF)
    # legacy
    'row': _key('legacy'),
    'col': _key('legacy'),
    'inp1': _key('legacy'),
    'out1': _key('legacy'),
    # internal
    'name': _key('internal', override=False),
    'help': _key('internal', override=False),
    'clean': _key('internal', override=False),
    'template': _key('internal', override=False),
    'qsel2': _key('internal', override=False),
    'qlist': _key('internal', override=False),
    'table_in': _key('internal', override=False),
    'table_out': _key('internal', override=False),
    'xpr': _key('internal'),
    'url': _key('internal'),
    'loop': _key('internal'),
    'cost': _key('internal'),
}

PUBLIC_KEYS = tuple(key for key, spec in INFO_KEYS.items() if spec.kind == 'public' and key != 'api')
LEGACY_KEYS = frozenset(key for key, spec in INFO_KEYS.items() if spec.kind == 'legacy')
INTERNAL_KEYS = frozenset(key for key, spec in INFO_KEYS.items() if spec.kind == 'internal')
ALL_INFO_KEYS = frozenset(INFO_KEYS)
INFO_OVERRIDE_KEYS = tuple(key for key, spec in INFO_KEYS.items() if spec.override)
