# Text Statistics

## Purpose

`text_stats()` provides quick content-size metrics from **Text**, **URL**, or **File** input.

It is useful for drafting, SEO prep, and rough LLM prompt sizing.

---

## Input Modes

### Text (default)

Paste content into the `text` field.

### URL

Provide `text_url` (default demo: `demo_url('demo.txt')`).
The calculator fetches page content and analyzes extracted text.

### File

Upload a text file using `upload_text`.

---

## Returned Metrics

- **Character Count**: total characters, including spaces/newlines.
- **Character Count (No Space)**: characters after removing all whitespace.
- **Word Count**: total words from standard word tokenization.
- **Token Estimate**: approximate LLM token count using:

```text
ceil(Character Count (No Space) / 4)
```

---

## Notes

- Token count is an **estimate**, not model-exact.
- For CJK text, emoji-heavy text, or code-heavy text, actual model tokens may differ.
- Empty or invalid input for the selected mode returns a clear validation error.
