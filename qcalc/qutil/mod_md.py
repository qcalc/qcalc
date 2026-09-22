# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

import markdown
from bs4 import BeautifulSoup

# 'toc' adds slug ids to headings (e.g. #1-getting-started) so in-doc TOC/bookmark links resolve
MARKDOWN_EXTENSIONS = extensions = ['extra', 'fenced_code', 'tables', 'mdx_math', 'toc']
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
"""

def md2html(md_text:str):
    html = markdown.markdown(
        md_text,
        extensions=MARKDOWN_EXTENSIONS,
        extension_configs=MARKDOWN_CONFIGS,
        output_format='html',
    )
    return html


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
