# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

import markdown
from bs4 import BeautifulSoup
from django.templatetags.static import static


def md_math_script():
    # without these inserts, the math rendering for $..$ and $$...$$ will not work correctly
    # however other Markdown features will still work correctly without this insert
    return f"""
<link href="{static('vendor/katex/0.11.1/katex.min.css')}" rel="stylesheet" type="text/css">
<script src="{static('vendor/katex/0.11.1/katex.min.js')}"></script>
<script src="{static('vendor/katex/0.11.1/contrib/mathtex-script-type.min.js')}"></script>
<script>
(function() {{
    if (window.__qcalcMdReaderMathInit) {{
        return;
    }}
    window.__qcalcMdReaderMathInit = true;

    function renderMathScripts(root) {{
        if (!window.katex || !root) {{
            return;
        }}

        root.querySelectorAll('script[type^="math/tex"]').forEach(function(script) {{
            var tex = script.textContent || '';
            var display = script.type.indexOf('mode=display') !== -1;
            var node = document.createElement(display ? 'div' : 'span');
            if (display) {{
                node.className = 'equation';
            }}
            katex.render(tex, node, {{displayMode: display, throwOnError: false}});
            script.replaceWith(node);
        }});
    }}

    function renderAllMarkdownMath() {{
        document.querySelectorAll('.md-content').forEach(renderMathScripts);
    }}

    document.addEventListener('DOMContentLoaded', renderAllMarkdownMath);
    document.body.addEventListener('htmx:afterSwap', renderAllMarkdownMath);
}})();
</script>
"""


# 'toc' adds slug ids to headings (e.g. #1-getting-started) so in-doc TOC/bookmark links resolve
# 'sane_lists' preserves explicit ordered-list numbering (start=...) when blocks (like math)
# split list items into separate <ol> sections during parsing.
MARKDOWN_EXTENSIONS = extensions = ['extra', 'fenced_code', 'tables', 'mdx_math', 'toc', 'sane_lists']
MARKDOWN_CONFIGS = {
    'mdx_math': {
        'enable_dollar_delimiter': True,
    }
}
"""
extra:  footnotes, abbreviations, and definition lists
fenced_code: multiline code blocks by wrapping them in three backticks (```) instead of forcing a four-space indentation.
tables: standard data grids using traditional pipe and dash separators (| and -).
mdx_math: Intercepts math syntax (like $ .. $ and $$ .. $$) so LaTeX math equations can be prepared for browser rendering.
toc: to generate a dynamic, hyperlinked Table of Contents.
sane_lists: keeps explicit ordered-list numbering instead of restarting at 1 for each split block.
"""


def md2html(md_text: str, wrap=False):
    """Render Markdown to HTML using qcalc's standard extension set."""
    html = markdown.markdown(
        md_text,
        extensions=MARKDOWN_EXTENSIONS,
        extension_configs=MARKDOWN_CONFIGS,
        output_format='html',
    )
    return html if not wrap else f'<div class="md-content">{html}</div>'


def wrap_md_images(html: str):
    soup = BeautifulSoup(html, 'html.parser')

    for image in soup.find_all('img', src=True):
        if image.find_parent(class_='qmd-img-wrapper'):
            continue
        wrapper = soup.new_tag('span')
        wrapper['class'] = 'qmd-img-wrapper'
        image.insert_before(wrapper)
        wrapper.append(image.extract())

    return str(soup)
