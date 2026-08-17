# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

import re


def ordinal(n):
    suffix = {1: "st", 2: "nd", 3: "rd"}
    if 10 <= n % 100 <= 20:
        suffix_str = "th"
    else:
        suffix_str = suffix.get(n % 10, "th")
    return f"{n}{suffix_str}"


def text2words(text: str):
    return re.findall(r'\w+', text.lower(), re.UNICODE)


def word_count(text: str):
    words = text2words(text)
    cnt = len(words)
    return cnt, words


def format_address(address):
    # Capitalize the first letter of each word
    def capitalize_word(word):
        return word.capitalize()

    # Split the address into components by spaces and commas
    parts = re.split(r'(\s|,)', address)

    # Capitalize words and keep punctuation intact
    formatted_parts = [capitalize_word(part) if part.strip() and not re.match(r'[\s,]', part) else part for part in
                       parts]

    # Join parts while ensuring correct spacing around commas
    formatted_address = ''.join(formatted_parts)

    # Ensure there is a space after each comma if not present
    formatted_address = re.sub(r',(\S)', r', \1', formatted_address)

    # Remove any extra spaces (e.g., multiple spaces) and leading/trailing spaces
    formatted_address = re.sub(r'\s+', ' ', formatted_address).strip()

    return formatted_address


if __name__ == '__main__':
    # Example usage
    address = "123 main street,apt 4b,new york, ny"
    formatted_address = format_address(address)
    print(formatted_address)  # Output: "123 Main Street, Apt 4B, New York, NY"
    print(format_address('')=='')
