import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")

import pytest

from calc.mod_qcals_security import safe_execute

UNSAFE_PROBES = [
    ("builtins exposure", "__builtins__"),
    ("module import through os", "__import__('os').environ.get('PATH')"),
    ("module import via builtins", "__import__('builtins').eval('__import__(\'os\').environ')"),
    ("file read via open", "open(r'./README.md').read()[:32]"),
    ("file read via pathlib", "__import__('pathlib').Path('./README.md').read_text()[:32]"),
    ("subprocess execution", "__import__('subprocess').run(['echo', 'LOCAL_ONLY_TEST'], capture_output=True, text=True).stdout"),
    ("class traversal", "().__class__.__mro__[1].__subclasses__()[:3]"),
    ("class bases traversal", "().__class__.__bases__[0].__subclasses__()[:3]"),
    ("mro lookup escape", "[].__class__.__mro__[1].__subclasses__()[:3]"),
    ("global lookup", "globals()"),
    ("local lookup", "locals()"),
    ("attribute escape", "().__class__.__dict__"),
    ("getattr-based import", "getattr(__import__('builtins'), 'eval')('__import__(\'os\').environ')"),
    ("eval call", "eval('1 + 1')"),
    ("exec call", "exec('x = 5')"),
    ("compile call", "compile('1+1', '<string>', 'eval')"),
]


@pytest.mark.parametrize("label, probe", UNSAFE_PROBES)
def test_unsafe_probes_are_rejected(label, probe):
    """These probes are intended to confirm the sandbox blocks access to runtime internals.

    A safe implementation should reject them with an exception. If they succeed, the
    evaluator has a security boundary bug.
    """
    with pytest.raises(Exception):
        safe_execute(probe)


MANUAL_MYCAL_PROBES = [
    "__import__('os').environ.get('PATH')",
    "__import__('builtins').eval('__import__(\'os\').environ')",
    "open(r'./README.md').read()[:32]",
    "__import__('pathlib').Path('./README.md').read_text()[:32]",
    "().__class__.__mro__[1].__subclasses__()[:5]",
    "().__class__.__bases__[0].__subclasses__()[:5]",
    "[].__class__.__mro__[1].__subclasses__()[:5]",
    "getattr(__import__('builtins'), 'eval')('__import__(\'os\').environ')",
    "__import__('subprocess').run(['echo', 'LOCAL_ONLY_TEST'], capture_output=True, text=True).stdout",
]


@pytest.mark.skip(reason="Manual-only local probe: do not run against real backend state or production data.")
@pytest.mark.parametrize("probe", MANUAL_MYCAL_PROBES)
def test_manual_mcal_probe_strings_are_only_for_isolated_local_audit(probe):
    """These are example payloads to run manually against a disposable evaluator instance.

    They intentionally exercise known sandbox-bypass patterns and should never be used
    against live systems, shared state, or real backend resources.
    """
    assert isinstance(probe, str)
