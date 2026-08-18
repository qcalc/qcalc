## IMPORTANT

qCalc is designed to run with a locked set of dependency and asset versions.
These versions are part of the app's compatibility contract:
- the Python packages in requirements.txt are pinned to exact working releases,
- and the static vendor resources already bundled in qcalc/static/vendor match the versions the app expects.
Changing them without a deliberate migration can break templates, JavaScript/CSS behavior,
Django compatibility, and other runtime assumptions.

For any local implementation, do not alter these required versions;
use the project’s stored static assets and pinned dependency list as the authoritative baseline.


## VENDOR JAVASCRIPT AND CSS

Required versions are already locally available and linked to qcalc/static/vendor

**tabulator:**

```html
<link href="https://unpkg.com/tabulator-tables@6.1.0/dist/css/tabulator.min.css" rel="stylesheet">
<script src="https://unpkg.com/tabulator-tables@6.1.0/dist/js/tabulator.min.js"></script>
```

**select2:**

```html
<link href="https://cdn.jsdelivr.net/npm/select2@4.1.0-rc.0/dist/css/select2.min.css" rel="stylesheet">
<script src="https://cdn.jsdelivr.net/npm/select2@4.1.0-rc.0/dist/js/select2.min.js"></script>
```

**intro.js:**

```html
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/intro.js@7.2.0/minified/introjs.min.css">
```

**tingle:**

```html
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/tingle/0.16.0/tingle.min.css">
```

**htmx:**

```html
<script src="https://unpkg.com/htmx.org@1.9.11"></script>
<script src="https://unpkg.com/htmx.org@1.9.11/dist/ext/response-targets.js"></script>
```

**suneditor:**

```html
<link href="https://cdn.jsdelivr.net/npm/suneditor@2.45.1/dist/css/suneditor.min.css" rel="stylesheet">
<script src="https://cdn.jsdelivr.net/npm/suneditor@2.45.1/dist/suneditor.min.js"></script>
```

**codemirror:**

```html
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/codemirror@5.65.5/lib/codemirror.min.css">
<script src="https://cdn.jsdelivr.net/npm/codemirror@5.65.5/mode/htmlmixed/htmlmixed.js"></script>
<script src="https://cdn.jsdelivr.net/npm/codemirror@5.65.5/mode/xml/xml.js"></script>
<script src="https://cdn.jsdelivr.net/npm/codemirror@5.65.5/mode/css/css.js"></script>
<script src="https://cdn.jsdelivr.net/npm/codemirror@5.65.5/mode/python/python.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/codemirror@5.65.5/addon/edit/matchbrackets.min.js"></script>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/codemirror@5.65.5/theme/dracula.min.css">
```

**katex:**

```html
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.11.1/dist/katex.min.css">
<script src="https://cdn.jsdelivr.net/npm/katex@0.11.1/dist/katex.min.js"></script>
```

**google font:** 

roboto (qcalc/static/vendor/fonts/google/)


## CORE SOFTWARE

- Python 3.12.10
- Django 5.0.6
- htmx 1.9.11
- jquery 3.3.1
- bootstrap 4.3.1


## DATABASE SERVER

- if using sqlite: built-in
- if using MySql: version 8.4.3 or above
- if using PostGres: version 16.0 or above

**Note:** 

In principle, a supported database version can be used as-is for a local implementation; however,
if the database version later needs to be upgraded, this must be done with a proper data migration plan
and validation of schema, compatibility, and application behavior before deployment.


## CACHE SERVER

- by default qCalc use a file based cache, for which no cache service is required
- if using Redis: version 6.2.23 or 8.0.1 or above (using protocol=3)
- if using Memcached: version 1.6.8 or above

## OTHERS

- nginx: version 1.31.3
- gunicorn: version 23.0.0

## OPTIONAL 

If you want to change templates and themes.

Required toolchain versions:
- Node 24.18.0
- gulp cli 3.1.0
- saas 1.99.0


## PYTHON DEPENDENCIES

The setup process installs the Python dependencies from "requirements.txt",
which is pinned to the exact library versions required by qCalc.
