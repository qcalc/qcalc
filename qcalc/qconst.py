# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

# COMBINE_FINF = {dict,   dict,       dict,      dict,       dict,    list,      dict,    value}
COMBINE_FINF = {'schema', 'autofill', 'related', 'showhide', 'anyof', 'fargs', 'script'}
KNOWN_METAS = ['__info', '__input', '__modify', '__command', '__help']
CODE_TAB = 4

# Local trusted deployments may enable legacy unrestricted user-calculator imports.
ALLOW_UNSAFE_USER_CALCULATOR_IMPORTS = False
# 'toc' adds slug ids to headings (e.g. #1-getting-started) so in-doc TOC/bookmark links resolve
MARKDOWN_EXTENSIONS = extensions=['extra', 'fenced_code', 'tables', 'mdx_math', 'toc']
"""
extra:  footnotes, abbreviations, and definition lists
fenced_code: multiline code blocks by wrapping them in three backticks (```) instead of forcing a four-space indentation.
tables: standard data grids using traditional pipe and dash separators (| and -).
mdx_math: Intercepts math syntax (like $ .. $ and $$ .. $$) so LaTeX math equations can be prepared for browser rendering.
toc: to generate a dynamic, hyperlinked Table of Contents.
"""
# catalog properties
name_separator = '-'
separator_display = ' > '
admin_name = 'admin'
demo_name = 'demo'
personal_name = 'personal'
