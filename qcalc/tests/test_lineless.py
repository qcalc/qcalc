# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

import qsett
from django.test import TestCase
from django.template import Context, Template


class LinelessNodeTest(TestCase):
    def test_lineless_ex_tag(self):
        template = Template('''
{% load qfilter %}
{% lineless_ex %}
<p>Test paragraph.</p>



<pre>
def example():
pass


</pre>

<textarea>
Test textarea.

</textarea>
{% endlineless_ex %}
        ''')

        context = Context({})
        rendered = template.render(context)

        # Check that blank lines are removed outside <pre> and <textarea>
        self.assertNotIn('\n\n\n\n', rendered)
        self.assertIn('<pre>\ndef example():\npass\n\n\n', rendered)
        self.assertIn('<textarea>\nTest textarea.\n\n</textarea>', rendered)

    def test_lineless_tag(self):
        template = Template('''
{% load qfilter %}
{% lineless %}
<p>Test paragraph.</p>



<pre>
def example():
pass


</pre>

<textarea>
Test textarea.

</textarea>
{% endlineless %}
        ''')

        context = Context({})
        rendered = template.render(context)

        # Check that blank lines are removed outside <pre> and <textarea>
        self.assertNotIn('\n\n\n\n', rendered)
        self.assertIn('<pre>\ndef example():\npass\n', rendered)
        self.assertIn('<textarea>\nTest textarea.\n</textarea>', rendered)
