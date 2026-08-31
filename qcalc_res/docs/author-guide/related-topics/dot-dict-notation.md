# qCalc DotDict notation: Using `dd()` in `__info()`
<!-- TOC -->
* [qCalc DotDict notation: Using `dd()` in `__info()`](#qcalc-dotdict-notation-using-dd-in-__info)
  * [1. Without `dd()`](#1-without-dd)
  * [2. With `dd()`](#2-with-dd)
  * [3. The basic idea](#3-the-basic-idea)
    * [3.1 Use `dd()` for groups of settings](#31-use-dd-for-groups-of-settings)
    * [3.2 Simple values need no `dd()`](#32-simple-values-need-no-dd)
    * [3.2 A useful rule](#32-a-useful-rule)
<!-- TOC -->
The `__info()` function defines information and configuration for a calculator.

qCalc provides `dd()` (`DotDict`) so that you can write this information using **dot notation**, without repeatedly creating dictionaries with `{}`.

## 1. Without `dd()`

A typical `__info()` function can become difficult to read because nested dictionaries require many braces:

```python
def wall_paint2__info():
    return {
        'title': 'Paint Required for a Wall v2',
        'calculate': 'Estimate',
        'schema': {
            'brand': {
                'type': 'choice',
                'choices': ['standard', 'premium'],
                'initial': 'standard',
            },
            'coverage': {'attrs': {'readonly': True}},
            'tin_size': {'attrs': {'readonly': True}},
            'coats': {
                'type': 'choice',
                'choices': [1, 2],
                'initial': 2,
            },
        },
        'autofill': {
            'brand': {
                'fields': ['coverage', 'tin_size'],
                'values': {
                    'standard': ['350', '1.0'],
                    'premium': ['600', '1.5'],
                },
            },
        },
        'tags': 'home, painting, estimation',
    }
```

## 2. With `dd()`

The same information can be written more naturally:

```python
def wall_paint3__info():
    d = dd()

    d.title = 'Paint Required for a Wall v2'
    d.calculate = 'Estimate'

    d.schema.brand = dd(
        type='choice',
        choices=['standard', 'premium'],
        initial='standard',
    )

    d.schema.coverage.attrs = dd(
        readonly=True,
    )

    d.schema.tin_size.attrs = dd(
        readonly=True,
    )

    d.schema.coats = dd(
        type='choice',
        choices=[1, 2],
        initial=2,
    )

    d.autofill.brand = dd(
        fields=['coverage', 'tin_size'],
        values=dd(
            standard=['350', '1.0'],
            premium=['600', '1.5'],
        ),
    )

    d.tags = 'home, painting, estimation'

    return d
```

## 3. The basic idea

A dictionary key such as:

```python
'schema'
```

becomes an attribute:

```python
d.schema
```

A nested key such as:

```python
'schema': {
    'brand': ...
}
```

becomes:

```python
d.schema.brand = ...
```

Missing intermediate sections are created automatically. Therefore, you can write:

```python
d.schema.coverage.attrs = dd(
    readonly=True,
)
```

without first creating `schema`, `coverage`, or `attrs`.

### 3.1 Use `dd()` for groups of settings

When several values belong together, use `dd()`:

```python
d.schema.coats = dd(
    type='choice',
    choices=[1, 2],
    initial=2,
)
```

For deeper structures, `dd()` can be nested:

```python
d.autofill.brand = dd(
    fields=['coverage', 'tin_size'],
    values=dd(
        standard=['350', '1.0'],
        premium=['600', '1.5'],
    ),
)
```

### 3.2 Simple values need no `dd()`

For individual values, simply assign them:

```python
d.title = 'Paint Required for a Wall v2'
d.calculate = 'Estimate'
d.tags = 'home, painting, estimation'
```

### 3.2 A useful rule

**Use dot notation for the structure; use `dd()` for grouped values.**

For example:

```python
d.schema.brand = dd(
    type='choice',
    choices=['standard', 'premium'],
    initial='standard',
)
```

is generally cleaner than manually constructing the equivalent nested dictionaries.

`dd()` produces a dictionary, so qCalc can use the returned value (`return d`) in the same way as a normal dictionary.
