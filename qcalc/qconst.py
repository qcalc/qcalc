# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

import re

# COMBINE_FINF = {dict,   dict,       dict,      dict,       dict,    list,      dict,    value}
COMBINE_FINF = {'schema', 'autofill', 'related', 'showhide', 'anyof', 'fargs', 'script'}
KNOWN_METAS = ['__info', '__input', '__modify', '__command', '__help']
QCALC_LAYOUTS = ['lr', 'tb']
CODE_TAB = 4
CHART_WIDTH = 800
CHART_HEIGHT = 800

# Marker tokens used in nested function/dict metadata and script placeholders.
DICT_CLASS_FUNC = '@'
DICT_CLASS_PLAIN = '#'
DICT_KEY_SEP = '--'
SCRIPT_RUNTIME_VAR = '@'
DICT_KEY_LABEL_SEP = ': '

# Field/component suffix tokens used in generated names/ids.
# Keep as full token fragments so migrations can be granular.
TOK_UOM = '_uom'
TOK_PART = '_part'
TOK_PART_UOM = '_part_uom'
TOK_ID_PREFIX = 'id_'

# Separator between cid and field name in generated DOM ids (e.g. id_<cid>_<field>).
TOK_FIELD_SEP = '_'
# Separator between a list field root and its numeric index suffix (e.g. value__2).
# Also used for multi widget fields e.g. qtc, qtc2, qty
TOK_INDEX_SEP = '__'  # was _ before changed @ 27.09.26
# Separator between a base field and composite control suffixes (row/col/table_update/table_resize/table_ed).
TOK_COMPOSITE_SEP = '_'
# Unit of measure separator in tables
TBL_UOM_SEP = '|'  # ref. debt_invest() for output, production_mix_profit() for input

_row_suffix = 'row'
_col_suffix = 'col'
_table_update_suffix = 'table_update'
_table_resize_suffix = 'table_resize'
_table_ed_suffix = 'table_ed'

TOK_ROW = f'{TOK_COMPOSITE_SEP}{_row_suffix}'
TOK_COL = f'{TOK_COMPOSITE_SEP}{_col_suffix}'
TOK_TABLE_UPDATE = f'{TOK_COMPOSITE_SEP}{_table_update_suffix}'
TOK_TABLE_RESIZE = f'{TOK_COMPOSITE_SEP}{_table_resize_suffix}'
TOK_TABLE_ED = f'{TOK_COMPOSITE_SEP}{_table_ed_suffix}'

TOK_RESULT_SUFFIX = '__r'

# Compiled because this fixed pattern is reused in text normalization helpers.
TOK_RESULT_SUFFIX_PATTERN = re.compile(r'__r[a-z]?')
TOK_LIST_INDEX_PATTERN = rf'{re.escape(TOK_INDEX_SEP)}\d+$'

_token_part_with_optional_index = rf'(?:{re.escape(TOK_INDEX_SEP)}\d+)?{re.escape(TOK_PART)}'
FIELD_ROOT_SUFFIX_PATTERN = re.compile(
    rf'{_token_part_with_optional_index}(?:{re.escape(TOK_UOM)})?$|{re.escape(TOK_UOM)}$'
)

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
#   TOK_INDEX_SEP    -> TOK_INDEX_SEP (qlist index suffix separator)
#   TOK_COMPOSITE_SEP-> TOK_COMPOSITE_SEP (showhide composite controls)
# - JS-only tokens are intentionally kept local in frontend files (not imported
#   by Python), e.g. TOK_FORM_PREFIX, TOK_OUTPUT_PREFIX, TOK_EXTRA_PREFIX,
#   TOK_SCRIPT_DATA_*_SUFFIX, and qsite-scoped QCALC_TOK_* UI constants.

# IO table limits
TABLE_MAX_COLS = 125  # Maximum number of columns
TABLE_MAX_CELLS = 50000  # Maximum number of celss
TABLE_MAX_CELLS_XPR = 1000 # Maximum number of cells that allows an expression to be built

# Expression builder limit
SCALAR_LENGTH = 512  # Maximum length of a scalar value or string for expression builder to process

# Relative value syntax used by compare(), e.g. 5%, -5%, 5(%), 5(+), 2(x)
RELATIVE_VALUE_PATTERN = re.compile(
    r'(?P<sign>[+-]?)(?P<number>(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?)'
    r'\s*(?:(?P<percent>%)|\(\s*(?P<op>[-+*/xX%])\s*\))'
)

# Keep as string because some call sites may compile with their own flags.
# NUMBER_PATTERN = r"[+-]?[0-9]+(\.[0-9]*)?([eE][+-]?[0-9]+)?"
NUMBER_PATTERN = r"[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?" # .5, -.5 accepted

# Row selector token: single row index or inclusive range (e.g. 2 or 2-5).
ROW_INDEX_PATTERN = re.compile(r'^\d+(\s*-\s*\d+)?$')

# Compiled because this fixed validator is reused by calculator call parsing.
FUNC_CALL_PATTERN = re.compile(r'^[a-zA-Z_]\w*\(.*\)$')

# Compiled because percent parsing runs frequently in result-table scans.
PERCENT_PATTERN = re.compile(r'^\s*([+-]?\d+(?:\.\d*)?|[+-]?\.\d+)\s*%\s*$')

# Keep as string template because callers inject dynamic word alternations.
WORD_LIST_PATTERN = r'\b(?:%s)\b'

# Keep as string because callers compile with runtime flags (e.g. IGNORECASE).
# Matches:
#   parameter='1.3 kW'
#   parameter="1.3 kW"
#   parameter=0.8
#   parameter=-12
#   parameter=1.25
PARAMETER_PATTERN = r"""
    (?P<name>[A-Za-z_]\w*)
    (\s*=\s*)
    (?:
        (?P<quote>['"])
        (?P<quantity>
            [+-]?(?:\d+(?:\.\d*)?|\.\d+)
            \s+
            [^'"]+
        )
        (?P=quote)
      |
        (?P<number>
            [+-]?(?:\d+(?:\.\d*)?|\.\d+)
        )
    )
"""

# Compiled because timezone parsing uses a fixed validator pattern.
TIMEZONE_PATTERN = re.compile(r'^(?:UTC)?([+-]\d{2}:?\d{2})(?:\s*(.+))?$')

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
