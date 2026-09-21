# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

# COMBINE_FINF = {dict,   dict,       dict,      dict,       dict,    list,      dict,    value}
COMBINE_FINF = {'schema', 'autofill', 'related', 'showhide', 'anyof', 'fargs', 'script'}
KNOWN_METAS = ['__info', '__input', '__modify', '__command', '__help']
QCALC_LAYOUTS = ['l2r', 'l2r2', 'lr', 'lr2', 't2b', 't2b2', 'tb', 'tb2']
CODE_TAB = 4

# IO table limits
TABLE_MAX_COLS = 125  # Maximum number of columns
TABLE_MAX_CELLS = 50000  # Maximum number of celss

# Expression builder limit
SCALAR_LENGTH = 512  # Maximum length of a scalar value or string for expression builder to process

# Local trusted deployments may enable legacy unrestricted user-calculator imports.
ALLOW_UNSAFE_USER_CALCULATOR_IMPORTS = False

# catalog properties
name_separator = '-'
separator_display = ' > '
admin_name = 'admin'
demo_name = 'demo'
personal_name = 'personal'

amount_help_text = 'Enter an amount to be converted\nor a simple expression (e.g. 92/3+15)\nto calculate the amount before conversion.'
delimiter_help_text = "A single delimiter character (e.g. ',' or ';'), or one of:\n'tab' or '\\t'; 'space' or '\\s'; 'whitespace' or '\\ws' (one or more spaces)."
