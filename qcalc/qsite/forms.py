# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

from django import forms
from .utils.qmixins import AntiBotSecurityMixin


class ContactForm(AntiBotSecurityMixin, forms.Form):
    name = forms.CharField(max_length=100, required=True,
                           widget=forms.TextInput(attrs={"placeholder": "Enter your name please"}))
    email = forms.EmailField(required=True,
                             widget=forms.EmailInput(attrs={"placeholder": "Enter your email address please"}))
    subject = forms.CharField(max_length=100, required=True)
    message = forms.CharField(widget=forms.Textarea, required=True)
