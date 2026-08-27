# qCalc field types or annotations

qCalc can automatically generate form fields by inferring their types from the 
initial parameter values. However, annotations can be used to explicitly specify 
the exact field type and provide greater control over the generated form.

A field type can be declared either as a function parameter annotation 
or in the schema's `type` key. The two forms are equivalent. For example:

```python
def func(x: qdate): # parameter 'x' is a 'qdate' type field
    return x
    
def func__info():
    return {
        'title': 'func title'
    }
```
and 

```python

def func(x):
    return x

def func__info():
    return {
        'title': 'func title',
        'schema': {
            'x': {'type': 'qdate'}, # parameter 'x' is a 'qdate' type field
        }
    }
```

both select a date field for parameter `x`. If no annotation is supplied, 
qCalc infers the field type from the **initial value**. When both are supplied, the function 
parameter annotation takes precedence.

```python
# parameter 'x' is a 'qdate' type field because it's initial value string is a date
def func(x='2026-08-27'): 
    return x

def func__info():
    return {
        'title': 'func title',
    }
```

In the annotation table below, there are two types of annotations: Type-1 and Type-2.

* **Type-1:** This type of annotation can be used with or without quotes. 
Using it without quotes is recommended because it can be verified during syntax checking. 
For example: `def func(x: bool)` or `def func(x: 'bool')`.
* **Type-2:** This type of annotation must be enclosed in single or double quotes. 
For example: `def func(x: 'boolean')`.

Some annotations require additional information. These annotations are better specified 
using the schema's `type` key.


```python
def func(x):
    return x

def func__info():
    return {
        'title': 'func title',
        'schema': {
            'x': {'type': 'choice', 'choices':['A','B','C']}, 
        }
    }
```

Below is the alphabetical list of qCalc field types or annotations. 

| Annotation Type-1 | Annotation Type-2          | Description                                                                                                                                                                                                                                                                                   |
|-------------------|----------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `qchar`           | `'char'`                   | Short character input field up to 50 characters                                                                                                                                                                                                                                               |
| `qcode`           | `'codeedit'`               | Source-code editor input field                                                                                                                                                                                                                                                                |
| `qdate`           | `'date'`                   | Date input field                                                                                                                                                                                                                                                                              |
| `qdatetime`       | `'datetime'`               | Date-and-time input field                                                                                                                                                                                                                                                                     |
| `qemail`          | `'email'`                  | Email address input field                                                                                                                                                                                                                                                                     |
| `qfile`           | `'file'`                   | File upload field with a 2 MB limit                                                                                                                                                                                                                                                           |
| `qfl`             |                            | Floating-point short input field                                                                                                                                                                                                                                                              |
| `qfunc`           | `'hidden'`                 | qCalc function field                                                                                                                                                                                                                                                                          |
| `qhide`           |                            | Hidden field, pass the value to function call but do not display the field, e.g. func, __info                                                                                                                                                                                                 |
| `qhtml`           | `'html'`                   | Display output field containing HTML markup                                                                                                                                                                                                                                                   |
| `qimage`          | `'image'`                  | Image upload field with a 2 MB limit                                                                                                                                                                                                                                                          |
| `qin`             |                            | Integer short input field                                                                                                                                                                                                                                                                     |
| `qlist`           |                            | Dynamic list input allowing item addition and deletion. List values can be of type float, int, str, qtexta, or qchar.                                                                                                                                                                         |
| `qpage`           |                            | Display output field containing a page of text                                                                                                                                                                                                                                                |
| `qread`           | `'read'`                   | Read-only text input field up to 50 characters                                                                                                                                                                                                                                                |
| `qregex`          | `'regex'`                  | Regular-expression input field                                                                                                                                                                                                                                                                |
| `qsel2`           | `'select2'`                | Text input field, search and select from drop-down                                                                                                                                                                                                                                            |
| `qtable`          |                            | Editable table input backed by a DataFrame. Not available to front-end calculators                                                                                                                                                                                                            |
| `qtbl`            |                            | Safe table field represented by columns and row data without exposing the DataFrame                                                                                                                                                                                                           |
| `qtext`           | `'text'`                   | Text input field with a 255-character limit                                                                                                                                                                                                                                                   |
| `qtexta`          | `'textarea'`               | Multi-line text input field with a 65535-character limit                                                                                                                                                                                                                                      |
| `qtexte`          | `'textedit'`               | Rich text editor input field with a 65535-character limit                                                                                                                                                                                                                                     |
| `qtime`           | `'time'`                   | Time input field                                                                                                                                                                                                                                                                              |
| `qt`              |                            | Quantity input containing a value and a valid unit using a simple interface. Could be single or multipart quantity input. If explicitly not specified, the default unit selection interface is select2 (improved selection) unless otherwise changed by the global preference setting uom_v2. |
| `qt2`             |                            | Quantity input using the select2 (improved selection) unit interface. Could be single or multipart quantity input. If explicitly not specified, the default unit selection interface is select2 (improved selection) unless otherwise changed by the global preference setting uom_v2.        |
| `qtx`             |                            | Quantity input accepting value and any valid unit                                                                                                                                                                                                                                             |
| `quom`            | `'uom'`                    | Compatible unit input for a specific dimension such as length, weight, or pressure. No search and select drop-down is provided; the unit must be entered manually.                                                                                                                            |
| `quom2`           | `'uom2'`                   | Unit input field, search and select from drop-down. Only compatible units for a specific dimension such as length, weight, or pressure are displayed in the drop-down.                                                                                                                        |
| `quomx`           |                            | Unit input accepting any valid unit such as ft, kg, or m2. No search and select drop-down is provided; the unit must be entered manually.                                                                                                                                                     |
| `qurl`            | `'url'`                    | URL input field up to 255 characters                                                                                                                                                                                                                                                          |
| `qvstr`           |                            | Display output field containing a loop-safe value string                                                                                                                                                                                                                                      |
| `bool`            | `'boolean'`, `'checkbox'`  | Boolean input representing true or false                                                                                                                                                                                              |
| `int`             | `'integer'`                | Whole-number input                                                                                                                                                                                                                    |
| `float`           | `'float'`                  | Floating-point number input                                                                                                                                                                                                           |
| `str`             | `'text'`                   | General text input                                                                                                                                                                                                                    |
|                   | `'choice'`                 | Select one value from a predefined set of choices                                                                                                                                                                                     |
|                   | `'multiplechoice'`         | Select multiple values from a predefined set of choices                                                                                                                                                                               |
|                   | `'checkboxselectmultiple'` | Select multiple values using a group of checkboxes                                                                                                                                                                                    |
|                   | `'radio'`                  | Select one value using a group of radio buttons                                                                                                                                                                                      |
|                   | `'combo'`                  | Select one value from a compact combo box or drop-down list                                                                                                                                                                           |
|                   | `'decimal'`                | Decimal-number input with fixed-point precision                                                                                                                                                                                       |
|                   | `'duration'`               | Duration input representing an amount of elapsed time                                                                                                                                                                                |
|                   | `'filepath'`               | File-path input for a path on the server or selected file system                                                                                                                                                                      |
|                   | `'multivalue'`             | Input for multiple values collected as one field                                                                                                                                                                                     |
|                   | `'nullboolean'`            | Three-state boolean input: true, false, or unset                                                                                                                                                                                     |
|                   | `'range'`                  | Numeric range input with minimum and maximum values                                                                                                                                                                                  |
|                   | `'rchoice'`                | Select one value from choices displayed as a row of radio-style options                                                                                                                                                               |
|                   | `'slug'`                   | Text input for a URL-friendly slug containing letters, numbers, underscores, or hyphens                                                                                                                                              |
|                   | `'uuid'`                   | UUID input for a universally unique identifier                                                                                                                                                                                       |

Use the following code snippets in `mycal` to see how various field types render on a calculator form. 
Copy and paste the snippet into `mycal`, then click **[Format Code]** to automatically generate the 
stub __info() function required to run the test calculator.

```python
def type_text(x: qchar, y: str, z: qtext):
    return {'x': x, 'y': y, 'z': z}
```

```python
def type_code(x: qcode, y: qtexte, z: qtexta):
    return {'x': x, 'y': y, 'z': z}
```

```python
def type_datetime(
        x: qdate = '2026-08-27',
        y: qdatetime = '2026-08-27 16:40',
        z: qtime = '16:40'):
    return {'x': x, 'y': y, 'z': z}
```

Within the __info() function key `schema` you can define the behavior of each parameter/field individually.
To do so you can use the following schema keys:

| Schema key         | Description                                                                                                               |
|--------------------|---------------------------------------------------------------------------------------------------------------------------|
| `'type'`           | Field type/renderer used for the parameter, such as `text`, `date`, `choice`, or other qCalc-specific annotation.         |
| `'required'`       | Whether the user must provide a value before the form can be submitted; blank values are invalid when set to `True`.      |
| `'label'`          | Human-readable label displayed for the field in the form. By default qCalc creates a label from the parameter name itself. |
| `'initial'`        | Default value shown when the field is first rendered or when no value has been entered yet.                               |
| `'help_text'`      | Extra explanatory text shown to the user, an info icon will appear after the field label.                                 |
| `'disabled'`       | If `True`, the field is rendered as non-editable and the user cannot change its value.                                    |
| `'choices'`        | List of valid options for select-style fields; often given as a list of `(value, label)` pairs or simple values.          |

