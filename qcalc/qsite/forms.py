# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

# forms.py
from django import forms
import random
from qutil import makeid, ordinal, qdomain
from hashlib import sha256
import time


class ContactForm(forms.Form):
    name = forms.CharField(max_length=100, required=True,
                             widget=forms.TextInput(attrs={"placeholder": "Enter your name please"}))
    email = forms.EmailField(required=True,
                             widget=forms.EmailInput(attrs={"placeholder": "Enter your email address please"}))
    subject = forms.CharField(max_length=100, required=True)
    message = forms.CharField(widget=forms.Textarea, required=True)

    # | CAPTCHA fields
    captcha_question = forms.CharField(widget=forms.HiddenInput)
    captcha_answer = forms.CharField(required=True)
    captcha_correct_answer = forms.CharField(widget=forms.HiddenInput)

    # | A Honeypot is a hidden field that humans won’t fill out, but bots often do
    honeypot = forms.CharField(required=False, widget=forms.HiddenInput)
    # | Time-Based Validation
    timestamp = forms.IntegerField(widget=forms.HiddenInput)

    def __init__(self, request, *args, **kwargs):
        is_post = kwargs.pop('post', False)
        self.request = request
        super().__init__(*args, **kwargs)

        if not is_post:
            question, answer = self.get_random_qa()
            self.fields['captcha_question'].initial = question
            self.fields['captcha_answer'].label = question
            self.fields['captcha_correct_answer'].initial = sha256(str(answer).encode()).hexdigest() # answer
            self.fields['timestamp'].initial = int(time.time())
        else:
            self.fields['captcha_answer'].label = self.data.get('captcha_question')

    def clean(self):
        cleaned_data = super().clean()
        honeypot_value = cleaned_data.get('honeypot')
        timestamp = int(cleaned_data.get('timestamp'))

        # | Reject if honeypot is filled
        if honeypot_value:
            raise forms.ValidationError("Spam detected.")

        # | Reject if form is submitted too quickly i.e. within 5 sec
        if timestamp and int(time.time()) - timestamp < 5:
            # print('t', int(time.time()) - timestamp)
            raise forms.ValidationError("Form submitted too quickly. Possible bot activity.")

        request = self.request
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        referrer = request.META.get('HTTP_REFERER', '')

        # | Check for suspicious or missing User-Agent headers
        if not user_agent or 'bot' in user_agent.lower():
            raise forms.ValidationError("Suspicious activity detected.")

        # | Check for invalid HTTP_REFERER
        if not referrer or qdomain() not in referrer:
            raise forms.ValidationError("Invalid form submission source.")

    @staticmethod
    def get_random_qa():
        def addition_question():
            num1 = random.randint(1, 20)
            num2 = random.randint(1, 20)
            question = (f"What is the result of: "
                        f"{num1} {random.choice(['+', 'plus', 'added to'])} {num2}?")
            answer = num1 + num2
            return question, answer

        def multiplication_question():
            num1 = random.randint(1, 10)
            num2 = random.randint(1, 10)
            question = (f"What is the result of: "
                        f"{num1} {random.choice(['*', 'multiplied by', 'multiply with', 'times'])} {num2}?")
            answer = num1 * num2
            return question, answer

        def string_question():
            rstr = makeid()
            rpos = random.randint(1, 8)
            question = f"What is the {ordinal(rpos)} character of the string: {rstr} ?"
            answer = rstr[rpos-1]
            return question, answer

        question_types = [addition_question, multiplication_question, string_question]
        selected_question_type = random.choice(question_types)
        return selected_question_type()

    def clean_captcha_answer(self):
        answer = self.cleaned_data.get('captcha_answer').strip()
        answer_hash = sha256(answer.encode()).hexdigest()
        correct_answer_hash = self.data.get('captcha_correct_answer')
        # | reject if CAPTCHA is not correctl
        if answer_hash != correct_answer_hash:
            raise forms.ValidationError("Incorrect CAPTCHA answer.")

        return answer
