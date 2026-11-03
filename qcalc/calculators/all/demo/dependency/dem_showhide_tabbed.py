# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

from qcore.mod_anno import *


def demo_showhide_tabbed__info():
    return {
        'title': 'Tabbed Show/Hide Demo',
        'interactive': True,
        'layout': 'tb',
        'input_columns': 2,
        'input_blocks': [
            {
                'column': 1,
                'fields': [
                    'hide_group1_tabs',
                ],
            },
            {
                'column': 1,
                'tabs': [
                    {
                        'title': 'Main',
                        'fields': [
                            'mode',
                            'base_value',
                        ],
                    },
                    {
                        'title': 'Details',
                        'fields': [
                            'detail_a',
                            'detail_b',
                            'detail_note',
                        ],
                    },
                ],
            },
            {
                'column': 2,
                'fields': [
                    'hide_group2_tabs',
                ],
            },
            {
                'column': 2,
                'tabs': [
                    {
                        'title': 'Summary',
                        'fields': [
                            'multiplier',
                            'summary_label',
                            'summary_text',
                        ],
                    },
                    {
                        'title': 'Notes',
                        'fields': [
                            'internal_note',
                        ],
                    },
                ],
            },
        ],
        'showhide': {
            'hide_group1_tabs': {
                'fields': ['mode', 'base_value', 'detail_a', 'detail_b', 'detail_note'],
                'callback': '!@',
            },
            'hide_group2_tabs': {
                'fields': ['multiplier', 'summary_label', 'summary_text', 'internal_note'],
                'callback': '!@',
            },
        },
        'schema': {
            'hide_group1_tabs': {
                'type': 'checkbox',
                'help_text': 'Hide the first group when checked.',
            },
            'hide_group2_tabs': {
                'type': 'checkbox',
                'help_text': 'Hide the second group when checked.',
            },
            'mode': {
                'type': 'choice',
                'choices': ['compact', 'expanded'],
                'help_text': 'Switch between a compact or expanded view.',
            },
            'base_value': {
                'type': 'float',
                'help_text': 'Base number used by the demo calculation.',
            },
            'detail_a': {
                'type': 'qtext',
                'help_text': 'First detail field shown only when details are enabled.',
            },
            'detail_b': {
                'type': 'integer',
                'help_text': 'Second detail field shown only when details are enabled.',
            },
            'detail_note': {
                'type': 'qtexta',
                'help_text': 'Freeform note in the details tab.',
            },
            'multiplier': {
                'type': 'float',
                'help_text': 'Hidden when the mode is compact.',
            },
            'summary_label': {
                'type': 'qtext',
                'help_text': 'Label for the computed summary.',
            },
            'summary_text': {
                'type': 'qtext',
                'help_text': 'Secondary summary text hidden in compact mode.',
            },
            'internal_note': {
                'type': 'qtexta',
                'help_text': 'A notes field placed in a separate tab.',
            },
        },
    }


def demo_showhide_tabbed(
    mode='expanded',
    base_value: float = 10.0,
    detail_a='Alpha',
    detail_b: int = 2,
    detail_note='Visible when details are enabled',
    multiplier: float = 1.5,
    summary_label='Result',
    summary_text='Shown when the mode is expanded',
    internal_note='Tabbed layout with cross-tab visibility controls',
    hide_group1_tabs=False,
    hide_group2_tabs=False,
):
    total = base_value * multiplier
    return {
        'current_mode': mode,
        'summary_label_out': summary_label,
        'summary': f'{summary_label}: {total}',
        'summary_text_out': summary_text,
        'detail_a_out': detail_a,
        'detail_b_out': detail_b,
        'detail_note_out': detail_note,
        'internal_note_out': internal_note,
    }
