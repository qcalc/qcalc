# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _read(rel_path: str) -> str:
    return (ROOT / rel_path).read_text(encoding="utf-8")


def _assert_math_assets_are_in_content_block(template_text: str) -> None:
    # Regression guard:
    # KaTeX assets must stay in the swapped help fragment body so HTMX
    # insertions re-execute math rendering for markdown-produced math/tex tags.
    assert "{% block extra_header_script %}" in template_text

    header_start = template_text.index("{% block extra_header_script %}")
    header_end = template_text.index("{% endblock %}", header_start)
    header_block = template_text[header_start:header_end]

    assert "katex.min.css" not in header_block
    assert "katex.min.js" not in header_block
    assert "mathtex-script-type.min.js" not in header_block

    md_idx = template_text.index('<div class="md-content">')
    css_idx = template_text.index("katex.min.css")
    js_idx = template_text.index("katex.min.js")
    mathtex_idx = template_text.index("mathtex-script-type.min.js")

    assert md_idx < css_idx < js_idx < mathtex_idx


def test_calculator_help_partial_keeps_math_assets_in_swapped_content_block():
    template = _read("calc/templates/calculator-help-partial.html")
    _assert_math_assets_are_in_content_block(template)


def test_page_help_partial_keeps_math_assets_in_swapped_content_block():
    template = _read("qsite/templates/page-help-partial.html")
    _assert_math_assets_are_in_content_block(template)
