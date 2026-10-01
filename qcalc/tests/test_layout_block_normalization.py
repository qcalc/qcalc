# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

import qsett

qsett.init()

from calc.mod_layout_dynamic import build_layout_plan
from calc.views import _normalize_layout_blocks


class _FakeForm:
    def __init__(self, names):
        self.fields = {name: object() for name in names}


def test_dynamic_layout_keeps_empty_tab_specs_empty_not_all_fields():
    blocks = [
        {
            'column': 1,
            'tabs': [
                {'title': 'Present', 'fields': ['Summary']},
                {'title': 'Missing', 'fields': ['Stability Summary']},
            ],
        }
    ]
    spec_source = ['summary__r', 'period_plan__r']
    info = {
        'layout': 'tb',
        'output_columns': 1,
        'output_blocks': _normalize_layout_blocks(blocks, spec_source),
    }
    output_form = _FakeForm(spec_source)

    plan = build_layout_plan(info, input_form=None, output_form=output_form)

    tabs = plan['output']['blocks'][0]['tabs']
    assert [tab['title'] for tab in tabs] == ['Present']
    assert tabs[0]['fields'] == ['summary__r']


def test_dynamic_layout_keeps_empty_field_specs_empty_not_all_fields():
    blocks = [
        {'column': 1, 'fields': ['Summary']},
        {'column': 1, 'fields': ['No Match']},
    ]
    spec_source = ['summary__r']
    info = {
        'layout': 'tb',
        'output_columns': 1,
        'output_blocks': _normalize_layout_blocks(blocks, spec_source),
    }
    output_form = _FakeForm(spec_source)

    plan = build_layout_plan(info, input_form=None, output_form=output_form)

    assert len(plan['output']['blocks']) == 1
    assert plan['output']['blocks'][0]['fields'] == ['summary__r']

