# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

from qcore import Qty

def token_cost__info():
    return {
        'title': 'AI Agent Token Cost Estimator',
        'desc': 'Estimate cost to run AI agents based on cumulative input/output tokens and API cost over multiple rounds.',
        'calculate': 'Estimate Cost',
        'schema': {
            'input_mode': {
                'help_text': (
                    'Full history mode assumes each request resends the initial context, all '
                    'previous round inputs, and all previous assistant outputs. '
                    'Prompt caching and other charges are excluded.'
                ),
                'type': 'choice',
                'choices': {
                    'full': 'Full history resent',
                    'current': 'Only current input',
                },
                'initial': 'full',
            },
        },
        'tags': 'ai agent, api, tokens',
    }


def token_cost(
    rounds = 20,
    initial_context_tokens = 4000,
    new_input_tokens_per_round = 250,
    output_tokens_per_round = 500,
    input_price_per_million = '4.0 USD',
    output_price_per_million = '20.0 USD',
    input_mode = 'full',
):
    rounds = max(1, int(rounds))
    initial_context_tokens = max(0, int(initial_context_tokens))
    new_input_tokens_per_round = max(0, int(new_input_tokens_per_round))
    output_tokens_per_round = max(0, int(output_tokens_per_round))
    input_price_per_million = Qty(input_price_per_million, 'USD')
    output_price_per_million = Qty(output_price_per_million, 'USD')

    if input_mode == 'full':
        total_input_tokens = (
            rounds * (initial_context_tokens + new_input_tokens_per_round)
            + rounds * (rounds - 1) / 2
            * (new_input_tokens_per_round + output_tokens_per_round)
        )
    else:
        total_input_tokens = rounds * (
            initial_context_tokens + new_input_tokens_per_round
        )

    total_output_tokens = rounds * output_tokens_per_round

    input_cost = total_input_tokens * input_price_per_million / 1_000_000
    output_cost = total_output_tokens * output_price_per_million / 1_000_000
    total_cost = input_cost + output_cost

    return {
        'Cumulative Input Tokens': int(total_input_tokens),
        'Cumulative Output Tokens': int(total_output_tokens),
        'Input Cost': Qty(input_cost, 'USD'),
        'Output Cost': Qty(output_cost, 'USD'),
        'Total Estimated Cost': Qty(total_cost, 'USD'),
    }
