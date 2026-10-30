# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

from django.utils.html import format_html
from .qc_qty import *
from .mod_qfields import *
from qutil import fchoices, variable_to_title
from qutil.mod_settings import max_file_mb
from .mod_qfvalidators import validate_file_size
from .mod_qcutil import request_prefs


class RangeWidget(forms.NumberInput):
    # Slider showing min, current (live) and max values
    input_type = 'range'

    def render(self, name, value, attrs=None, renderer=None):
        attrs = dict(attrs or {})
        attrs['oninput'] = 'this.parentNode.querySelector("output").value=this.value'
        attrs['style'] = 'width:100%'
        slider = super().render(name, value, attrs, renderer)
        a = {**self.attrs, **attrs}
        lo = a.get('min', 0)
        hi = a.get('max', 100)
        cur = lo if value in (None, '') else value
        return format_html(
            '<div class="range-wrap" style="width:100%;max-width:20rem">{}'
            '<div style="display:flex;justify-content:space-between;font-size:.85em;line-height:1;margin-top:-.2rem;color:#6c757d">'
            '<span class="range-min">{}</span>'
            '<output class="range-cur" style="font-weight:400;color:#0d6efd">{}</output>'
            '<span class="range-max">{}</span></div></div>',
            slider, lo, cur, hi)


class QFieldHandler:
    # Create "DynaForm" input/output fields from json_schema

    def __init__(self, sname, json_schema, cid, json_s2f, post_data, proper_dict):
        # Keep fields instance-scoped so insertion order is rebuilt per form.
        # A shared class dict can leak prior ordering between requests/calculators.
        self.formfields = {}
        self.sname = sname
        self.cid = cid
        self.list_added = {}  # dict of list
        self.proper_dict = proper_dict
        pref = request_prefs()
        self.uom_subset = pref.get('uom_subset_enabled', False)

        i = -1
        for field_meta in json_schema:
            i += 1

            options = self.get_options(field_meta, post_data)
            if json_s2f and json_s2f[i]['type'] == 'c':
                type_key = field_meta['type'].lower()
                f = self._get_field_builder(type_key, field_meta['name'])(field_meta, post_data, options)
            else:
                if ':' in field_meta['type']:
                    type_spec = field_meta['type'].lower().split(':')
                    type_key = type_spec[0]
                    variant = type_spec[1]
                    f = self._get_field_builder(type_key, field_meta['name'])(field_meta, variant, options)
                else:
                    type_key = field_meta['type'].lower()
                    f = self._get_field_builder(type_key, field_meta['name'])(field_meta, options)

            spec_attrs = field_meta.get('attrs', None) or {}
            for attr, value in spec_attrs.items():
                f.widget.attrs[attr] = value

            self.formfields[field_meta['name']] = f

        # print(self.formfields)

    def _field_builders(self):
        return {
            'boolean': self.create_boolean_field,
            'btn': self.create_btn_field,
            'char': self.create_char_field,
            'checkbox': self.create_checkbox_field,
            'checkboxselectmultiple': self.create_checkboxselectmultiple_field,
            'choice': self.create_choice_field,
            'codeedit': self.create_codeedit_field,
            'combo': self.create_combo_field,
            'date': self.create_date_field,
            'datetime': self.create_datetime_field,
            'decimal': self.create_decimal_field,
            'duration': self.create_duration_field,
            'email': self.create_email_field,
            'file': self.create_file_field,
            'filepath': self.create_filepath_field,
            'float': self.create_float_field,
            'genericipaddress': self.create_genericipaddress_field,
            'hidden': self.create_hidden_field,
            'html': self.create_html_field,
            'image': self.create_image_field,
            'integer': self.create_integer_field,
            'multiplechoice': self.create_multiplechoice_field,
            'multivalue': self.create_multivalue_field,
            'nullboolean': self.create_nullboolean_field,
            'qty': self.create_qty_field,
            'radio': self.create_radio_field,
            'range': self.create_range_field,
            'rchoice': self.create_rchoice_field,
            'read': self.create_read_field,
            'regex': self.create_regex_field,
            'select2': self.create_select2_field,
            'slug': self.create_slug_field,
            'table': self.create_table_field,
            'text': self.create_text_field,
            'textarea': self.create_textarea_field,
            'textedit': self.create_textedit_field,
            'time': self.create_time_field,
            'typedchoice': self.create_typedchoice_field,
            'typedmultiplechoice': self.create_typedmultiplechoice_field,
            'uom': self.create_uom_field,
            'uom2': self.create_uom2_field,
            'uomx': self.create_uomx_field,
            'url': self.create_url_field,
            'uuid': self.create_uuid_field,
        }

    def _get_field_builder(self, type_key, field_name):
        builder = self._field_builders().get(type_key)
        if builder is None:
            raise ValueError(f"Unknown field type '{type_key}' for '{field_name}'")
        return builder

    # noinspection PyMethodMayBeStatic
    def get_options(self, field_meta, post_data):
        # | determine django field options from field_meta
        # | field-meta have a couple of exclusive parameters which options don't have
        # | such as name and type. Other parameters are same as django field options
        options = {
            'required': bool(field_meta.get('required', False)),
            'label': field_meta.get('label', variable_to_title(field_meta.get('name'), self.proper_dict)),
            'label_suffix': field_meta.get('label_suffix', None),
            'initial': field_meta.get('initial', None),
            'widget': field_meta.get('widget', None),
            'help_text': field_meta.get('help_text', ''),
            # 'placeholder': field_meta.get('placeholder', ''),
            'error_messages': field_meta.get('error_messages', []),
            'validators': field_meta.get('validators', []),
            'localize': field_meta.get('localize', None),
            'disabled': bool(field_meta.get('disabled', 0))
        }

        # | in case of uom2 and select2 field_meta['initial'] is replaced with current posted value
        # | however options['initial'] remains the original arguement value
        if field_meta['type'] in ['uom2', 'select2', 'quom2', 'qsel2']:  # @08-13.01.24
            if field_meta['name'] in post_data:
                field_meta['initial'] = post_data[field_meta['name']]
        # | Hide label if following conditions are met
        if (field_meta['type'].startswith('btn') or  # annotation 'btn:0' etc.
            field_meta['name'].startswith('_') or  # variable name
            options['label'].startswith('_') or  # label name
            options['label'].startswith('-')):  # label name or implicitly ""
            options['label'] = ""
        return options

    def create_select2_field(self, field_meta, options):  #
        sel2id = field_meta.get('sel2id', field_meta['name'])
        if sel2id != field_meta['name']:
            list_exists = True
            if sel2id not in self.list_added:
                list_exists = False
                self.list_added[sel2id] = fchoices(field_meta['choices'])
            slist = self.list_added[sel2id]
        else:
            list_exists = False
            slist = fchoices(field_meta['choices'])
        return Select2Field(field_meta, sel2id, list_exists, choices=slist, **options)

    def create_qty_field(self, field_meta, arg2, options=None):  #
        if options is None:
            post_data = {}
            options = arg2
        else:
            post_data = arg2

        fields = []
        fnames = []
        fvalues = []
        fsufxs = []
        for key in field_meta['comp']:
            fld_meta = field_meta['comp'][key]
            opts = self.get_options(fld_meta, post_data)
            type_key = fld_meta['type'].lower()
            f = self._get_field_builder(type_key, fld_meta['name'])(fld_meta, opts)

            spec_attrs = fld_meta.get('attrs', None) or {}
            for attr, value in spec_attrs.items():
                f.widget.attrs[attr] = value

            fields.append(f)
            fnames.append(key)
            # print('|', key)
            fvalues.append(fld_meta['initial'])
            fsufxs.append(fld_meta['sufx'])
        return QtyField(fields, fnames, fvalues, fsufxs, **options)

    def _uom_choices(self, uname):
        # In subset mode the list may carry an extra default unit (e.g. 'roti' for gold), so
        # lists of one lmt can differ. Each distinct list gets its own datalist id; reusing one
        # id for several datalists makes the client collect every option once per datalist.
        lmt = unit2lmt(uname)
        ulist = lmt2ulist(lmt, subset=self.uom_subset, default_uname=uname)
        cache_key = (lmt, tuple(u[0] for u in ulist))
        list_exists = cache_key in self.list_added
        if not list_exists:
            n = sum(1 for k in self.list_added if isinstance(k, tuple) and k[0] == lmt)
            list_id = lmt if n == 0 else f'{lmt}_{n}'
            self.list_added[cache_key] = (list_id, ulist)
        list_id, ulist = self.list_added[cache_key]
        return list_id, list_exists, ulist

    def create_uom2_field(self, field_meta, options):
        # | in case of uom2 and select2 field_meta['initial'] is replaced with current posted value
        # | however options['initial'] remains the original arguement value
        uname = options['initial'] or 'm'
        lmt, list_exists, ulist = self._uom_choices(uname)
        return Uom2Field(field_meta, lmt, list_exists, choices=ulist, **options)

    def create_uom_field(self, field_meta, options):  # tested, deb@08.23
        uname = field_meta['initial']
        lmt, list_exists, ulist = self._uom_choices(uname)
        return UomField(field_meta, lmt, list_exists, choices=ulist, **options)

    # noinspection PyMethodMayBeStatic
    def create_uomx_field(self, field_meta, options):  # tested, deb@11.23
        uname = field_meta['initial']
        lmt, list_exists, ulist = self._uom_choices(uname)
        return UomxField(field_meta, lmt, list_exists, choices=ulist, **options)

    def create_table_field(self, field_meta, options):
        return TabulatorField(field_meta, self.cid, **options)

    # noinspection PyMethodMayBeStatic
    def create_boolean_field(self, _field_meta, options):  # tested
        return forms.BooleanField(**options)

    # noinspection PyMethodMayBeStatic
    def create_btn_field(self, field_meta, variant, options):  # tested
        return ButtonField(field_meta, variant, **options)

    # noinspection PyMethodMayBeStatic
    def create_checkbox_field(self, field_meta, options):  # tested - there is no choices in django CehckboxInput
        options['widget'] = field_meta.get('widget', forms.CheckboxInput)
        return forms.BooleanField(**options)  # ??

    # noinspection PyMethodMayBeStatic
    def create_checkboxselectmultiple_field(self, field_meta, options):  # tested deb@08.23
        # tested - there is no choices in django CehckboxInput
        options['choices'] = fchoices(field_meta['choices'])
        options['widget'] = field_meta.get('widget', forms.CheckboxSelectMultiple)
        # source: https://stackoverflow.com/questions/52137632/how-to-display-choices-as-checkboxes-in-django
        # return forms.CheckboxSelectMultiple(**options)
        return forms.MultipleChoiceField(**options)

    # noinspection PyMethodMayBeStatic
    def create_char_field(self, field_meta, options):  # tested
        options['max_length'] = int(field_meta.get('max_length', '50'))
        return forms.CharField(**options)

    # def create_editor_field(self, field_meta, options):
    #     return EditorField(**options)

    # noinspection PyMethodMayBeStatic
    def create_hidden_field(self, field_meta, options):  # tested
        options['widget'] = field_meta.get('widget', forms.HiddenInput())
        return forms.CharField(**options)

    # noinspection PyMethodMayBeStatic
    def create_read_field(self, field_meta, options):  # tested
        options['max_length'] = int(field_meta.get('max_length', '50'))
        options['widget'] = field_meta.get('widget', forms.TextInput(attrs={'readonly': True}))
        return forms.CharField(**options)

    # noinspection PyMethodMayBeStatic
    def create_text_field(self, field_meta, options):  # tested
        options['max_length'] = int(field_meta.get('max_length', '255'))
        return forms.CharField(**options)  # ok

    # noinspection PyMethodMayBeStatic
    def create_textarea_field(self, field_meta, options):  # tested
        options['max_length'] = int(field_meta.get('max_length', "65536"))
        options['widget'] = field_meta.get('widget', forms.Textarea())
        return forms.CharField(**options)  # ??

    # noinspection PyMethodMayBeStatic
    def create_textedit_field(self, field_meta, options):  # tested
        options['max_length'] = int(field_meta.get('max_length', "65536"))
        options['widget'] = field_meta.get('widget', forms.Textarea())
        return forms.CharField(**options)  # ??

    # noinspection PyMethodMayBeStatic
    def create_codeedit_field(self, field_meta, options):  # tested
        # id_ = f"{self.cid}_{field_meta['attrs']['id']}"
        id_ = field_meta['attrs']['id']
        return CodeField(id_, **options)

    # noinspection PyMethodMayBeStatic
    def create_rchoice_field(self, field_meta, options):  # tested, related choices, created by deb@13.09.23
        # source: https://stackoverflow.com/questions/53840628/
        # django-disable-form-select-field-validation-for-a-drop-down
        choices = field_meta.get('choices')
        if choices is None:
            choices = [options['initial']] if options.get('initial') is not None else []
        options['choices'] = fchoices(choices)
        return ChoiceFieldNoValidation(**options)

    # noinspection PyMethodMayBeStatic
    def create_choice_field(self, field_meta, options):  # tested
        options['choices'] = fchoices(field_meta['choices'])
        return forms.ChoiceField(**options)

    # noinspection PyMethodMayBeStatic
    def create_radio_field(self, field_meta, options):  # tested
        options['choices'] = fchoices(field_meta['choices'])
        options['widget'] = field_meta.get('widget', forms.RadioSelect)
        return forms.ChoiceField(**options)  # ??

    # noinspection PyMethodMayBeStatic
    def create_typedchoice_field(self, field_meta, options):
        options['choices'] = fchoices(field_meta['choices'])
        return forms.TypedChoiceField(**options)

    # noinspection PyMethodMayBeStatic
    def create_date_field(self, field_meta, options):  # tested
        options['widget'] = field_meta.get('widget', forms.DateInput(attrs={'type': 'date'}))  # SelectDateWidget
        return forms.DateField(**options)

    # noinspection PyMethodMayBeStatic
    def create_datetime_field(self, _field_meta, options):  # tested
        return forms.DateTimeField(**options)

    # noinspection PyMethodMayBeStatic
    def create_decimal_field(self, _field_meta, options):
        return forms.DecimalField(**options)

    # noinspection PyMethodMayBeStatic
    def create_duration_field(self, _field_meta, options):
        return forms.DurationField(**options)

    # noinspection PyMethodMayBeStatic
    def create_email_field(self, _field_meta, options):  # tested
        return forms.EmailField(**options)

    # noinspection PyMethodMayBeStatic
    def create_file_field(self, field_meta, options):  # tested
        max_mb = max_file_mb(field_meta.get('max_mb'))
        options['validators'].append(validate_file_size(max_mb))
        field = forms.FileField(**options)
        field.widget.attrs.setdefault('data-max-mb', f'{max_mb:g}')  # read by validateFileSize() in qcalc.js
        return field

    # noinspection PyMethodMayBeStatic
    def create_filepath_field(self, _field_meta, options):
        return forms.FilePathField(**options)

    # noinspection PyMethodMayBeStatic
    def create_float_field(self, _field_meta, options):  # tested
        # options['max_value'] = int(field_meta.get("max_value", "999999999"))
        # options['min_value'] = int(field_meta.get("min_value", "-999999999"))
        return forms.FloatField(**options)

    # noinspection PyMethodMayBeStatic
    def create_image_field(self, field_meta, options):
        max_mb = max_file_mb(field_meta.get('max_mb'))
        options['validators'].append(validate_file_size(max_mb))
        field = forms.ImageField(**options)
        field.widget.attrs.setdefault('data-max-mb', f'{max_mb:g}')  # read by validateFileSize() in qcalc.js
        return field

    # noinspection PyMethodMayBeStatic
    def create_integer_field(self, _field_meta, options):  # tested
        # options['max_value'] = int(field_meta.get("max_value", "999999999"))
        # options['min_value'] = int(field_meta.get("min_value", "-999999999"))
        return forms.IntegerField(**options)

    # noinspection PyMethodMayBeStatic
    def create_range_field(self, field_meta, options):  # tested deb@29.10.23
        options['widget'] = field_meta.get('widget', RangeWidget())
        for key in ('min_value', 'max_value'):
            if key in field_meta:
                options[key] = field_meta[key]
        if 'step' in field_meta:
            options['widget'].attrs['step'] = field_meta['step']
        return forms.IntegerField(**options)

    # noinspection PyMethodMayBeStatic
    def create_genericipaddress_field(self, _field_meta, options):
        return forms.GenericIPAddressField(**options)

    # noinspection PyMethodMayBeStatic
    def create_multiplechoice_field(self, field_meta, options):  # tested with choices
        options['choices'] = fchoices(field_meta['choices'])
        return forms.MultipleChoiceField(**options)

    # noinspection PyMethodMayBeStatic
    def create_typedmultiplechoice_field(self, field_meta, options):
        options['choices'] = fchoices(field_meta['choices'])
        return forms.TypedMultipleChoiceField(**options)

    # noinspection PyMethodMayBeStatic
    def create_nullboolean_field(self, _field_meta, options):
        return forms.NullBooleanField(**options)

    # noinspection PyMethodMayBeStatic
    def create_regex_field(self, field_meta, options):  # tested@8.11.23
        options['regex'] = field_meta.get('regex', '')
        return forms.RegexField(**options)

    # noinspection PyMethodMayBeStatic
    def create_slug_field(self, _field_meta, options):
        return forms.SlugField(**options)

    # noinspection PyMethodMayBeStatic
    def create_time_field(self, _field_meta, options):  # tested
        return forms.TimeField(**options)

    # noinspection PyMethodMayBeStatic
    def create_url_field(self, _field_meta, options):  # tested
        options["assume_scheme"] = "https"
        return forms.URLField(**options)

    # noinspection PyMethodMayBeStatic
    def create_html_field(self, field_meta, options):  # tested
        return HtmlField(field_meta, **options)

    # noinspection PyMethodMayBeStatic
    def create_uuid_field(self, _field_meta, options):
        return forms.UUIDField(**options)

    # noinspection PyMethodMayBeStatic
    def create_combo_field(self, _field_meta, options):  # !?
        return forms.ComboField(**options)

    # noinspection PyMethodMayBeStatic
    def create_multivalue_field(self, _field_meta, options):
        return forms.MultiValueField(**options)

    # # noinspection PyMethodMayBeStatic
    # def create_splitdatetime_field(self, _field_meta, options):
    #     return forms.SplitDateTimeField(**options)
