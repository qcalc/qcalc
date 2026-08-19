# qCalc — Dev System Setup Guide

This guide sets up a local qCalc development environment using **SQLite** as the database and **file-based caching** - no PostgreSQL, MySQL, Memcached, or Redis required. Platform-specific instructions are grouped into separate Windows and Linux sections.

The automated scripts `setup/install_qcalc.bat` (Windows) and `setup/install_qcalc.sh` (Linux) perform all steps below. You can run them directly or follow this guide manually.

---

## Windows Setup

The commands in this section are intended for PowerShell or Command Prompt on Windows.

### 1. Prerequisites

a) Install the **Python version manager** (if not already installed):

```powershell
winget install 9NQ7512CXL7T
```

b) Then install Python 3.12:

```powershell
py install 3.12.10
```

Verify:

```powershell
py -3.12 --version
```

---

### 2. Clone the qCalc Repository from Git

Move to directory where you want to clone.

```powershell
git clone https://github.com/qcalc/qcalc.git qcalc_dock
cd qcalc_dock/qcalc
```

---

### 3. Run the Automated Installation Script

From `qcalc_dock/qcalc/`:

```bat
setup\install_qcalc
```

The **script runs steps 4–7 below**. If you prefer to proceed manually, follow those steps instead. Otherwise, proceed to step 8.

---

### 4. Create the Python Virtual Environment

```bat
py -3.12 -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

---

### 5. Create Required Directories

```bat
mkdir ..\.local
mkdir ..\.temp
mkdir .setup
```

---

### 6. Copy Configuration Templates

```bat
copy setup\env\template_setup.env setup.env
copy setup\env\template_dev_sqlite_file.env .setup\dev_sqlite_file.env
copy setup\env\template_gpref.json gpref.json
```

The default `setup.env` points to the SQLite dev environment:

```env
QCALC_SCHEME='http'
QCALC_DOMAIN="127.0.0.1:8000"
QCALC_ENV_FILE=".setup/dev_sqlite_file.env"
DJANGO_SETTINGS_MODULE="config.settings.dev"
```

The default `.setup/dev_sqlite_file.env` uses:

```env
DB_ENGINE="django.db.backends.sqlite3"
DB_NAME="../.local/qcalc.sqlite3"
DEFAULT_CACHE_ALIAS="file"
FILE_UPLOAD_TEMP_DIR="{PROJ_DIR}/.temp/"
```

`{PROJ_DIR}` is automatically replaced with the project root path at runtime.

---

### 7. Initialize Django

Run from `qcalc_dock/qcalc/` with the virtual environment active:

```bat
python manage.py migrate
set DJANGO_SUPERUSER_USERNAME=super
set DJANGO_SUPERUSER_EMAIL=admin@example.com
set DJANGO_SUPERUSER_PASSWORD=super
python manage.py createsuperuser --noinput
python manage.py collectstatic --noinput
```

> The default superuser password is `super`. Change it after the first login at `/admin/`.

---

### 8. Start the Development Server

```bat
python manage.py runserver
```

Open `http://127.0.0.1:8000` in your browser.

---

### 9. Optional: Use MySQL Instead of SQLite

Install the extra build dependencies and the MySQL client:

With the virtual environment active:

```powershell
pip install mysqlclient==2.2.1
```

Create a MySQL database and user, then update `.setup/dev_sqlite_file.env` (or create a new env file):

```env
DB_ENGINE="django.db.backends.mysql"
DB_NAME="qcalc"
DB_USER="qcalc"
DB_PASSWORD="db_user_password"
DB_HOST="127.0.0.1"
DB_PORT="3306"
```

Point `setup.env` at the new env file:

```env
QCALC_ENV_FILE=".setup/dev_mysql.env"
```

### 10. Optional: Rebuild Templates, Themes, and Static Files

Please follow this section if you want to change templates and themes.

qCalc templates are composed from component template files and are built using gulp.
The CSS resources are likewise compiled from Sass sources.
If any template or Sass changes are required, rebuild the generated files using:
```bat
setup/run_gulp.bat
setup/run_sass.bat
```
Then refresh the collected static output with:
```bat
python manage.py collectstatic
```

Required toolchain versions:
- Node 24.18.0
- gulp cli 3.1.0
- saas 1.99.0

---

## Linux Setup

The commands in this section are intended for Ubuntu Linux and a Bash shell.

### 1. Prerequisites

Install Python 3.12, configure the required repository and packages:

```bash
sudo apt update
sudo apt install software-properties-common -y
sudo add-apt-repository ppa:deadsnakes/ppa -y
sudo apt update
sudo apt install python3.12 python3.12-venv python3.12-dev -y
```

Verify:

```bash
python3.12 --version
```

### 2. Clone the Repository

```bash
cd ~
git clone https://github.com/qcalc/qcalc.git qcalc_dock
cd ~/qcalc_dock/qcalc
```

### 3. Run the Automated Installation Script

From `~/qcalc_dock/qcalc/`:

```bash
cp setup/install_qcalc.sh setup/install_qcalc
chmod u+x setup/install_qcalc
bash ./setup/install_qcalc
```

The script runs steps 4-7 below. If you prefer to proceed manually, follow those steps instead. Otherwise, proceed to step 8.

### 4. Create the Python Virtual Environment

From `~/qcalc_dock/qcalc/`:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 5. Create Required Directories

```bash
mkdir -p ~/qcalc_dock/.local
mkdir -p ~/qcalc_dock/.temp
mkdir -p ~/qcalc_dock/qcal/.setup
```

### 6. Copy Configuration Templates

From `~/qcalc_dock/qcalc/`:

```bash
cp setup/env/template_setup.env setup.env
cp setup/env/template_dev_sqlite_file.env .setup/dev_sqlite_file.env
cp setup/env/template_gpref.json gpref.json
```

The default `setup.env` points to the SQLite dev environment:

```env
QCALC_SCHEME='http'
QCALC_DOMAIN="127.0.0.1:8000"
QCALC_ENV_FILE=".setup/dev_sqlite_file.env"
DJANGO_SETTINGS_MODULE="config.settings.dev"
```

The default `.setup/dev_sqlite_file.env` uses:

```env
DB_ENGINE="django.db.backends.sqlite3"
DB_NAME="../.local/qcalc.sqlite3"
DEFAULT_CACHE_ALIAS="file"
FILE_UPLOAD_TEMP_DIR="{PROJ_DIR}/.temp/"
```

`{PROJ_DIR}` is automatically replaced with the project root path at runtime.

### 7. Initialize Django

Run from `qcalc_dock/qcalc/` with the virtual environment active:

```bash
python manage.py migrate
export DJANGO_SUPERUSER_USERNAME=super
export DJANGO_SUPERUSER_EMAIL=admin@example.com
export DJANGO_SUPERUSER_PASSWORD=super
python manage.py createsuperuser --noinput
python manage.py collectstatic --noinput
```

The default superuser password is `super`. Change it after the first login at `/admin/`.

### 8. Start the Development Server

```bash
python manage.py runserver
```

Open `http://127.0.0.1:8000` in your browser.

### 9. Optional: Use MySQL Instead of SQLite

Install the extra build dependencies and the MySQL client:

```bash
sudo apt install build-essential pkg-config libmysqlclient-dev -y
pip install mysqlclient==2.2.1
```

Create a MySQL database and user, then update `.setup/dev_sqlite_file.env` (or create a new env file):

```env
DB_ENGINE="django.db.backends.mysql"
DB_NAME="qcalc"
DB_USER="qcalc"
DB_PASSWORD="db_user_password"
DB_HOST="127.0.0.1"
DB_PORT="3306"
```

Point `setup.env` at the new env file:

```env
QCALC_ENV_FILE=".setup/dev_mysql.env"
```

### 10. Optional: Rebuild Templates, Themes, and Static Files

Follow this section if you want to change templates and themes. The repository currently provides the Gulp and Sass runner files as Windows batch scripts (`setup/run_gulp.bat` and `setup/run_sass.bat`). Run those scripts in a Windows environment, or use the equivalent Node and Sass commands configured by your project on Linux.

Then refresh the collected static output:

```bash
python manage.py collectstatic
```

Required toolchain versions:

- Node 24.18.0
- gulp cli 3.1.0
- sass 1.99.0

---

## Production Deployment notes

Step-by-step production installation guides are provided in the `docs` folder:

- Bare-metal Ubuntu Linux/VPS using Python, Gunicorn, Nginx, PostgreSQL, and Certbot: [qCalc Production Server on Linux](/docs/installation-guide/create-qcalc-prod-server-on-linux.md)
- Docker Compose deployment with Nginx, Certbot, PostgreSQL, and Memcached containers: [qCalc Production Server on Docker](/docs/installation-guide/create-qcalc-prod-server-on-docker.md)

## Directory Layout After Setup

```
qcalc_dock/                        # qCalc PROJECT dir (Git-managed)
├── qcalc/                         # Django project, qCalc ROOT dir
│   ├── .venv/                     # Python virtual environment (not in Git)
│   ├── setup.env                  # Startup configuration (not in Git)
│   ├── .setup/                    # not in Git
│   │   └── dev_sqlite_file.env    # Dev environment variables (not in Git)
│   └── qsite                      # qCalc APP dir
├── qcalc_res/                     # Resource files (docs, help, json, model)
├── .local/                        # not in Git
│   └── qcalc.sqlite3              # SQLite database file
├── .temp/                         # Temporary file uploads, not in Git
└── .cache/                        # Application cache, for file based cacheing
```

---

## Quick Reference

| Task | Windows | Linux |
|------|---------|-------|
| Activate venv | `.venv\Scripts\activate` | `source .venv/bin/activate` |
| Run dev server | `python manage.py runserver` | `python manage.py runserver` |
| Run migrations | `python manage.py migrate` | `python manage.py migrate` |
| Collect static | `python manage.py collectstatic --noinput` | `python manage.py collectstatic --noinput` |
| Open Django shell | `python manage.py shell` | `python manage.py shell` |
