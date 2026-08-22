# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

import time
import random
from hashlib import sha256
from django import forms
from qutil import makeid, ordinal, qdomain


class AntiBotSecurityMixin(forms.Form):
    """
    A reusable mixin that adds Honeypot, Time-based validation,
    User-Agent monitoring, Referrer domain verification, and
    a simple Q&A CAPTCHA designed by qCalc.
    """
    # | Security & CAPTCHA fields
    captcha_question = forms.CharField(widget=forms.HiddenInput, required=False)
    captcha_answer = forms.CharField(required=True)
    captcha_correct_answer = forms.CharField(widget=forms.HiddenInput, required=False)

    # | Honeypot field (hidden from humans, filled by bots)
    honeypot = forms.CharField(required=False, widget=forms.HiddenInput)

    # | Time-Based Validation
    timestamp = forms.IntegerField(widget=forms.HiddenInput, required=False)

    def __init__(self, *args, **kwargs):
        # 1. Safely extract request from kwargs (used by allauth & class-based views)
        # 2. Or fallback to pulling the first positional argument if it's passed that way
        self.request = kwargs.pop('request', None)
        # 2. If not found in kwargs, check if it was passed positionally in args
        if not self.request and args:
            # If the first argument is a HttpRequest object, pluck it out
            if hasattr(args[0], 'META'):
                self.request = args[0]
                args = args[1:]  # Shift args down so super() doesn't choke

        is_post = kwargs.pop('post', False)
        super().__init__(*args, **kwargs)

        # Fallback automated check if 'post=True' wasn't explicitly passed
        if not is_post and self.request and self.request.method == 'POST':
            is_post = True

        if not is_post:
            question, answer = self.get_random_qa()
            self.fields['captcha_question'].initial = question
            self.fields['captcha_answer'].label = question
            self.fields['captcha_correct_answer'].initial = sha256(str(answer).encode()).hexdigest()
            self.fields['timestamp'].initial = int(time.time())
        else:
            self.fields['captcha_answer'].label = self.data.get('captcha_question')

    def clean_captcha_answer(self):
        answer = self.cleaned_data.get('captcha_answer', '').strip()
        answer_hash = sha256(answer.encode()).hexdigest()
        correct_answer_hash = self.data.get('captcha_correct_answer')

        if answer_hash != correct_answer_hash:
            raise forms.ValidationError("Incorrect CAPTCHA answer.")
        return answer

    def clean(self):
        cleaned_data = super().clean()
        honeypot_value = cleaned_data.get('honeypot')
        timestamp_val = cleaned_data.get('timestamp')

        # | Reject if honeypot is filled
        if honeypot_value:
            raise forms.ValidationError("Spam detected.")

        # | Reject if form is submitted too quickly i.e. within 5 sec
        if timestamp_val and int(time.time()) - int(timestamp_val) < 5:
            raise forms.ValidationError("Form submitted too quickly. Possible bot activity.")

        request = self.request
        if request:
            user_agent = request.META.get('HTTP_USER_AGENT', '')
            referrer = request.META.get('HTTP_REFERER', '')

            # | Check for suspicious or missing User-Agent headers
            if not user_agent or 'bot' in user_agent.lower():
                raise forms.ValidationError("Suspicious activity detected.")

            # | Check for invalid HTTP_REFERER
            if not referrer or qdomain() not in referrer:
                raise forms.ValidationError("Invalid form submission source.")

        return cleaned_data

    @staticmethod
    def get_random_qa():
        def addition_question():
            num1 = random.randint(1, 20)
            num2 = random.randint(1, 20)
            question = f"What is the result of: {num1} {random.choice(['+', 'plus', 'added to'])} {num2} ?"
            answer = num1 + num2
            return question, answer

        def multiplication_question():
            num1 = random.randint(2, 10)
            num2 = random.randint(2, 10)
            question = f"What is the result of: {num1} {random.choice(['*', 'multiplied by', 'multiply with', 'times'])} {num2} ?"
            answer = num1 * num2
            return question, answer

        # def string_question():
        #     rstr = makeid()
        #     rpos = random.randint(1, 8)
        #     question = f"What is the {ordinal(rpos)} character of the string: {rstr} ?"
        #     answer = rstr[rpos - 1]
        #     return question, answer

        def string_question():
            rstr = makeid()
            rpos = random.randint(1, 8)

            styles = [
                (
                    f"What is the {ordinal(rpos)} character of the string: {rstr} ?",
                    rstr[rpos - 1],
                ),
                (
                    f"What is the {ordinal(rpos)} character from the end of the string: {rstr} ?",
                    rstr[-rpos],
                ),
                (
                    f"Write the string in reverse order: {rstr} ",
                    rstr[::-1],
                ),
                (
                    f"What are the first 2 characters of the string: {rstr} ?",
                    rstr[:2],
                ),
                (
                    f"What are the last 2 characters of the string: {rstr} ?",
                    rstr[-2:],
                ),
                (
                    f"Remove the first character and write the remaining string: {rstr} ",
                    rstr[1:],
                ),
                (
                    f"Remove the last character and write the remaining string: {rstr} ",
                    rstr[:-1],
                ),
                (
                    f"Write the characters at odd positions of the string: {rstr} ",
                    rstr[::2],
                ),
                (
                    f"Write the characters at even positions of the string: {rstr} ",
                    rstr[1::2],
                ),
            ]
            question, answer = random.choice(styles)
            return question, answer

        question_types = [addition_question, multiplication_question, string_question]
        selected_question_type = random.choice(question_types)
        return selected_question_type()
