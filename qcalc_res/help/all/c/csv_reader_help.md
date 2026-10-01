# CSV Reader

## Purpose

This calculator loads CSV data from either an uploaded file or a URL and returns it as a table.

Use it to inspect CSV content quickly inside qCalc before further analysis or downstream processing.

## Background

### File vs URL source

The reader supports two source modes:

- File: reads the uploaded CSV file buffer.
- URL: fetches and parses CSV content from a URL.

Only fields relevant to the selected mode are shown.

- URL mode requires a non-empty URL.
- File mode requires an uploaded CSV file.

## Inputs

- Mode: Select File or URL. Initial selection is URL.
- Upload CSV: Used when Mode is File.
- CSV URL: Used when Mode is URL.
- Quoting: CSV quoting behavior passed to the parser. Choices are Minimal, All, Non-Numeric, None, and Remove Anyway.
- Delimiter: Column separator used when parsing CSV rows.

## Results

- table: Parsed CSV as a tabular output.

## Important Assumptions and Interpretation

- Parsing quality depends on correct delimiter and quoting settings for your data source.
- URL mode depends on network access and source availability.
