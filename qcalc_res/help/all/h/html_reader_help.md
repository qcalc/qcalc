# HTML Reader

## Purpose

This calculator reads HTML from a file, URL, or text input and displays it in qCalc.

It can optionally strip tags and return plain extracted text for quick content reading.

## Background

### Display vs convert-to-text mode

By default, the calculator returns HTML content for display. When Convert to Text is enabled, it removes style and script blocks and returns visible text extracted from the document.

## Inputs

- Mode: Select File, URL, or Text. Initial selection is URL.
- Upload HTML: Used when Mode is File.
- HTML URL: Used when Mode is URL.
- HTML Text: Used when Mode is Text.
- Convert to Text: If enabled, removes tags and returns stripped text instead of HTML.

## Results

- HTML output or text output, depending on Convert to Text.

## Understanding the Processing

1. Validation by mode:

- URL mode requires a non-empty URL.
- Text mode requires non-empty text.
- File mode requires an uploaded HTML file.

2. Source content is loaded.
3. If Convert to Text is true:

- HTML is parsed.
- style and script elements are removed.
- Remaining visible text is returned.

4. Otherwise, original HTML content is returned for display.

## Example

Example scenario:

- Mode: URL
- HTML URL: a page URL
- Convert to Text: true

Expected interpretation:

- Output is readable plain text extracted from the page, not rendered HTML layout.

## Important Assumptions and Interpretation

- URL mode depends on remote availability and network access.
- Convert-to-text output is extracted text, not a semantic summary.
