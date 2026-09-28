# Calculator Field Naming

This note describes the field-naming (function arguement naming) limits and conventions that matter when writing qCalc calculator functions.

## Why field names matter

Field names are not just labels. They are used to:

- build DOM ids and input names
- match tab blocks and layout groups
- identify generated child fields such as quantity parts and unit fields
- drive `autofill`, `related`, `showhide`, and `anyof` behavior

That means a field name that looks unique in the Python signature may be treated as a different root name in the UI.

## Tokens defined in `qconst.py`

These constants are part of the current naming contract:

- `TOK_ID_PREFIX = 'id_'`
- `TOK_FIELD_SEP = '_'`
- `TOK_UOM = '_uom'`
- `TOK_PART = '_part'`
- `TOK_PART_UOM = '_part_uom'`
- `TOK_ROW = '_row'`
- `TOK_COL = '_col'`
- `TOK_TABLE_UPDATE = '_table_update'`
- `TOK_TABLE_RESIZE = '_table_resize'`
- `TOK_TABLE_ED = '_table_ed'`
- `TOK_RESULT_SUFFIX = '__r'`
- `TOK_LIST_INDEX_PATTERN = r'_\d+$'` i.e. names ending with _<digit> e.g. _1, _2, _10 etc.

The important takeaway is that several suffixes are already reserved by the framework. Field names that end with one of these fragments can be interpreted as generated internal names.

## Practical limitations for authors

1. Avoid field names that end in an index-style suffix such as `_1`, `_2`, `_10`.
2. Avoid using `_uom`, `_part`, or `_part_uom` in your own field names.
3. Avoid `__r` at the end of user-facing input names because it is reserved for result naming.

## Safe naming guidelines

Good names are semantic and stable:

- `brand_choice`
- `mode_choice`
- `coverage_low`
- `coverage_mid`
- `coverage_high`

Avoid names that depend on implicit suffix stripping:

- `select_1`
- `select_2`
- `auto_fill_11`
- `auto_fill_21`

If you want repeated groups, prefer descriptive names over numeric suffixes, or define a separate naming scheme that is consistently handled everywhere.

## If you want to change the convention

It is possible to change the convention cleanly, but it is a coordinated refactor, not a single constant edit.

At minimum, review and update:

- `qconst.py`
- `calc/templatetags/qfilter.py`
- `calc/mod_layout_dynamic.py`
- `calc/templates/layout-render-block.html`
- `calc/view_form_data.py`
- relevant JavaScript helpers under `calc/static/calc/js/`
- tests that assert field-root behavior

## Rule of thumb

Keep field name free of framework suffix patterns.
