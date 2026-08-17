# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

import re
from bs4 import BeautifulSoup
import requests
import markdown

import qconst
from qutil import nzs, to_df, demo_url
from qcore.mod_anno import *


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
        'title': 'Mark Down File Reader'
    }


def md_reader(upload_markdown: qfile = None, md_url: qurl = demo_url('demo.md'),
              markdown_text: qtexta = ''):
    if md_url:
        response = requests.get(md_url, timeout=(3, 15))
        md_text = response.text
    elif nzs(markdown_text) != '':
        md_text = markdown_text
    elif upload_markdown is not None:
        md_text = upload_markdown.file_bytes.decode()
    else:
        raise Exception(f'Error (MR): A valid Markdown File, Text or URL is not found')
    return qhtml(markdown.markdown(md_text, extensions=qconst.MARKDOWN_EXTENSIONS, output_format="html"))


def csv_reader__info():
    return {
        'title': 'CSV Reader',
        'schema': {
            'quoting': {
                'type': 'choice', 'choices': {
                    '0': 'Minimal', '1': 'All', '2': 'Non-Numeric', '3': 'None', '9': 'Remove Anyway'
                }
            }
        }
    }


def csv_reader(upload_csv: qfile = None, csv_url: qurl = demo_url('closing.csv'),
               quoting='1', delimiter: qchar = ',', transfer: str = ''):
    if csv_url:
        df = to_df(csv_url, delimiter, quoting)
    elif upload_csv:
        df = to_df(upload_csv.txt_buf(), delimiter, quoting)
    else:
        raise Exception(f'Error (CR): A valid CSV File or URL is not found')

    return {'table': df}


def csv_editor__info():
    return {
        'title': 'CSV Editor',
        'schema': {
            'quoting': {
                'type': 'choice', 'choices': {
                    '0': 'Minimal', '1': 'All', '2': 'Non-Numeric', '3': 'None', '9': 'Remove Anyway'
                }
            }
        },
        'script':
            """
$(document).ready(function() {
    load_button_id = 'id_' + getCid() + '_@load';
    $("#"+load_button_id).on("click", function() {
        cid = getCidOf($(this));
        extra_field_id = "extra_" + cid;
        calc_btn_id = "calculate_" + cid;
        table_id = this.id.replace("_@load", "").replace("id_","");
        extra = JSON.stringify({
            "cmd":"load", "from": "@upload_csv", "to": "@csv_table",
            "delimiter":"@delimiter", "quoting": "@quoting", "url": "@csv_url"
            });
        $("#"+extra_field_id).val(extra); //should update instead of asigning
        $("#"+calc_btn_id).trigger("click");
    });
});
            """
    }


def csv_editor(upload_csv: qfile = None, csv_url: qurl = demo_url('emp.csv'),
               quoting='1', delimiter: qchar = ',', load: 'btn:0' = 'Load CSV',
               csv_table: qtable = pd.DataFrame(columns=[])):
    if len(csv_table) != 0:
        return csv_table
    elif csv_url:
        return to_df(csv_url, delimiter, quoting)
    elif upload_csv:
        return to_df(upload_csv.txt_buf(), delimiter, quoting)
    else:
        raise Exception(f'Error (CR): A valid CSV File or URL is not found')


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
        'title': 'HTML Reader'
    }


def html_reader(upload_html: qfile = None, html_url: qurl = demo_url('demo.html')):
    # https://www.geeksforgeeks.org/remove-all-style-scripts-and-html-tags-using-beautifulsoup/
    if html_url != '':
        response = requests.get(html_url, timeout=(3, 15))
        html = response.content
    elif upload_html is not None:
        html = upload_html.txt_buf()
    else:
        raise Exception(f'Error (HR): A valid HTML File or URL is not found')
    txt = remove_tags(html)
    return qhtml(txt)


# def analyze_file(file_path):
#     # Get MIME type using magic library
#     mime = magic.Magic(mime=True)
#     mime_type = mime.from_file(file_path)
#     return mime_type


if __name__ == '__main__':
    import os

    directory = 'S:/DATA/test_files/'
    for filename in os.listdir(directory):
        f = os.path.join(directory, filename)
        file_format = ''  # analyze_file(f)
        print(f'The file {f} is of type: {file_format}')
