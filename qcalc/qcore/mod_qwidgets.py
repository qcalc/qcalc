# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

from django import forms
from django.utils.html import escape
from django.utils.safestring import mark_safe
from django.forms import Widget
import pandas as pd
import json
from qutil import resize_df


class ButtonWidget(Widget):
    def __init__(self, field_meta, variant, **kwargs):
        super().__init__(**kwargs)
        self.caption = field_meta['initial']
        # self.caption = field_meta['label']
        self.btnid = field_meta['attrs']['id']
        self.variant = variant

    def get_variant(self):
        v = {
            "type": "button",
            "onclick": "",
            "class": "btn btnimg",
            "icon": "",  # warning: icon if defined can be event.target
            "xdef": "",
            "xcap": ""
        }
        # if self.variant == '+':
        #     v.update({"class": "btn btn-t imgbtn", "icon": "icon-plus3", "xcap": None})
        # elif self.variant == '-':
        #     v.update({"class": "btn btn-t imgbtn", "icon": "icon-minus3", "xcap": None})
        if self.variant == '0':
            v.update({"class": "btn btn-info btncmd", "xcap": ""})
        return v

    def render(self, name, value, attrs=None, renderer=None):
        v = self.get_variant()
        clk = f' onclick="{v['onclick']}"' if v['onclick'] else ""
        ico = f'<i class="{v['icon']}"></i>' if v['icon'] else ""
        button_html = (f'<button type="{v['type']}" name="{name}" id="{self.btnid}" '
                       f'class="{v['class']}"{clk} {v['xdef']}>{ico}{self.caption}</button>')  #
        return mark_safe(button_html)


class HtmlWidget(Widget):
    def __init__(self, *args, **kwargs):
        super(Widget, self).__init__(*args, **kwargs)
        self.attrs = {}

    def render(self, name, value, attrs=None, renderer=None):
        return mark_safe(value)


class CodeWidget_codemirror(Widget):
    @property
    def media(self):
        from django.templatetags.static import static

        return forms.Media(
            css={'all': [
                static("vendor/codemirror/5.65.5/codemirror.min.css"),
                static("vendor/codemirror/5.65.5/dracula.min.css"),
            ]},
            js=[static("vendor/codemirror/5.65.5/codemirror.min.js"),
                static("vendor/codemirror/5.65.5/mode/python.min.js"),
                static("vendor/codemirror/5.65.5/matchbrackets.min.js"),
                ]
        )

    def __init__(self, id_, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.id = id_

    def render(self, name, value, attrs=None, renderer=None):
        ret = str(self.media)
        ret += '''
        <style>
            .CodeMirror {
                border: 1px solid #ccc;
                height: 250px;
                min-height: 100px;
                resize: vertical;
                overflow: auto;
            }
            .elem-wrapper.fullscreen .CodeMirror {
                height: 95vh;
            }
        </style>
        '''
        ret += f'''
        <div class="elem-wrapper" style="width:100%;">
        <textarea id="{self.id}" name="{name}"{' disabled' if (attrs or {}).get('disabled') else ''}{' readonly' if (attrs or {}).get('readonly') else ''}>{escape(value) if value else ""}</textarea>
        <span class="fullscreen-square" onclick="toggleFullscreen(this.closest('.elem-wrapper'))"></span>
         <input type="file" id="{self.id}_upload" accept=".py,text/x-python" class="inputfile"
             onchange="uploadCodeMirrorWidget(this, '{self.id}')">
         <button type="button" class="btn btn-info btncmd mt-2" title="Upload from Python file"
              aria-label="Upload from Python file" onclick="document.getElementById('{self.id}_upload').click()">
             <i class="icon-file-upload"></i>
         </button>
        <button type="button" class="btn btn-info btncmd mt-2" title="Save to Python file"
                aria-label="Save to Python file" onclick="downloadCodeMirrorWidget('{self.id}')">
            <i class="icon-file-download"></i>
        </button>
        </div>
        <script>initializeCodeMirrorWidget("{self.id}");</script>
        '''
        # background-color: #282a36; is dracula theme background
        return mark_safe(ret)


class TextDataListWidget(forms.TextInput):
    def __init__(self, list_id, list_exists, data_list, name, *args, **kwargs):
        super(TextDataListWidget, self).__init__(*args, **kwargs)
        self._name = name
        self._list = data_list
        self.list_id = list_id
        self.list_exists = list_exists
        self.attrs.update({'list': 'list__%s' % self.list_id})

    def render(self, name, value, attrs=None, renderer=None):
        text_html = super(TextDataListWidget, self).render(name, value, attrs=attrs)
        result = text_html
        if not self.list_exists:
            data_list = '<datalist id="list__%s">' % self.list_id
            for item in self._list:
                data_list += f'<option value="{item[0]}">{item[1]}</option>'
            data_list += '</datalist>'
            result += data_list
        return mark_safe(result)  # dj5


class SelectDataListWidget(forms.Select):
    def __init__(self, list_id, list_exists, data_list, name, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._name = name
        self._list = data_list
        self.list_id = list_id
        self.list_exists = list_exists
        self.attrs.update({'data-list': 'list__%s' % self.list_id})

    def render(self, name, value, attrs=None, renderer=None):
        text_html = super().render(name, value, attrs=attrs)
        result = text_html
        if not self.list_exists:
            data_list = '<datalist id="list__%s">' % self.list_id
            for item in self._list:
                data_list += f'<option value="{item[0]}">{item[1]}</option>'
            data_list += '</datalist>'
            result += data_list
            # print(attrs, result)
        return mark_safe(result)  # dj5


class QtyWidget(forms.MultiWidget):
    # template_name = 'qty.html'

    def __init__(self, widgets, fnames, fvalues):
        super(QtyWidget, self).__init__(widgets)
        self.fnames = fnames
        self.fvalues = fvalues

    def render(self, name, value, attrs=None, renderer=None):
        html = ''
        if all(x is None for x in value):
            value = self.fvalues
        for w, n, v in zip(self.widgets, self.fnames, value):  # self.fvalues
            html += w.render(n, v)
        # ic(html)
        return mark_safe(html)


class TabulatorWidget(Widget):
    def __init__(self, cid, class_, *args, **kwargs):
        super(Widget, self).__init__(*args, **kwargs)
        self.attrs = {}
        self.cid = cid
        self.class_ = class_

    def render(self, name, value, attrs=None, renderer=None):
        # print('v',value)
        defa_mode = "edit"
        if isinstance(value, pd.DataFrame):  # data from django
            df = value
            resize = []
            mode = defa_mode  # default
            # print('mode defa', mode)
        elif isinstance(value, dict):  # input from json file
            # df = pd.DataFrame(value)
            # orient="split"
            if "data" in value and "columns" in value:
                df = pd.DataFrame(
                    data=value["data"],
                    columns=value["columns"],
                    index=value.get("index"),
                )
            else:
                # ordinary dict (dict of lists, etc.)
                df = pd.DataFrame(value)
            resize = value.get('shape', [])
            mode = defa_mode
        elif isinstance(value, list): # input from json file
            # orient="records"
            df = pd.DataFrame(value)
            resize = []
            mode = defa_mode
        else:  # data from JS (JSON string)
            try:
                # print(f"type(value) = {type(value)}")
                # print(value)
                value = json.loads(value)
                # df = pd.DataFrame(data=value['data'], columns=value['columns'])
                if isinstance(value, list):
                    # orient="records"
                    df = pd.DataFrame(value)

                elif isinstance(value, dict):
                    if "data" in value and "columns" in value:
                        # orient="split"
                        df = pd.DataFrame(
                            data=value["data"],
                            columns=value["columns"],
                            index=value.get("index"),
                        )
                    else:
                        # ordinary dict
                        df = pd.DataFrame(value)
                else:
                    raise ValueError(f"Error (TEW2): Unsupported DataFrame format for table {name}")
            except Exception as e:
                # e.args = (f'Error (TEW2): Invalid value {value} for table {name}',)
                e.args = (f'Error (TEW2): Invalid value for table {name}',)
                raise e
            resize = value.get('shape', [])
            mode = value.get('mode', '')  # edit, display
            # print('mode in data', mode)

        mode = mode if self.class_ == '' else ('edit' if self.class_ == 'table-in' else 'display')
        # print('mode, class_', mode, self.class_)
        extra_cols = 0  # if "Edit" in df.columns else 0  # before resizing
        # if self.mode == 'edit':
        cur_nrow = len(df)
        cur_ncol = len(df.columns) - extra_cols
        # print(cur_nrow, cur_ncol, extra_cols)
        if len(resize) == 0 and cur_nrow == 0 and cur_ncol > 0:
            nrow = 1
            ncol = cur_ncol
            if nrow != cur_nrow or ncol != cur_ncol:
                df = resize_df(df, nrow, ncol, extra_cols)
                extra_cols = 0  # if "Edit" in df.columns else 0  # after resizing
        elif len(resize) > 0:  # or cur_nrow == 0 or cur_ncol <= 0:
            nrow = max(int(resize[0]), 0)
            ncol = max(int(resize[1]), 0)
            if nrow != cur_nrow or ncol != cur_ncol:
                df = resize_df(df, nrow, ncol, extra_cols)
                extra_cols = 0  # if "Edit" in df.columns else 0  # after resizing

        # | making it 0 based row index
        # df.index = range(1, len(df) + 1)
        row = len(df)
        col = len(df.columns) - extra_cols

        # df = df.apply(lambda col: col.map(df_formatter))  # dont apply format for table-in
        html = df.to_html(
            table_id=f"{self.cid}_{name}",
            classes=f'table table-responsive table-in {self.cid}',  # display, class=hidden
            na_rep='',
            # float_format=qformatter().format,
            index=False,
        )

        # if mode == 'edit' and extra_cols == 0:
        #     html = html

        ed = 'Display' if mode == 'edit' else 'Edit'
        row_inp = f'<label for="id_{self.cid}_{name}_row">Row:</label>' + \
                  f'<input type="text" name="{name}_row" value="{row}" id="id_{self.cid}_{name}_row" class="vt mr-2">'
        col_inp = f'<label for="id_{self.cid}_{name}_col">Col:</label>' + \
                  f'<input type="text" name="{name}_col" value="{col}" id="id_{self.cid}_{name}_col" class="vt mr-2">'
        rsz_btn = f'<button type="button" name="{name}_table_resize" id="id_{self.cid}_{name}_table_resize" ' + \
                  f'class="btn btn-info btncmd mr-2" >Resize</button>'
        ed_btn = f'<button type="button" name="{name}_table_ed" id="id_{self.cid}_{name}_table_ed" ' + \
                 f'class="btn btn-info btncmd tbl-ed">{ed}</button>'

        if mode == 'edit':
            upd_btn = f'<button type="button" name="{name}_table_update" id="id_{self.cid}_{name}_table_update" ' + \
                      f'class="btn btn-info btncmd mr-2" >Update</button>'
            html += f'<span>{upd_btn}{row_inp}{col_inp}{rsz_btn}{ed_btn}</span>'
        else:
            html += f'<span>{row_inp}{col_inp}{rsz_btn}{ed_btn}</span>'

        hidden_field = f'<input type="hidden" name="{name}" value="" id="id_{self.cid}_{name}">'
        html = hidden_field + html
        return mark_safe(html)
