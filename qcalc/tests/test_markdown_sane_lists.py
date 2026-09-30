# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

from qutil.mod_md import md2html


def test_ordered_list_numbering_survives_math_block_splits():
    md = """
1. Work volume:

$$V_{work}=L\\times W\\times T$$

2. Dry material volume:

$$V_{dry}=V_{work}\\times f_{dry}$$

3. Mix parts total:

$$P=c+s+g$$
""".strip()

    html = md2html(md)

    # mdx_math creates block-level script tags that split list blocks;
    # sane_lists must preserve explicit numbering via start="N".
    assert '<ol start="2">' in html
    assert '<ol start="3">' in html


def test_inline_math_dollar_delimiters_render_to_mathtex_script():
    md = "Velocity is $v=d/t$ for uniform motion."

    html = md2html(md)

    assert '<script type="math/tex">v=d/t</script>' in html


def test_display_math_double_dollar_delimiters_render_to_display_mathtex_script():
    md = """
Work volume:

$$V_{work}=L\\times W\\times T$$
""".strip()

    html = md2html(md)

    assert '<script type="math/tex; mode=display">V_{work}=L\\times W\\times T</script>' in html
