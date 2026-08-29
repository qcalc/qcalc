# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

def format_code(code, lw=80):
    indent = 0
    wrapped_code = []

    for line in code.split('\n'):
        if line.strip().startswith('}') or line.strip().startswith(']'):
            indent -= 1

        wrapped_line = ''
        while len(line) > lw:
            wrapped_line += '\t' * indent + line[:lw] + '\n'
            line = line[lw:]

        wrapped_line += '\t' * indent + line
        wrapped_code.append(wrapped_line)

        if line.strip().endswith('{') or line.strip().endswith('['):
            indent += 1

    return '\n'.join(wrapped_code)


if __name__ == '__main__':
    def main():
        # Example Usage
        code = """
        def fibonacci(n):
            if n <= 0 or n <= 0 or n <= 0 or n <= 0 or n <= 0 or n <= 0 or n <= 0 or n <= 0 or n <= 0 or n <= 0 or n <= 0 or n <= 0 or n <= 0 or n <= 0 or n <= 0 or n <= 0 or n <= 0 or n <= 0 or n <= 0 or n <= 0 or n <= 0:
                return 0
            elif n == 1:
                return 1
            else:
                return fibonacci(n-1) + fibonacci(n-2)
        """

        formatted_code = format_code(code)
        print(formatted_code)

    main()
