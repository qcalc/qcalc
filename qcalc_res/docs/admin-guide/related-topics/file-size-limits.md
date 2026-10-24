## File Size Limits
<!-- TOC -->
  * [File Size Limits](#file-size-limits)
    * [a. How the limits fit together](#a-how-the-limits-fit-together)
    * [b. Settings you can change](#b-settings-you-can-change)
    * [c. Changing the limits](#c-changing-the-limits)
    * [d. What users see](#d-what-users-see)
    * [e. Per-calculator limits](#e-per-calculator-limits)
    * [f. Troubleshooting](#f-troubleshooting)
<!-- TOC -->

qCalc limits file sizes at several layers. They are separate settings, but they must agree with each other.
This page explains what each limit does, where it is configured, and which values to change together.

### a. How the limits fit together

A file reaches qCalc in one of two ways: the user uploads it from the browser, or the user gives a URL and the
server downloads it. Both are checked.

| Layer | Setting | Default | What it limits |
|---|---|---|---|
| nginx | `client_max_body_size` | 50 MB | The whole upload request, files included. The hard cap: a larger request is rejected with *413 Request Entity Too Large* before it reaches qCalc. |
| Django | `DATA_UPLOAD_MAX_MEMORY_SIZE` | 40 MB | Non-file form data only (for example a large table). Uploaded files are **not** counted. Normally left unchanged. |
| qCalc, per file | `QCALC_MAX_FILE_MB` | 10 MB | The default size of one uploaded file. Also the size cap for files downloaded from a URL. |
| qCalc, per file | `QCALC_MAX_FILE_MB_CEILING` | 45 MB | The largest limit a calculator field may ask for. A field asking for more is reduced to this value. |
| Browser | `data-max-mb` on the file input | follows the field limit | Early check in the page, so users get a message before a large upload starts. It is a convenience only; the server always checks again. |

Keep this order:

```text
QCALC_MAX_FILE_MB  <=  QCALC_MAX_FILE_MB_CEILING  <  nginx client_max_body_size
```

Leave a few MB of headroom between the ceiling and the nginx limit, because the request also carries form fields and
multipart overhead. The defaults (45 MB and 50 MB) follow this rule.

### b. Settings you can change

Add these to the environment file used by your installation (`.setup/prod.env` for production). Both are optional.
The values are in MB and may be decimals.

```env
QCALC_MAX_FILE_MB="10"
QCALC_MAX_FILE_MB_CEILING="45"
```

`setup/env/template_all_env_settings.env` lists them with the other optional settings.

The nginx limit is not read from qCalc's environment. It is set in the `http` block of `nginx.conf`
(Docker installs: `.local/nginx/nginx.conf`, copied from `setup/nginx/template_nginx.conf-common.conf`):

```nginx
client_max_body_size 50M;
```

### c. Changing the limits

**To allow larger files everywhere** (for example 20 MB):

1. In `prod.env`, set `QCALC_MAX_FILE_MB="20"`. The ceiling (45) already allows this.
2. Restart qCalc.

**To allow a larger limit than the ceiling** (for example 80 MB):

1. In nginx, raise `client_max_body_size` first, for example to `90M`.
2. In `prod.env`, set `QCALC_MAX_FILE_MB_CEILING="85"` and, if you want it as the new default, `QCALC_MAX_FILE_MB`.
3. Reload nginx and restart qCalc.
4. Check that the server has enough free disk space in `FILE_UPLOAD_TEMP_DIR`, and enough memory. Uploaded files are first
   written to that folder, and some calculators load the whole file into memory.

Apply the changes:

```bash
# Docker installation
docker compose restart nginx qcalc

# Dockerless installation
sudo nginx -t && sudo systemctl reload nginx
sudo systemctl restart qcalc        # or the name of your gunicorn service
```

If you raise a qCalc limit but not nginx, uploads between the two values fail with a 413 error from nginx.
If you lower the nginx limit below the qCalc limit, nginx will reject files that qCalc would have accepted.

### d. What users see

| Situation | Result |
|---|---|
| File larger than the field limit | The browser shows "File size must be less than N MB" and clears the selection. If it is bypassed, the form shows "The maximum file size that can be uploaded is N MB". |
| Request larger than nginx's limit | A plain *413 Request Entity Too Large* page from nginx. This usually means the nginx value is lower than the qCalc one. |
| URL download larger than `QCALC_MAX_FILE_MB` | The calculator shows an error such as "remote file too large". |

### e. Per-calculator limits

A calculator can ask for its own limit by setting `max_mb` on a file or image field, for example `'max_mb': '5'` for an
image-processing calculator. That value replaces `QCALC_MAX_FILE_MB` for that field only, and cannot go above
`QCALC_MAX_FILE_MB_CEILING`. Fields without `max_mb` use `QCALC_MAX_FILE_MB`. Calculator authors do not need to add any
browser code; the page picks up the limit automatically.

### f. Troubleshooting

| Symptom | Likely cause and fix |
|---|---|
| Browser says the file is too large, but you raised the limit | The environment change was not loaded. Restart qCalc and hard-refresh the page (the page may be cached). |
| nginx 413 error for files that should be accepted | `client_max_body_size` is lower than the qCalc limit. Raise it and reload nginx. |
| Limit does not go above 45 MB | `QCALC_MAX_FILE_MB_CEILING` is capping it. Raise the ceiling (and nginx). |
| Large file works from URL but not from upload, or the reverse | The two use the same `QCALC_MAX_FILE_MB`, so check for a per-field `max_mb` on that calculator, or the nginx limit. |
| Large table input is rejected | That is `DATA_UPLOAD_MAX_MEMORY_SIZE` (40 MB, set in `config/settings/base.py`), not a file limit. |

---
