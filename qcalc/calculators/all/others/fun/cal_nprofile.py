# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

import sympy
from qcore import QScreen


def ones_to_words(n):
    return ["", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine"][n]


def teens_to_words(n):
    return ["ten", "eleven", "twelve", "thirteen", "fourteen", "fifteen",
            "sixteen", "seventeen", "eighteen", "nineteen"][n - 10]


def tens_to_words(n):
    return ["", "", "twenty", "thirty", "forty", "fifty",
            "sixty", "seventy", "eighty", "ninety"][n]


def hundreds_to_words(n):
    if n == 0:
        return ""
    elif n < 10:
        return ones_to_words(n)
    elif n < 20:
        return teens_to_words(n)
    elif n < 100:
        return tens_to_words(n // 10) + (
            "-" + ones_to_words(n % 10) if n % 10 != 0 else "")
    else:
        return ones_to_words(n // 100) + " hundred" + (
            " " + hundreds_to_words(n % 100) if n % 100 != 0 else "")


def chunk_to_words(n):
    if n == 0:
        return ""
    elif n < 1000:
        return hundreds_to_words(n)
    else:
        raise ValueError("Chunk value should be less than 1000")


def number_to_words(n):
    if n == 0:
        return "zero"

    large_numbers = [
        (10 ** 12, "trillion"),
        (10 ** 9, "billion"),
        (10 ** 6, "million"),
        (10 ** 3, "thousand"),
        (1, "")
    ]

    words = []
    for value, name in large_numbers:
        if n >= value:
            words.append(chunk_to_words(n // value))
            if name:
                words.append(name)
            n %= value

    return " ".join(words).strip()


class QNumber:
    def __init__(self, number: int):
        self.number = number

    def number_to_words(self):
        return number_to_words(self.number)

    def ordinal_suffix(self):
        if 10 <= self.number % 100 <= 20:
            return 'th'
        else:
            return {1: 'st', 2: 'nd', 3: 'rd'}.get(self.number % 10, 'th')

    def number_to_ordinal(self):
        return f"{self.format_with_commas()}{self.ordinal_suffix()}"

    def ordinal_words(self):
        words = self.number_to_words()
        return words[:-1] + "ieth" if words.endswith("y") else words + self.ordinal_suffix()

    def base_n(self, base, numerals="0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"):
        num = self.number
        if num == 0:
            return numerals[0]
        result = ""
        while num:
            result = numerals[num % base] + result
            num //= base
        return result

    def get_cardinal(self):
        return self.number_to_words()

    def get_ordinal(self):
        ordinal_number = self.number_to_ordinal()
        ordinal_word = self.ordinal_words()
        return f"{ordinal_number} ({ordinal_word})"

    def get_factorization(self):
        factors = sympy.factorint(self.number)
        return " × ".join(
            f"{factor}^{exponent}" if exponent > 1 else f"{factor}" for factor, exponent in factors.items())

    def get_divisors(self):
        divisors = sorted(sympy.divisors(self.number))
        return ", ".join(map(str, divisors))

    def get_greek_numeral(self):
        num = self.number
        if num > 9999:
            return "Sorry, Number > 9999"
        greek_dict = {
            1: 'Α', 2: 'Β', 3: 'Γ', 4: 'Δ', 5: 'Ε', 6: 'Ϛ', 7: 'Ζ', 8: 'Η', 9: 'Θ',
            10: 'Ι', 20: 'Κ', 30: 'Λ', 40: 'Μ', 50: 'Ν', 60: 'Ξ', 70: 'Ο', 80: 'Π', 90: 'Ϙ',
            100: 'Ρ', 200: 'Σ', 300: 'Τ', 400: 'Υ', 500: 'Φ', 600: 'Χ', 700: 'Ψ', 800: 'Ω', 900: 'ϡ'
        }
        result = []
        for value, symbol in sorted(greek_dict.items(), reverse=True):
            while num >= value:
                result.append(symbol)
                num -= value
        return "".join(result) + '´'

    def get_roman_numeral(self):
        num = self.number
        if num > 9999999:
            return "Sorry, Number > 9,999,999"
        roman_dict = {
            1000000: "M̄", 900000: "C̄M̄", 500000: "D̄", 400000: "C̄D̄", 100000: "C̄",
            90000: "X̄C̄", 50000: "L̄", 40000: "X̄L̄", 10000: "X̄", 9000: "ĪX̄",
            5000: "V̄", 4000: "ĪV̄", 1000: "M", 900: "CM", 500: "D", 400: "CD",
            100: "C", 90: "XC", 50: "L", 40: "XL", 10: "X", 9: "IX", 5: "V",
            4: "IV", 1: "I"
        }
        result = []
        for value, numeral in roman_dict.items():
            while num >= value:
                result.append(numeral)
                num -= value
        return "".join(result)

    def get_binary(self):
        return bin(self.number)[2:]

    def get_ternary(self):
        num = self.number
        ternary = ""
        while num:
            ternary = str(num % 3) + ternary
            num //= 3
        return ternary

    def get_senary(self):
        return self.base_n(6)

    def get_octal(self):
        return oct(self.number)[2:]

    def get_duodecimal(self):
        return self.base_n(12)

    def get_hexadecimal(self):
        return hex(self.number)[2:].upper()

    def number_profile(self):
        output = {
            'Number': self.format_with_commas(),
            'Cardinal': self.get_cardinal(),
            'Ordinal': self.get_ordinal(),
            'Factorization': self.get_factorization(),
            'Divisors': self.get_divisors(),
            'Greek numeral': self.get_greek_numeral(),
            'Roman numeral': self.get_roman_numeral(),
            'Binary': self.get_binary(),
            'Ternary': self.get_ternary(),
            'Senary': self.get_senary(),
            'Octal': self.get_octal(),
            'Duodecimal': self.get_duodecimal(),
            'Hexadecimal': self.get_hexadecimal(),
        }
        return output

    def format_with_commas(self):
        return "{:,}".format(self.number)

def number_profile__info():
    return {
        'title': 'Calculate Profile of an Integer Number'
    }


def number_profile(number: int = 6174):
    qnum = QNumber(number)
    out = QScreen()
    prof = qnum.number_profile()
    for key, val in prof.items():
        out.write(f'{key}: {val}')
    return out.flush()


if __name__ == '__main__':
    qn = QNumber(99999999)
    print(qn.number_profile())
    print(number_to_words(
        123456789012))  # "one hundred twenty-three billion four hundred fifty-six million seven hundred eighty-nine thousand twelve"
    print(number_to_words(1001000))  # "one million one thousand"
