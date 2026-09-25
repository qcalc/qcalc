from __future__ import annotations

from typing import Any

from calc.templatetags.qfilter import field_root

LAYOUTS = {'lr', 'tb'}
SIDE_SPECS = (
    {
        'side': 'input',
        'blocks_key': 'input_blocks',
        'columns_key': 'input_columns',
        'legacy_group_key': 'inp1',
        'single_class': 'section-input1',
        'col1_class': 'section-input1',
        'col2_class': 'section-input2',
    },
    {
        'side': 'output',
        'blocks_key': 'output_blocks',
        'columns_key': 'output_columns',
        'legacy_group_key': 'out1',
        'single_class': 'section-output1',
        'col1_class': 'section-output1',
        'col2_class': 'section-output2',
    },
)


def has_dynamic_layout(info: dict[str, Any] | None) -> bool:
    if not isinstance(info, dict):
        return False
    return bool(info.get('input_blocks') or info.get('output_blocks'))


def build_layout_plan(info, input_form=None, output_form=None):
    info = info if isinstance(info, dict) else {}
    layout = info.get('layout', 'lr')
    plan = {
        'layout': layout if layout in LAYOUTS else 'lr',
        **{
            spec['side']: _build_side_plan(info, form, spec)
            for spec, form in zip(SIDE_SPECS, (input_form, output_form), strict=True)
        }
    }
    return plan


def _build_side_plan(
    side_info: dict[str, Any],
    form,
    spec: dict[str, str],
):
    field_names = _build_field_names(form)
    blocks_def = side_info.get(spec['blocks_key']) or []

    if blocks_def:
        blocks = _normalize_blocks(spec['side'], blocks_def)
    else:
        blocks = _legacy_blocks(spec['side'], side_info.get(spec['legacy_group_key']), field_names)

    columns = side_info.get(spec['columns_key'])
    if columns not in [1, 2]:
        columns = _infer_columns(blocks)

    blocks = [block for block in blocks if block.get('fields') or block.get('tabs')]
    column1 = [block for block in blocks if block.get('column', 1) == 1]
    column2 = [block for block in blocks if block.get('column', 1) == 2]

    if columns == 1:
        column1 = blocks
        column2 = []

    return {
        'side': spec['side'],
        'columns': columns,
        'single_class': spec['single_class'],
        'col1_class': spec['col1_class'],
        'col2_class': spec['col2_class'],
        'blocks': blocks,
        'column1': column1,
        'column2': column2,
        'has_tabs': any(block.get('kind') == 'tabs' for block in blocks),
    }


def _build_field_names(form):
    field_names = []
    seen = set()

    def add_name(name):
        if name not in seen:
            field_names.append(name)
            seen.add(name)

    if form is None:
        return field_names
    try:
        fields = getattr(form, 'fields', {})
        for name in fields:
            add_name(field_root(name))
    except Exception:
        try:
            for field in form:
                add_name(field_root(field.name))
        except Exception:
            pass
    return field_names


def _legacy_blocks(side_name, group_1, field_names):
    if not group_1:
        return [
            {
                'id': f'{side_name}-block-0',
                'column': 1,
                'kind': 'fields',
                'fields': field_names,
            }
        ]

    group_1_set = set(group_1)
    group_2_fields = [name for name in field_names if name not in group_1_set]

    if not group_2_fields:
        return [
            {
                'id': f'{side_name}-block-0',
                'column': 1,
                'kind': 'fields',
                'fields': group_1,
            }
        ]

    return [
        {
            'id': f'{side_name}-block-0',
            'column': 1,
            'kind': 'fields',
            'fields': group_1,
        },
        {
            'id': f'{side_name}-block-1',
            'column': 2,
            'kind': 'fields',
            'fields': group_2_fields,
        },
    ]


def _normalize_blocks(side_name, blocks_def):
    blocks = []
    for block_index, block_def in enumerate(blocks_def):
        if not isinstance(block_def, dict):
            continue

        kind_value = block_def.get('kind')
        if kind_value is None:
            kind_value = 'tabs' if block_def.get('tabs') else 'fields'
        kind = str(kind_value).strip().lower()
        column = block_def.get('column', 1)
        try:
            column = int(column)
        except Exception:
            column = 1
        if column not in [1, 2]:
            column = 1

        block_id = block_def.get('id') or f'{side_name}-block-{block_index}'
        if kind == 'tabs':
            tabs = []
            tab_defs = block_def.get('tabs', [])
            for tab_index, tab_def in enumerate(tab_defs):
                if not isinstance(tab_def, dict):
                    continue
                tab_title = tab_def.get('title', tab_def.get('label', f'Tab {tab_index + 1}'))
                tab_fields = list(tab_def.get('fields', []))
                if not tab_fields:
                    continue
                tabs.append({
                    'id': tab_def.get('id') or f'{block_id}-tab-{tab_index}',
                    'title': tab_title,
                    'fields': tab_fields,
                })
            if tabs:
                blocks.append({
                    'id': block_id,
                    'column': column,
                    'kind': 'tabs',
                    'tabs': tabs,
                })
            continue

        fields = list(block_def.get('fields', []))
        if fields:
            blocks.append({
                'id': block_id,
                'column': column,
                'kind': 'fields',
                'fields': fields,
            })
    return blocks


def _infer_columns(blocks):
    max_column = 1
    for block in blocks:
        try:
            max_column = max(max_column, int(block.get('column', 1)))
        except Exception:
            continue
    return 2 if max_column > 1 else 1
