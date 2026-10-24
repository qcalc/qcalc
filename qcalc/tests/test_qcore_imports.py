import ast
import subprocess
import sys
from pathlib import Path

import pytest

QCORE_DIR = Path(__file__).resolve().parent.parent / 'qcore'
MODULES = sorted(p.stem for p in QCORE_DIR.glob('*.py') if p.stem != '__init__')


def test_qcore_modules_do_not_import_from_their_own_package():
    # `from qcore import X` inside qcore only works through __init__.py import order (a cycle);
    # import from the defining submodule instead, e.g. `from .mod_anno import qchat`.
    offenders = []
    for path in QCORE_DIR.glob('*.py'):
        if path.name == '__init__.py':
            continue
        for node in ast.walk(ast.parse(path.read_text(encoding='utf-8'))):
            if isinstance(node, ast.ImportFrom) and node.level == 0 and node.module == 'qcore':
                offenders.append(f'{path.name}:{node.lineno}')
    assert not offenders, f'package-level self imports: {offenders}'


@pytest.mark.parametrize('module', MODULES)
def test_qcore_submodule_imports_standalone(module):
    # fresh interpreter per module: importing any submodule first must not depend on import order
    code = (
        "import os; os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.dev'); "
        f"import qcore.{module}"
    )
    result = subprocess.run([sys.executable, '-c', code], cwd=QCORE_DIR.parent,
                            capture_output=True, text=True, timeout=120)
    assert result.returncode == 0, result.stderr[-1500:]
