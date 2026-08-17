# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

# COMBINE_FINF = {dict,   dict,       dict,      dict,       dict,    list,      dict,    value}
COMBINE_FINF = {'schema', 'autofill', 'related', 'showhide', 'anyof', 'fargs', 'script'}
KNOWN_METAS = ['__info', '__input', '__modify', '__command', '__help']
CODE_TAB = 4

# Local trusted deployments may enable legacy unrestricted user-calculator imports.
ALLOW_UNSAFE_USER_CALCULATOR_IMPORTS = False
MARKDOWN_EXTENSIONS = extensions=['extra', 'fenced_code', 'tables', 'mdx_math']

# catalog properties
name_separator = '-'
separator_display = ' > '
admin_name = 'admin'
demo_name = 'demo'
personal_name = 'personal'
