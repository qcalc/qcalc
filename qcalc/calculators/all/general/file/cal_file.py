# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

import re
from bs4 import BeautifulSoup
from qconst import delimiter_help_text
from qutil import nzs, csv2df, demo_url, md2html, md_math_script, action_script, fetch_url, code2html
from qcore.mod_anno import *
from calc.mod_result import df2normalized


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
        'inserts': {
            'out_bottom': md_math_script(),
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


# the default qcode must be left adjusted
def md_reader(upload_markdown: qfile = None, md_url: qurl = demo_url('demo.md'),
              markdown_text: qcode = """
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
""", mode='URL'):
    mode = str(mode).strip().upper()
    if mode == 'URL':
        if not md_url:
            raise Exception(f'Error (MR): A valid Markdown URL is not found')
        response = fetch_url(md_url, check_status=False)
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
    return qhtml(md2html(md_text, wrap=True))


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
        df = csv2df(csv_url, delimiter, quoting)
    elif mode == 'FILE':
        if upload_csv is None:
            raise Exception(f'Error (CR): A valid CSV File is not found')
        df = csv2df(upload_csv.txt_buf(), delimiter, quoting)
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
        'script': action_script(
            button_name='@load',
            cmd='load',
            field_refs={
                'from': 'upload_csv',
                'to': 'csv_table',
                'delimiter': 'delimiter',
                'quoting': 'quoting',
                'url': 'csv_url',
            },
        ),
    }


def csv_editor(upload_csv: qfile = None, csv_url: qurl = demo_url('emp.csv'),
               quoting='1', delimiter: qchar = ',', load: 'btn:0' = 'Load CSV',
               csv_table: qtable = pd.DataFrame(columns=[]),
               normalize_units: bool = False):
    if len(csv_table) != 0:
        df = csv_table
    elif csv_url:
        df = csv2df(csv_url, delimiter, quoting)
    elif upload_csv:
        df = csv2df(upload_csv.txt_buf(), delimiter, quoting)
    else:
        raise Exception(f'Error (CR): A valid CSV File or URL is not found')

    if normalize_units:
        df = df2normalized(df)

    return df


def remove_tags(html):
    # parse html content
    soup = BeautifulSoup(html, "html.parser")

    for data in soup(['style', 'script']):
        # Remove tags
        data.decompose()

    # return data by retrieving the tag content
    return ' '.join(soup.stripped_strings)


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


# the default qcode must be left adjusted
def html_reader(upload_html: qfile = None, html_url: qurl = demo_url('demo.html'),
                html_text: qcode = """
<h1>Hello World</h1>
<h2>Subheading</h2>
<p>This is a paragraph of text under the subheading.</p>
<ul>
    <li>First item</li>
    <li>Second item</li>
    <li>Third item</li>
</ul>
""", convert_to_text: bool = False, mode='URL'):
    # https://www.geeksforgeeks.org/remove-all-style-scripts-and-html-tags-using-beautifulsoup/
    mode = str(mode).strip().upper()
    if mode == 'URL':
        if not html_url:
            raise Exception(f'Error (HR): A valid HTML URL is not found')
        response = fetch_url(html_url, check_status=False)
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
        return qhtml(code2html(html, 'text'))
    return qhtml(code2html(html, 'html'))


def js_reader__info():
    return {
        'title': 'JavaScript Reader',
        'showhide': {
            'mode': {
                'fields': ['upload_js', 'js_url', 'js_text'],
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
                'help_text': 'Choose whether to read JavaScript from a file, URL, or text input.',
            },
            'js_text': {
                'attrs': {
                    'data-lang': 'javascript',
                },
            },
        },
    }


# the default qcode must be left adjusted
def js_reader(upload_js: qfile = None, js_url: qurl = demo_url('demo.js'),
              js_text: qcode = """
function greet(name) {
    return `Hello, ${name}!`;
}

const numbers = [1, 2, 3, 4, 5];
const squares = numbers.map((n) => n * n);

console.log(greet('World'));
console.log(squares);
""", mode='URL'):
    mode = str(mode).strip().upper()
    if mode == 'URL':
        if not js_url:
            raise Exception(f'Error (JR): A valid JavaScript URL is not found')
        response = fetch_url(js_url, check_status=False)
        js = response.text
    elif mode == 'TEXT':
        if nzs(js_text) == '':
            raise Exception(f'Error (JR): A valid JavaScript Text is not found')
        js = js_text
    elif mode == 'FILE':
        if upload_js is None:
            raise Exception(f'Error (JR): A valid JavaScript File is not found')
        js = upload_js.text()
    else:
        raise Exception(f"Error (JR): mode must be one of 'File', 'URL', or 'Text'")
    return qhtml(code2html(js, 'javascript'))


if __name__ == '__main__':
    import os

    directory = 'S:/DATA/test_files/'
    for filename in os.listdir(directory):
        f = os.path.join(directory, filename)
        file_format = ''  # analyze_file(f)
        print(f'The file {f} is of type: {file_format}')
