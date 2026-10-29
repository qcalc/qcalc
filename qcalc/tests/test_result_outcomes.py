# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha
# Tests generated with AI assistance. Reviewed and validated by the author.

from types import SimpleNamespace

import qsett

qsett.init()

from calc.views_result import q1145_result_to_form_schema
from qcore import qchat


def test_qchat_renders_as_scrollable_html_output():
    request = SimpleNamespace(
        pref={},
        recall=False,
        remember=False,
        success=True,
        var_owner='',
        variant='',
        token='',
        cmd='',
        ojson_d4f={},
        json_doc={'info': {'out1': '', 'output_blocks': []}},
    )

    q1145_result_to_form_schema(
        request,
        func_id='ai_chat',
        cid='chat1',
        result={'Conversation': qchat('<p>Hello</p>')},
        proper_dict={},
    )

    assert request.ojson_schema[0]['type'] == 'html'
    rendered = str(request.ojson_schema[0]['initial'])
    assert 'class="elem-wrapper chat-wrap"' in rendered
    assert 'class="qchat"' in rendered
    assert 'class="fullscreen-square"' in rendered
    assert 'toggleFullscreen' in rendered
    assert 'role="log"' in rendered
    assert '<p>Hello</p>' in rendered
    assert 'scrollHeight' in rendered
