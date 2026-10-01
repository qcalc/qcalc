# Mark Down File Reader

## Purpose

This calculator reads Markdown content from one of three sources and renders it as formatted HTML in qCalc.

Use it when you want to quickly preview Markdown from a file, a URL, or pasted text, including code blocks, tables, and math notation.

## Background

### Source mode behavior

The reader has three mutually exclusive modes:

- File: reads uploaded Markdown file content.
- URL: fetches Markdown text from a URL.
- Text: reads Markdown from the text input field.

Only the fields relevant to the selected mode are shown.

## Inputs

- Mode: Select File, URL, or Text. Initial selection is URL.
- Upload Markdown: Used when Mode is File.
- MD URL: Used when Mode is URL.
- Markdown Text: Used when Mode is Text.

## Results

- Rendered Markdown output: The converted HTML rendering of the Markdown source.

## Understanding the Processing

1. Validation by mode:

- URL mode requires a non-empty URL.
- Text mode requires non-empty text.
- File mode requires an uploaded file.

2. Markdown is converted to HTML using qCalc Markdown conversion rules.

3. Math rendering support is enabled


## Example

Example scenario:

- Mode: Text
- Markdown Text:

```text
# Weekly Notes

Total = 42

| Item | Qty |
|---|---|
| A | 2 |
| B | 5 |
```

Expected interpretation:

- The result shows a rendered heading, paragraph, and table rather than raw Markdown syntax.

## Important Assumptions and Interpretation

- URL mode depends on remote availability and network access.
- The calculator renders Markdown as HTML; it is a viewer, not a Markdown linter.
- Mode must be File, URL, or Text; any other value is rejected.
