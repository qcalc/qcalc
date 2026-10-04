# qCalc API Reference (for calculator authors)

This document summarizes calculator-facing symbols exposed by qCalc, with practical descriptions and examples. You can type `help <symbol>` in cosole to know more about input and output interface of a symbol.

---

## 1) Quantity and Unit APIs

| Symbol | Kind | What it does | Example |
|---|---|---|---|
| `Qty` (alias: `q`) | class | Quantity object with value + unit and unit-aware math | `d = Qty("10 m"); t = Qty("2 s"); v = d / t` |
| `qx`, `qxi` | function | Special Quantity  | `qx("th_hair")`, `qxi("th_hair")` |
| `is_qty`, `is_unit` | function | Checks whether value is quantity/unit | `if is_qty(x): ...` |
| `base_units`, `base_dims`, `prefixes` | data | Built-in unit/dimension dictionaries and prefixes | `base_units["m"]` |
| `unit_desc`, `lmt_desc` | function | Human-readable unit / limit-category description | `unit_desc("kg")` |
| `unit2lmt`, `lmt2cat`, `lmt2ulist`, `lmt2qlist` | function | Unit-category and compatible-unit lookups | `lmt2ulist(unit2lmt("km"))` |
| `find_unit`, `read_unit` | function | Search/resolve unit definitions | `find_unit("meter")` |
| `is_str_qty`, `str_type` | function | Quantity-string check and string type info | `is_str_qty("3.5 kg")` |

---

## 2) Date/Time APIs

| Symbol | Kind | What it does | Example |
|---|---|---|---|
| `QDateTime` (alias: `qdt` in `qlib_dict`) | class | Parse/hold date/time values; supports `+/-` day math and timedelta | `QDateTime("2026-10-04 10:30 UTC+06:00")` |
| `today()` | function | Returns current local date as `QDateTime` | `d = today()` |
| `now(tz=None)` | function | Returns current time as `QDateTime`; accepts `UTC`, `+HHMM`, `+HH:MM`, `UTC+HH:MM` | `now("UTC")`, `now("+06:00")` |
| `spellnow(tz=None)` | function | Returns human-readable current datetime text via `QDateTime.spell()` | `spellnow("UTC")` |

---

## 3) Conditional and CSS-like value helpers

| Symbol | Kind | What it does | Example |
|---|---|---|---|
| `iif` | function | Inline-if helper | `iif(score >= 60, "Pass", "Fail")` |
| `joinx` | function | Join helper for values/strings | `joinx(", ", ["A", "B", "C"])` |
| `css2floats`, `css2ints`, `css2values`, `css2strs`, `vals2css`, `css2set` | function | Convert comma/space separated text to typed values and back | `css2ints("1,2,3")` |

---

## 4) Safe table / dataframe APIs (`qtbl`)

`qtbl` is the safe table type used in qapi:
```python
tbl = {"columns": ["name", "qty"], "data": [["A", 3], ["B", 5]]}
```

| Symbol | Kind | What it does | Example |
|---|---|---|---|
| `qdf(tbl)` | function | Wraps `qtbl` into a safe dataframe facade (limited methods) | `qdf(tbl).sum()` |
| `qcol(tbl, col)` | function | Returns one column by name or index | `qcol(tbl, "qty")` |
| `qrow(tbl, row)` | function | Returns one row by index | `qrow(tbl, 0)` |
| `qsum(values)` | function | Sum numbers and/or quantities safely | `qsum([Qty("2 m"), Qty("30 cm")])` |
| `qadd`, `qsub`, `qmul`, `qdiv` | function | Scalar/list element-wise arithmetic; quantity-aware where possible | `qadd([1,2], 10)` |

---

## 5) NumPy API (restricted)

| Symbol | Kind | What it does | Example |
|---|---|---|---|
| `np` | proxy object | Restricted NumPy surface (safe allowlist only) | `np.sqrt([1,4,9])` |
| `np_names()` | function | Lists exposed `np.<name>` symbols | `np_names()` |

---

## 6) Symbol discovery/help APIs

| Symbol | Kind | What it does | Example |
|---|---|---|---|
| `qtypes()` | function | Lists supported qtype annotation names | `qtypes()` |
| `qmodules()` | function | Lists allowed import modules in safe execution context | `qmodules()` |
| `qsymbols(scope='api', name_filter=None)` | function | Discover available symbols/calculators/units | `qsymbols("api")` |
| `qsymstat()` | function | Count summary by symbol category | `qsymstat()` |
| `qsymhelp(name)` | function | Signature/doc help for one symbol | `qsymhelp("qsum")` |

---

## 7) User/environment helpers

| Symbol | Kind | What it does | Example |
|---|---|---|---|
| `user_name`, `user_process`, `user_ip`, `local_ip` | function | Runtime/user context metadata | `user_name()` |

---

## 8) Link/UI helpers

| Symbol | Kind | What it does | Example |
|---|---|---|---|
| `page_link`, `calurl`, `cal_link`, `command_button`, `addcal_button` | function | Build calculator/page links and action buttons | `cal_link("my_calc", "Open")` |

---

## 9) File / image / visualization classes

| Symbol | Kind | What it does | Example |
|---|---|---|---|
| `QFile`, `qf2bio` | class/function | File wrapper and conversion to bytes stream | `bio = qf2bio(my_file)` |
| `QImage`, `qf2img`, `nparray_to_bio` | class/function | Image utilities and conversions | `img = qf2img(my_file)` |
| `QChart` | class | Chart object for calculator output | `chart = QChart(...)` |
| `QGeo`, `QMap` | class | Geo/map output helpers | `m = QMap(...)` |
| `SmartCalc` | class | Smart calculation helper engine | `sc = SmartCalc()` |
| `dd_list`, `DotDict` (aliases: `dd`) | function/class | Dict convenience helpers / dot-access dict | `cfg = DotDict({"x": 1}); cfg.x` |

---

## 10) qtype annotations (input/output schema types)

These are classes used in calculator function signatures to define UI input/output fields.

### 10.1 Text, number, and basic input types

`qchar`, `qfl`, `qin`, `qdate`, `qdatetime`, `qemail`, `qtext`, `qtexta`, `qtexte`, `qcode`, `qtime`, `qurl`, `qregex`, `qread`

Example:
```python
def bmi(weight: qfl, height_cm: qfl, note: qtexta = ""):
    ...
```

### 10.2 Hidden and function/meta fields

`qfunc`, `qhide`, `qhidex`

Example:
```python
def my_calc(op: qfunc, token: qhide = "", internal: qhidex = ""):
    ...
```

### 10.3 Units and quantities

`quom`, `quomx`, `quom2`, `qtx`, `qt`, `qt2`, `qtc`, `qtc2`

Example:
```python
def convert(value: qt, target_uom: quom2):
    ...
```

### 10.4 Collection and table types

`qlist`, `qdict`, `qtbl`

Example:
```python
def totals(rows: qtbl):
    return qsum(qcol(rows, "amount"))
```

### 10.5 File/image input

`qfile`, `qimage`

Example:
```python
def upload_photo(photo: qimage):
    img = qf2img(photo)
    ...
```

### 10.6 Display/output-oriented types

`qhtml`, `qvstr`, `qpage`

Example:
```python
def hello(name: qchar) -> qpage:
    return qpage(f"Hello, {name}")
```

---

## 11) Small utility

| Symbol | Kind | What it does | Example |
|---|---|---|---|
| `minimum(*args, key=None)` | function | Local alias to Python `min` (to avoid conflicts with minute unit `min`) | `minimum([5, 2, 9])` |

