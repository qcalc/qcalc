# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

import re
from bs4 import BeautifulSoup
from django.templatetags.static import static
from django.utils.safestring import mark_safe
import requests
from qconst import delimiter_help_text
from qutil import nzs, to_df, demo_url, md2html
from qcore.mod_anno import *
from calc.mod_result import df2unit_normalized


def file_reader__info():
    return {
        'title': 'File Reader',
    }


def file_reader(
    upload_file: qfile,
):
    if upload_file:
        return upload_file.file_name, upload_file.file_type
    else:
        raise Exception(f'Error (FR): A valid File or URL is not found')


def md_reader__info():
    return {
        'title': 'Mark Down File Reader',
        'showhide': {
            'mode': {
                'fields': ['upload_markdown', 'md_url', 'markdown_text'],
                'callback': 'mode_reader_fields',
            },
        },
        # without these inserts, the math rendering for $..$ and $$...$$ will not work correctly
        # however other markdown features will still work correctly without this insert
        'inserts': {
            'out_bottom':
                f"""
                <link href="{static('vendor/katex/0.11.1/katex.min.css')}" rel="stylesheet" type="text/css">
                <script src="{static('vendor/katex/0.11.1/katex.min.js')}"></script>
                <script src="{static('vendor/katex/0.11.1/contrib/mathtex-script-type.min.js')}"></script>
                <script>
                (function() {{
                    if (window.__qcalcMdReaderMathInit) {{
                        return;
                    }}
                    window.__qcalcMdReaderMathInit = true;

                    function renderMathScripts(root) {{
                        if (!window.katex || !root) {{
                            return;
                        }}

                        root.querySelectorAll('script[type^="math/tex"]').forEach(function(script) {{
                            var tex = script.textContent || '';
                            var display = script.type.indexOf('mode=display') !== -1;
                            var node = document.createElement(display ? 'div' : 'span');
                            if (display) {{
                                node.className = 'equation';
                            }}
                            katex.render(tex, node, {{displayMode: display, throwOnError: false}});
                            script.replaceWith(node);
                        }});
                    }}

                    function renderAllMarkdownMath() {{
                        document.querySelectorAll('.md-content').forEach(renderMathScripts);
                    }}

                    document.addEventListener('DOMContentLoaded', renderAllMarkdownMath);
                    document.body.addEventListener('htmx:afterSwap', renderAllMarkdownMath);
                }})();
                </script>
                """
        },
        'script': """
        function mode_reader_fields(v){
            return [v === 'File', v === 'URL', v === 'Text'];
        }
        """,
        'schema': {
            'mode': {
                'type': 'choice',
                'choices': {'File': 'File', 'URL': 'URL', 'Text': 'Text'},
                'initial': 'URL',
                'help_text': 'Choose whether to read Markdown from a file, URL, or text input.',
            },
            'markdown_text': {
                'attrs': {
                    'data-lang': 'markdown',
                },
            },
        },
    }


def md_reader(upload_markdown: qfile = None, md_url: qurl = demo_url('demo.md'),
              markdown_text: qcode = 
"""
# Example Markdown content with LaTeX math equations.

## This is a sample Markdown content.

$$(a + b)^2 = a^2 + 2ab + b^2$$

$a$ and $b$ are variables in the equation.

- Example list item
- Another list item

*Italic text*

**Bold text**

```python
# This is a sample Python code block.
print("Hello, World!")
```

""", 
              mode='URL'):
    mode = str(mode).strip().upper()
    if mode == 'URL':
        if not md_url:
            raise Exception(f'Error (MR): A valid Markdown URL is not found')
        response = requests.get(md_url, timeout=(3, 15))
        md_text = response.text
    elif mode == 'TEXT':
        if nzs(markdown_text) == '':
            raise Exception(f'Error (MR): A valid Markdown Text is not found')
        md_text = markdown_text
    elif mode == 'FILE':
        if upload_markdown is None:
            raise Exception(f'Error (MR): A valid Markdown File is not found')
        md_text = upload_markdown.text()
    else:
        raise Exception(f"Error (MR): mode must be one of 'File', 'URL', or 'Text'")
    return qhtml(f'<div class="md-content">{md2html(md_text)}</div>')


def csv_reader__info():
    return {
        'title': 'CSV Reader',
        'showhide': {
            'mode': {
                'fields': ['upload_csv', 'csv_url'],
                'callback': 'csv_reader_mode_showhide',
            },
        },
        'schema': {
            'mode': {
                'type': 'choice',
                'choices': {'File': 'File', 'URL': 'URL'},
                'initial': 'URL',
                'help_text': 'Choose whether to read the CSV from an uploaded file or from a URL.',
            },
            'quoting': {
                'type': 'choice', 'choices': {
                    '0': 'Minimal', '1': 'All', '2': 'Non-Numeric', '3': 'None', '9': 'Remove Anyway'
                }
            },
            'delimiter': {
                'help_text': delimiter_help_text,
            }
        },
        'script': """
        function csv_reader_mode_showhide(v){
            return [v === 'File', v === 'URL'];
        }
        """,
    }


def csv_reader(upload_csv: qfile = None, csv_url: qurl = demo_url('closing.csv'),
               quoting='1', delimiter: qchar = ',', transfer: str = '', mode='URL'):
    mode = str(mode).strip().upper()
    if mode == 'URL':
        if not csv_url:
            raise Exception(f'Error (CR): A valid CSV URL is not found')
        df = to_df(csv_url, delimiter, quoting)
    elif mode == 'FILE':
        if upload_csv is None:
            raise Exception(f'Error (CR): A valid CSV File is not found')
        df = to_df(upload_csv.txt_buf(), delimiter, quoting)
    else:
        raise Exception(f"Error (CR): mode must be either 'File' or 'URL'")

    return {'table': df}


def csv_editor__info():
    return {
        'title': 'CSV Editor',
        'schema': {
            'quoting': {
                'type': 'choice', 'choices': {
                    '0': 'Minimal', '1': 'All', '2': 'Non-Numeric', '3': 'None', '9': 'Remove Anyway'
                }
            },
            'delimiter': {
                'help_text': delimiter_help_text,
            },
            'normalize_units': {
                'type': 'checkbox',
                'help_text': 'Convert compatible quantity columns to numeric values and append units to column titles.',
            },
        },
        # Prefix calculator arguments with @ so this script can call the
        # calculator function correctly when reused from another calculator.
        # The prefix is resolved by flatten_finfo() before the script is rendered.
        'script':
            """
$(document).ready(function() {
    load_button_id = QCALC_TOK_ID_PREFIX + getCid() + '_@load';
    $("#"+load_button_id).on("click", function() {
        cid = getCidOf($(this));
        updateExtra(cid, {
            "cmd":"load", "from": "@upload_csv", "to": "@csv_table",
            "delimiter":"@delimiter", "quoting": "@quoting", "url": "@csv_url"
            });
        qcalc_FullFormSubmit(cid);
    });
});
            """
    }


def csv_editor(upload_csv: qfile = None, csv_url: qurl = demo_url('emp.csv'),
               quoting='1', delimiter: qchar = ',', load: 'btn:0' = 'Load CSV',
               csv_table: qtable = pd.DataFrame(columns=[]),
               normalize_units: bool = False):
    if len(csv_table) != 0:
        df = csv_table
    elif csv_url:
        df = to_df(csv_url, delimiter, quoting)
    elif upload_csv:
        df = to_df(upload_csv.txt_buf(), delimiter, quoting)
    else:
        raise Exception(f'Error (CR): A valid CSV File or URL is not found')

    if normalize_units:
        df = df2unit_normalized(df)

    return df


def remove_tags(html):
    # parse html content
    soup = BeautifulSoup(html, "html.parser")

    for data in soup(['style', 'script']):
        # Remove tags
        data.decompose()

    # return data by retrieving the tag content
    return ' '.join(soup.stripped_strings)


def word_count(text: str):
    words = re.findall(r'\w+', text)
    cnt = len(words)
    return cnt, words


def html_reader__info():
    return {
        'title': 'HTML Reader',
        'showhide': {
            'mode': {
                'fields': ['upload_html', 'html_url', 'html_text'],
                'callback': 'mode_reader_fields',
            },
        },
        'script': """
        function mode_reader_fields(v){
            return [v === 'File', v === 'URL', v === 'Text'];
        }
        """,
        'schema': {
            'mode': {
                'type': 'choice',
                'choices': {'File': 'File', 'URL': 'URL', 'Text': 'Text'},
                'initial': 'URL',
                'help_text': 'Choose whether to read HTML from a URL or from text input.',
            },
            'html_text': {
                'attrs': {
                    'data-lang': 'html',
                },
            },
        },
    }


def html_reader(upload_html: qfile = None, html_url: qurl = demo_url('demo.html'),
                html_text: qcode = 
"""
<h1>Hello World</h1>
<h2>Subheading</h2>
<p>This is a paragraph of text under the subheading.</p>
<ul>
    <li>First item</li>
    <li>Second item</li>
    <li>Third item</li>
</ul>
"""
    , convert_to_text: bool = False, mode='URL'):
    # https://www.geeksforgeeks.org/remove-all-style-scripts-and-html-tags-using-beautifulsoup/
    mode = str(mode).strip().upper()
    if mode == 'URL':
        if not html_url:
            raise Exception(f'Error (HR): A valid HTML URL is not found')
        response = requests.get(html_url, timeout=(3, 15))
        html = response.text
    elif mode == 'TEXT':
        if nzs(html_text) == '':
            raise Exception(f'Error (HR): A valid HTML Text is not found')
        html = html_text
    elif mode == 'FILE':
        if upload_html is None:
            raise Exception(f'Error (HR): A valid HTML File is not found')
        html = upload_html.text()
    else:
        raise Exception(f"Error (HR): mode must be one of 'File', 'URL', or 'Text'")
    if convert_to_text:
        html = remove_tags(html)
    return qhtml(html)


if __name__ == '__main__':
    import os

    directory = 'S:/DATA/test_files/'
    for filename in os.listdir(directory):
        f = os.path.join(directory, filename)
        file_format = ''  # analyze_file(f)
        print(f'The file {f} is of type: {file_format}')
