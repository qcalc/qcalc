# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

from .qc_qty import *
from .mod_qfields import *
from qutil import fchoices, variable_to_title
from .mod_qfvalidators import validate_file_size


class QFieldHandler:
    formfields = {}

    # Create "DynaForm" input/output fields from json_schema

    def __init__(self, sname, json_schema, cid, json_s2f, post_data):
        self.sname = sname
        self.cid = cid
        self.list_added = {}  # dict of list

        i = -1
        for field_meta in json_schema:
            i += 1

            options = self.get_options(field_meta, post_data)
            if json_s2f and json_s2f[i]['type'] == 'c':
                type_key = field_meta['type'].lower()
                f = getattr(self, f"create_{type_key}_field")(field_meta, post_data, options)
            else:
                if ':' in field_meta['type']:
                    type_spec = field_meta['type'].lower().split(':')
                    type_key = type_spec[0]
                    variant = type_spec[1]
                    f = getattr(self, f"create_{type_key}_field")(field_meta, variant, options)
                else:
                    type_key = field_meta['type'].lower()
                    f = getattr(self, f"create_{type_key}_field")(field_meta, options)

            spec_attrs = field_meta.get('attrs', None) or {}
            for attr, value in spec_attrs.items():
                f.widget.attrs[attr] = value

            self.formfields[field_meta['name']] = f

        # print(self.formfields)

    # noinspection PyMethodMayBeStatic
    def get_options(self, field_meta, post_data):
        # | determine django field options from field_meta
        # | field-meta have a couple of exclusive parameters which options don't have
        # | such as name and type. Other parameters are same as django field options
        options = {
            'required': bool(field_meta.get('required', False)),
            'label': field_meta.get('label', variable_to_title(field_meta.get('name'))),
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
        if field_meta['type'].startswith('btn') or options['label'] == '-':  # or implicitly ""
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
            f = getattr(self, f"create_{type_key}_field")(fld_meta, opts)

            spec_attrs = fld_meta.get('attrs', None) or {}
            for attr, value in spec_attrs.items():
                f.widget.attrs[attr] = value

            fields.append(f)
            fnames.append(key)
            fvalues.append(fld_meta['initial'])
            fsufxs.append(fld_meta['sufx'])
        return QtyField(fields, fnames, fvalues, fsufxs, **options)

    def create_uom2_field(self, field_meta, options):
        # | in case of uom2 and select2 field_meta['initial'] is replaced with current posted value
        # | however options['initial'] remains the original arguement value
        uname = options['initial'] or 'm'
        lmt = uname2lmt(uname)
        list_exists = True
        if lmt not in self.list_added:
            list_exists = False
            self.list_added[lmt] = lmt2ulist(lmt)
        ulist = self.list_added[lmt]
        return Uom2Field(field_meta, lmt, list_exists, choices=ulist, **options)

    def create_uom_field(self, field_meta, options):  # tested, deb@08.23
        uname = field_meta['initial']
        lmt = uname2lmt(uname)
        list_exists = True
        if lmt not in self.list_added:
            list_exists = False
            self.list_added[lmt] = lmt2ulist(lmt)
        ulist = self.list_added[lmt]
        return UomField(field_meta, lmt, list_exists, choices=ulist, **options)

    # noinspection PyMethodMayBeStatic
    def create_uomx_field(self, field_meta, options):  # tested, deb@11.23
        uname = field_meta['initial']
        lmt = uname2lmt(uname)
        list_exists = True
        if lmt not in self.list_added:
            list_exists = False
            self.list_added[lmt] = lmt2ulist(lmt)
        ulist = self.list_added[lmt]
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
        id_ = f"{self.cid}_{field_meta['attrs']['id']}"
        return CodeField(id_, **{'initial': options['initial']})  # ??

    # noinspection PyMethodMayBeStatic
    def create_rchoice_field(self, _field_meta, options):  # tested, related choices, created by deb@13.09.23
        # source: https://stackoverflow.com/questions/53840628/
        # django-disable-form-select-field-validation-for-a-drop-down
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
    def create_typedchoice_field(self, _field_meta, options):
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
        max_mb = float(field_meta.get('max_mb', '10.0'))
        options['validators'].append(validate_file_size(max_mb))
        return forms.FileField(**options)

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
        max_mb = float(field_meta.get('max_mb', '10.0'))
        options['validators'].append(validate_file_size(max_mb))
        return forms.ImageField(**options)

    # noinspection PyMethodMayBeStatic
    def create_integer_field(self, _field_meta, options):  # tested
        # options['max_value'] = int(field_meta.get("max_value", "999999999"))
        # options['min_value'] = int(field_meta.get("min_value", "-999999999"))
        return forms.IntegerField(**options)

    # noinspection PyMethodMayBeStatic
    def create_range_field(self, field_meta, options):  # tested deb@29.10.23
        options['widget'] = field_meta.get('widget', forms.NumberInput(attrs={'type': 'range'}))
        return forms.IntegerField(**options)

    # noinspection PyMethodMayBeStatic
    def create_genericipaddress_field(self, _field_meta, options):
        return forms.GenericIPAddressField(**options)

    # noinspection PyMethodMayBeStatic
    def create_multiplechoice_field(self, field_meta, options):  # tested with choices
        options['choices'] = fchoices(field_meta['choices'])
        return forms.MultipleChoiceField(**options)

    # noinspection PyMethodMayBeStatic
    def create_typedmultiplechoice_field(self, _field_meta, options):
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
