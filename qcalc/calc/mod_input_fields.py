# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

FLD_GENDER_CHOICE = {
    'type': 'choice',
    'initial': 'F',
    'choices': {'M': 'Male', 'F': 'Female'}
}

FLD_SHOW_CHOICE = {
    'type': 'radio',
    'initial': 'both',
    'choices': {'table': 'Table', 'chart': 'Chart', 'both': 'Both'}
}

FLD_VARIATION_TARGET = {
    'label': 'Vary By',
    'type': 'choice',
    'choices': {'p': 'Parameters', 'v': 'Variables'},
    'help_text': "Select what to vary: Parameters of a function (e.g. function(param1=5, param2='10 ft') "
                 "or Variables of an expression (e.g. 3*x + 5*y), here x and y are variables. "
                 "You can add variables inside a function too e.g. function(param1=5, param2='x ft') "
                 "Here x is an added variable, which you can then use as a variation target.",
}

FLD_RESULT_CELLS = {'help_text': (
    'Optional table cells to use as results when the expression returns tables, separated by comma. '
    'Each is Table[: Row[: Column]], e.g. Income Statement: Net Income, Ratios: *margin*. '
    'Table/Row/Column accept names, row numbers, ranges (1-5), * wildcards and ~ exclusion. '
    'Other scalar results are kept alongside the selected cells, and table_columns/table_units/'
    'chart_columns/chart_units then filter the combined columns; the other text columns of a row '
    '(e.g. an acronym) also work there as names'
)}


class ResultCellsError(Exception):
    """Raised for result_cells problems that must not be swallowed as a failed trial."""


FLD_INPUTS = {
    'help_text': (
        'Use Distribution to choose the sampling shape.<br>'
        '<b>normal:</b> Param 1 = <b>mean</b>, Param 2 = <b>stdev</b>, Param 3 = blank<br>'
        '<b>uniform:</b> Param 1 = <b>low</b>, Param 2 = <b>high</b>, Param 3 = blank<br>'
        '<b>triangular:</b> Param 1 = <b>low</b>, Param 2 = <b>high</b>, Param 3 = <b>mode</b><br>'
        '<b>lognormal:</b> Param 1 = <b>mu</b>, Param 2 = <b>sigma</b>, Param 3 = blank<br>'
    ),
}
