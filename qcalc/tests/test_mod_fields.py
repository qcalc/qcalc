# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha
# Tests generated with AI assistance. Reviewed and validated by the author.

from qcore.mod_fields import ai_prompt_field


def test_ai_prompt_field_uses_custom_help_text_with_token_hint():
    field = ai_prompt_field(
        max_chars=4000,
        help_text='Custom guidance.',
    )

    assert field['help_text'] == (
        'Max 4000 chars (~1000 tokens). Custom guidance.'
    )


def test_ai_prompt_field_preserves_custom_help_text_without_token_hint():
    field = ai_prompt_field(
        token_hint=False,
        help_text='Custom guidance.',
    )

    assert field['help_text'] == 'Custom guidance.'
