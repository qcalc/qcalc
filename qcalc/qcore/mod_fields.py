# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha


def ai_prompt_field(
    label='AI Prompt',
    placeholder='Describe behavior, constraints, edge cases, and expected output...',
    rows=10,
    max_chars=12000,
    monospace=True,
    token_hint=True,
    help_inline=None,
):
    classes = ['texta', 'w-100']
    if monospace:
        classes.append('text-monospace')

    if help_inline is None:
        help_inline = (
            'Use clear steps, constraints, and examples. '
            'AI-generated responses may contain errors; review them with '
            'appropriate caution.'
        )
    if token_hint:
        approx_tokens = max_chars // 4
        help_inline = f'Max {max_chars} chars (~{approx_tokens} tokens). {help_inline}'

    return {
        'type': 'qtexta',
        'label': label,
        'max_length': max_chars,
        'help_inline': help_inline,
        'attrs': {
            'class': ' '.join(classes),
            'rows': rows,
            'placeholder': placeholder,
            'maxlength': str(max_chars),
            'data-token-estimate': 'chars_div_4',
        },
    }


def br(html: str):
    return f'<div class="w-100">{html}</div>'
