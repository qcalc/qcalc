# SPDX-License-Identifier: MIT
# Regression tests for printable-flat wiring (runtime flag and Tabulator handling)

import os
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]


def read(path):
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()


def test_source_template_contains_runtime_flag():
    """Ensure the source template injects the runtime flag for printable-flat mode."""
    p = BASE / 'calc' / 'templates' / 'insert-calculator-form-core.html'
    assert p.exists(), f"Source template not found: {p}"
    s = read(p)
    assert 'window.__qcalc_tabulator_print_all' in s, "Runtime flag script missing from source template"
    assert "input.doc.info.print_mode == 'flat'" in s or 'tabulator_print_all' in s, (
        "Condition to enable runtime flag not found in source template"
    )


def test_generated_template_contains_runtime_flag():
    """Ensure the generated template (gulp output) contains the flag (regenerated files should include it)."""
    p = BASE / 'calc' / 'templates' / 'gen-calculator-core.html'
    assert p.exists(), f"Generated template not found: {p}"
    s = read(p)
    assert 'window.__qcalc_tabulator_print_all' in s, "Runtime flag script missing from generated template"


def test_tabulator_initializers_respect_flag():
    """Ensure both Tabulator initializers look for the runtime flag and disable pagination in flat mode."""
    in_js = BASE / 'calc' / 'static' / 'calc' / 'js' / 'tabulator-in.js'
    out_js = BASE / 'calc' / 'static' / 'calc' / 'js' / 'tabulator-out.js'
    assert in_js.exists(), f"tabulator-in.js not found: {in_js}"
    assert out_js.exists(), f"tabulator-out.js not found: {out_js}"
    sin = read(in_js)
    sout = read(out_js)
    # they should reference the runtime flag
    assert 'window.__qcalc_tabulator_print_all' in sin, "tabulator-in.js does not read runtime flag"
    assert 'window.__qcalc_tabulator_print_all' in sout, "tabulator-out.js does not read runtime flag"
    # they should disable pagination when the flag is set (look for pagination=false or tabOpts.pagination = false)
    assert 'pagination = false' in sin or 'tabOpts.pagination = false' in sin, (
        "tabulator-in.js does not disable pagination for print-all"
    )
    assert 'pagination = false' in sout or 'tabOpts.pagination = false' in sout, (
        "tabulator-out.js does not disable pagination for print-all"
    )
