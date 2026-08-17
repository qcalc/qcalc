# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

def kaprekar_steps__info():
    return {
        'title': "Calculates the Steps to reach Kaprekar's constant (6174)"
    }


def kaprekar_steps(number: int = 2783):
    KAPREKAR_CONSTANT = 6174

    # Check if the number is a repdigit
    num_str = f"{number:04d}"  # Ensure it's 4 digits by padding with zeros if needed
    if len(set(num_str)) == 1:  # Check if all digits are the same
        return [f"{number} is a repdigit, no Kaprekar routine possible."]
    if number < 0 or number > 9998:
        return [f"Number should be between 0 and 9998"]

    steps = []
    while number != KAPREKAR_CONSTANT:
        num_str = f"{number:04d}"
        ascending = int("".join(sorted(num_str)))
        descending = int("".join(sorted(num_str, reverse=True)))
        number = descending - ascending
        steps.append(f"{descending:04d} – {ascending:04d} = {number:04d}")

    return steps


if __name__ == '__main__':
    steps = kaprekar_steps(1459)
    for step in steps:
        print(step)
    steps = kaprekar_steps(1)
    for step in steps:
        print(step)
