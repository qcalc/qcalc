# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

from .mod_qwidgets import *
from django.forms import Field, CharField, ChoiceField
from .qc_munit import isMeasureUnit
from .qc_units import find_unit
from django.core.exceptions import ValidationError


class ButtonField(CharField):
    def __init__(self, field_meta, variant, **kwargs):
        super().__init__(**kwargs)
        self.widget = ButtonWidget(field_meta, variant)


class ChoiceFieldNoValidation(ChoiceField):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def validate(self, value):
        pass


class ChoiceEditField(CharField):

    def __init__(self, field_meta, list_id, list_exists, choices, **kwargs):
        super().__init__(**kwargs)
        self.choices = choices
        self.widget = TextDataListWidget(list_id, list_exists, choices, field_meta['name'])

    def to_python(self, value):
        return super().to_python(value)


class ChoiceEditField2(ChoiceField):

    def __init__(self, field_meta, list_id, list_exists, choices, **kwargs):
        super().__init__(**kwargs)
        self.choices = choices
        self.widget = SelectDataListWidget(list_id, list_exists, choices, field_meta['name'])
        self.widget.attrs.update({'data-default': field_meta['initial']})

    def to_python(self, value):
        # | do not return super().to_python(value)
        return value  # | to allow for uom like USD/g


class UomField(ChoiceEditField):
    default_error_messages = {
        'invalid': 'Enter a compatible unit.',
    }

    def __init__(self, field_meta, lmt, list_exists, choices, **kwargs):
        super().__init__(field_meta, lmt, list_exists, choices, **kwargs)
        self.default = field_meta['initial'] or 'm'

    def to_python(self, value):
        defa_unit = find_unit(self.default)
        try:
            input_unit = find_unit(value)
        except Exception as e:
            raise ValidationError(str(e))
        if not defa_unit.is_compatible(input_unit):
            raise ValidationError(self.error_messages['invalid'], code='invalid')
        return super().to_python(value)


class UomxField(ChoiceEditField):
    default_error_messages = {
        'invalid': 'Enter a valid unit.',
    }

    def __init__(self, field_meta, lmt, list_exists, choices, **kwargs):
        super().__init__(field_meta, lmt, list_exists, choices, **kwargs)
        self.default = field_meta['initial'] or 'm'

    def to_python(self, value):
        defa_unit = find_unit(self.default)
        if not isMeasureUnit(defa_unit):
            raise ValidationError(self.error_messages['invalid'], code='invalid')
        try:
            input_unit = find_unit(value)
        except Exception as e:
            raise ValidationError(str(e))
        if not isMeasureUnit(input_unit):
            raise ValidationError(self.error_messages['invalid'], code='invalid')
        return super().to_python(value)


class HtmlField(Field):
    def __init__(self, _field_meta, **kwargs):
        super().__init__(**kwargs)
        self.widget = HtmlWidget()

    def validate(self, value):
        pass


class CodeField(Field):
    def __init__(self, id_, **kwargs):
        super().__init__(**kwargs)
        # class_ = field_meta.get('attrs', {}).get('class', '')
        self.widget = CodeWidget_codemirror(id_=id_)

    def to_python(self, value):
        return value

    def validate(self, value):
        pass


class TabulatorField(Field):
    def __init__(self, field_meta, cid, **kwargs):
        super().__init__(**kwargs)
        class_ = field_meta.get('attrs', {}).get('class', '')
        self.widget = TabulatorWidget(cid, class_=class_)
        self.empty_values = []

    def validate(self, value):
        pass


class Select2Field(ChoiceEditField2):
    def __init__(self, field_meta, list_id, list_exists, choices, **kwargs):
        super().__init__(field_meta, list_id, list_exists, choices, **kwargs)

    def validate(self, value):
        pass


class Uom2Field(ChoiceEditField2):
    default_error_messages = {
        'invalid': 'Enter a compatible unit.',
    }

    def __init__(self, field_meta, lmt, list_exists, choices, **kwargs):
        super().__init__(field_meta, lmt, list_exists, choices, **kwargs)
        self.default = kwargs['initial'] or 'm'

    def to_python(self, value):
        defa_unit = find_unit(self.default)
        try:
            input_unit = find_unit(value)
        except Exception as e:
            raise ValidationError(str(e))
        if not defa_unit.is_compatible(input_unit):
            raise ValidationError(self.error_messages['invalid'], code='invalid')
        return super().to_python(value)

    def validate(self, value):
        # | if not found in list but compatible it's ok e.g. usd/g
        pass


class QtyField(forms.MultiValueField):

    def __init__(self, fields, fnames, fvalues, fsufxs, **kwargs):
        # widgets = {prefix: fld.widget for fld, prefix in zip(fields, fnames)}
        widgets = {sufx: fld.widget for fld, sufx in zip(fields, fsufxs)}
        self.widget = QtyWidget(widgets, fnames, fvalues)
        self.initial = fvalues
        # self.widget = forms.MultiWidget(widgets)
        super().__init__(fields, **kwargs)

    def compress(self, values):
        # ic('fc', values, self.initial)
        return values
        # ln = len(self.fields)
        # parts = []
        # for i in range(0, ln, 2):
        #     parts.append(f"{values[i]} {values[i + 1]}")
        # toret = ', '.join(parts)
        # ic(toret)
        # return toret

    def validate(self, value):
        pass

    # def clean(self, value):  # call compress
    #     ic('clean', value, self.initial)
    #     return value
