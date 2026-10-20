import qsett

qsett.init()

from qutil import escape_markdown, md2html


def test_escape_markdown_preserves_code_quotes_and_escapes_raw_html():
    markdown = """Here is an example:

```python
value = '<script>alert("unsafe")</script>'
```
"""

    rendered = md2html(escape_markdown(markdown))

    assert '&#x27;' not in rendered
    assert '&amp;lt;' not in rendered
    assert "value = '&lt;script&gt;alert(&quot;unsafe&quot;)&lt;/script&gt;'" in rendered
    assert '<script>alert' not in rendered


def test_escape_markdown_preserves_inline_code_without_allowing_raw_html():
    markdown = "Use `Qty('7 ft')` instead of <script>alert('unsafe')</script>."

    rendered = md2html(escape_markdown(markdown))

    assert "<code>Qty('7 ft')</code>" in rendered
    assert '<script>alert' not in rendered
