# qCalc

qCalc is a Python and Django based web application for calculators, unit conversion, and interactive computation. It supports personal calculators, public catalog browsing, calculator variants and examples, favorites, and rich outputs such as tables, charts, maps, and images.

## Feature summary

- Browse and search a public **catalog of calculators**. Search and directory navigation make it easier to find calculators.
- qCalc calculators are **unit-aware by design**, allowing calculations to be performed naturally with physical quantities. Automatic unit conversion and dimensional consistency make them ideal for everything from simple arithmetic to advanced business, scientific and engineering computations.
- Create and manage **personal calculators and favorites**. Define your calculator as a Python function directly from the app interface, and qCalc automatically generates the corresponding input form and user interface.
- Create and maintain help pages with the **built-in documentation editor**. Write, edit, and manage help documentation directly within qCalc.
- **Your server. Your calculators. Your rules.** Host qCalc on your own infrastructure, create custom calculators either in the back end or entirely from the front end, and tailor the platform to your needs without being limited to the built-in collection.
- Use calculator **variants and examples** to compare or reuse calculations.
- **Share calculators** and calculations easily through links and access tokens.
- Work with **richer inputs and outputs**, including tables, charts, maps, and images.
- Enjoy a smoother experience with **better stability**, faster loading, and fewer UI bugs.
- Get **guided help** through a quick-start tour and improved documentation.
- **Fully responsive** and mobile-friendly, although a desktop is recommended for the best experience.
- Powerful. Extensible. Free! qCalc is **open sourced** and MIT Licensed. Everything you've seen is completely free.

## Overview

This repository contains the qCalc application together with local development and deployment helpers under the setup folder. The project is designed to run as a Django web app with a SQLite-based development setup by default.

## Requirements

Before installing qCalc, make sure you have:

- Python 3.12
- Git
- A terminal with access to the repository

For non-SQLite deployments, the setup scripts also mention optional support for MySQL, Redis, and Memcached.

## Quick start

For a full step-by-step walkthrough covering Python installation, optional database and cache choices, and all configuration files, refer to the following guides:

1. [Set Up qCalc Development System](qcalc_res/docs/installation-guide/create-qcalc-dev-system.md)
   - Recommended for a quick development environment or a setup intended for a small number of users.

2. [Set Up qCalc Production Server on Docker](qcalc_res/docs/installation-guide/create-qcalc-prod-server-on-docker.md)
   - Recommended for a public-facing website, where Docker provides better isolation and security.

3. [Set Up qCalc Production Server on Linux](qcalc_res/docs/installation-guide/create-qcalc-prod-server-on-linux.md)
   - Suitable for a local production deployment without Docker.
   
The installer will:

- create a Python virtual environment in `.venv`
- install dependencies from `requirements.txt`
- create local configuration files under `.setup`
- copy the default environment templates from `setup/env`
- run database migrations
- create a default superuser account
- collect static files

## Configuration

The installation scripts create the following important files:

- `setup.env` from `setup/env/template_setup.env`
- `.setup/dev_sqlite_file.env` from `setup/env/template_dev_sqlite_file.env`
- `gpref.json` from `setup/env/template_gpref.json`

These files hold the base environment and Django settings for development. During startup, qCalc first reads `setup.env`, which points to the active environment file. In a typical local setup, that environment file lives in the `.setup` folder and contains the server-specific values used by Django. You can create your own copy of the relevant template from `setup/env` and place it in `.setup` so it is preserved locally and not overwritten by future updates.

The main environment template is `setup/env/template_all_env_settings.env`. It documents the common startup variables, including:

- `ROBOTS_TXT` for the robots file to use
- `DJANGO_DEBUG` and `DJANGO_SECRET_KEY` for Django runtime settings
- `DB_ENGINE`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, and `DB_PORT` for database selection
- `DEFAULT_CACHE_ALIAS` and related cache settings such as Redis or Memcached
- `FILE_UPLOAD_TEMP_DIR`, `JSON_FILES_DIR`, `HELP_FILES_DIR`, `DOCS_FILE_DIR` and `AI_MODELS_DIR` for local data folders
- API keys and URLs for currency, and other services
- `DJANGO_EMAIL_BACKEND` for email handling in development or production

For local development, a copy of the relevant template under `.setup` is usually the best approach, while `setup.env` remains the small entry point that selects the active environment file.

## Dependency and static asset management

qCalc relies on a defined set of Python packages and frontend static assets, and the project keeps their versions intentionally controlled. The repository documents the expected package requirements in `requirements.txt`, `req_extra_dev.txt`, `req_database.txt`, and `versions_required.txt`, so the environment should be installed with the documented versions rather than relying on whatever happens to be available in the current Python environment. This helps keep the app stable across development, testing, and deployment.

All external JavaScript and CSS dependencies used by the UI are also stored locally under `qcalc/static`, with the correct versions of each package preserved in the repository. This makes qCalc more self-contained and reduces the risk of breakage caused by upstream CDN or package changes, while also improving reproducibility and long-term stability.

## Default development credentials

The installer creates a default superuser account:

- username: `super`
- password: `super`

It is recommended that you change the password after the first login.

## Useful development commands

```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py collectstatic --noinput
python manage.py runserver
```

## Screenshots

Screenshots will be added here.

## Deployment notes

Step-by-step production installation guides are provided as mentioned in Quick start section above.
Both guides cover SSL certificate provisioning via Let's Encrypt and the two-phase Nginx configuration.
For more advanced deployments, the repository also includes raw helper templates under `setup/nginx` and `setup/docker`.
In production, review the environment templates in `setup/env` and configure the appropriate Django settings, database, cache, and static file settings before deployment.

## Notes for local customization

- Files in `setup` are intended as project templates and should not be edited directly.
- Local overrides should be placed under `qcalc/.setup`.
- The project includes deployment-related files under `setup/nginx` and `setup/docker` for more advanced setups.
