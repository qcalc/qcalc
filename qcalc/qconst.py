# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

# COMBINE_FINF = {dict,   dict,       dict,      dict,       dict,    list,      dict,    value}
COMBINE_FINF = {'schema', 'autofill', 'related', 'showhide', 'anyof', 'fargs', 'script'}
KNOWN_METAS = ['__info', '__input', '__modify', '__command', '__help']
QCALC_LAYOUTS = ['l2r', 'l2r2', 'lr', 'lr2', 't2b', 't2b2', 'tb', 'tb2']
CODE_TAB = 4

# Field/component suffix tokens used in generated names/ids.
# Keep as full token fragments so migrations can be granular.
TOK_UOM = '_uom'
TOK_PART = '_part'
TOK_PART_UOM = '_part_uom'
TOK_ROW = '_row'
TOK_COL = '_col'
TOK_TABLE_UPDATE = '_table_update'
TOK_TABLE_RESIZE = '_table_resize'
TOK_TABLE_ED = '_table_ed'
TOK_ID_PREFIX = 'id_'
TOK_FIELD_SEP = '_'

# Token usage map (2026-09-25 analysis):
# - These TOK_* values are backend/frontend contracts. If any token here changes,
#   update corresponding JS tokens/selectors in calc and qsite scripts together.
# - Python TOK_* -> corresponding JS token(s):
#   TOK_UOM          -> TOK_UOM, QCALC_TOK_UOM
#   TOK_PART         -> TOK_PART
#   TOK_PART_UOM     -> no dedicated JS const; represented by TOK_PART + TOK_UOM
#   TOK_ROW          -> TOK_ROW
#   TOK_COL          -> TOK_COL
#   TOK_TABLE_UPDATE -> TOK_TABLE_UPDATE, QCALC_TOK_TABLE_UPDATE
#   TOK_TABLE_RESIZE -> TOK_TABLE_RESIZE
#   TOK_TABLE_ED     -> TOK_TABLE_ED
#   TOK_ID_PREFIX    -> TOK_ID_PREFIX, QCALC_TOK_ID_PREFIX
#   TOK_FIELD_SEP    -> TOK_FIELD_SEP, QCALC_TOK_FIELD_SEP
# - JS-only tokens are intentionally kept local in frontend files (not imported
#   by Python), e.g. TOK_FORM_PREFIX, TOK_OUTPUT_PREFIX, TOK_EXTRA_PREFIX,
#   TOK_SCRIPT_DATA_*_SUFFIX, and qsite-scoped QCALC_TOK_* UI constants.

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
