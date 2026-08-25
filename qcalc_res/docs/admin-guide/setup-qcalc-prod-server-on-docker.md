# qCalc — Docker, Ubuntu Linux, VPS: Installation Guide
<!-- TOC -->
* [qCalc — Docker, Ubuntu Linux, VPS: Installation Guide](#qcalc--docker-ubuntu-linux-vps-installation-guide)
  * [Prerequisites](#prerequisites)
  * [1. Initial Linux Server Setup](#1-initial-linux-server-setup)
  * [2. Install Docker Engine and Docker Compose](#2-install-docker-engine-and-docker-compose)
  * [3. Clone the qCalc Repository from Git](#3-clone-the-qcalc-repository-from-git)
  * [4. Create the Project Directory Structure](#4-create-the-project-directory-structure)
  * [5. Set Up the Docker Files](#5-set-up-the-docker-files)
    * [Edit the Dockerfile](#edit-the-dockerfile)
    * [Edit the docker-compose.yml file](#edit-the-docker-composeyml-file)
  * [6. Set Up Nginx Configuration Files](#6-set-up-nginx-configuration-files)
    * [6a. Main `nginx.conf`](#6a-main-nginxconf)
    * [6b. Initial HTTP-only config (used before the SSL certificate exists)](#6b-initial-http-only-config-used-before-the-ssl-certificate-exists)
    * [6c. Full HTTPS template (used after the SSL certificate is obtained)](#6c-full-https-template-used-after-the-ssl-certificate-is-obtained)
  * [7. Configure Environment Files](#7-configure-environment-files)
    * [7a. `setup.env`](#7a-setupenv)
    * [7b. Production `.env` file](#7b-production-env-file)
    * [7c. `gpref.json`](#7c-gprefjson)
  * [8. Create Docker Named Volumes](#8-create-docker-named-volumes)
  * [9. Phase 1 — Start Containers with HTTP-Only Nginx](#9-phase-1--start-containers-with-http-only-nginx)
  * [10. Obtain the SSL Certificate](#10-obtain-the-ssl-certificate)
  * [11. Phase 2 — Switch Nginx to HTTPS](#11-phase-2--switch-nginx-to-https)
  * [11a. Create qCalc Super User](#11a-create-qcalc-super-user)
  * [11b. Switch to HTTPS](#11b-switch-to-https)
  * [12. Post-Installation](#12-post-installation)
  * [Day-to-Day Operations](#day-to-day-operations)
    * [Pull latest code and redeploy](#pull-latest-code-and-redeploy)
    * [Verify static files inside the container](#verify-static-files-inside-the-container)
    * [Run a management command inside the container](#run-a-management-command-inside-the-container)
    * [View logs](#view-logs)
  * [### Some useful docker commands](#-some-useful-docker-commands)
  * [Quick Reference — Useful Commands](#quick-reference--useful-commands)
  * [Directory Layout Summary](#directory-layout-summary)
<!-- TOC -->
This guide covers a Docker-based deployment of qCalc on an Ubuntu VPS.
All services (qCalc/Gunicorn, Nginx, Certbot, PostgreSQL, Memcached) run as Docker containers defined in `setup/docker/template_docker.yml`.

---

## Prerequisites

- Ubuntu 22.04 LTS or 24.04 LTS VPS with root / sudo access
- A registered domain name pointed at the VPS IP address
- SSH access to the server

---

## 1. Initial Linux Server Setup

Follow [Initial Linux Server Setup](related-topics/initial-linux-server-setup.md) if you do not have a user account in linux

## 2. Install Docker Engine and Docker Compose

Following instruction set is for Ubuntu 26.04 LTS.

```bash
sudo apt update
sudo apt install -y ca-certificates curl

sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg \
    -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc

echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] \
  https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "${UBUNTU_CODENAME:-$VERSION_CODENAME}") stable" \
  | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

sudo apt update

sudo apt install -y \
    docker-ce \
    docker-ce-cli \
    containerd.io \
    docker-buildx-plugin \
    docker-compose-plugin

sudo systemctl enable --now docker

sudo usermod -aG docker ${USER}
newgrp docker

docker info
docker compose version
```

---

## 3. Clone the qCalc Repository from Git

```bash
cd ~
git clone https://github.com/qcalc/qcalc.git qcalc_dock
```

---

## 4. Create the Project Directory Structure

```bash
mkdir -p ~/qcalc_dock/.local/nginx/templates
mkdir -p ~/qcalc_dock/.local/nginx/conf
mkdir -p ~/qcalc_dock/.local/certbot/conf
mkdir -p ~/qcalc_dock/.local/certbot/www
mkdir -p ~/qcalc_dock/.local/log/nginx
mkdir -p ~/qcalc_dock/.local/log/gunicorn
mkdir -p ~/qcalc_dock/.local/log/certbot
mkdir -p ~/qcalc_dock/.temp
mkdir -p ~/qcalc_dock/qcalc/.setup
```

---

## 5. Set Up the Docker Files

The compose template is at `qcalc/setup/docker/template_docker.yml`. Copy it one level up as `docker-compose.yml`:

```bash
cp ~/qcalc_dock/qcalc/setup/docker/template_docker_compose.yml ~/qcalc_dock/docker-compose.yml
cp ~/qcalc_dock/qcalc/setup/docker/template_dockerfile ~/qcalc_dock/Dockerfile
cp ~/qcalc_dock/qcalc/setup/docker/.dockerignore ~/qcalc_dock/.dockerignore
```

### Edit the Dockerfile

```bash
nano ~/qcalc_dock/Dockerfile

# Uncomment the following line if you are using MySQL
# RUN pip install --no-cache-dir mysqlclient==2.2.1

# (optional) Uncomment the following line if you are using PostgreSQL instead
# RUN pip install --no-cache-dir psycopg2-binary==2.9.9
```

### Edit the docker-compose.yml file

Search and replace the following placeholders:

- `<your_host_name>`
- `<pg_user_password>` or `<mysql_user_password>` and `<mysql_root_password>`

Review Gunicorn instances and number of workers.

> The compose file uses `~/qcalc_dock/.local/` paths for all volumes. No edits are required unless you change the installation directory.

---

## 6. Set Up Nginx Configuration Files

### 6a. Main `nginx.conf`

```bash
cp ~/qcalc_dock/qcalc/setup/nginx/template_nginx.conf-common.conf \
   ~/qcalc_dock/.local/nginx/nginx.conf
```

### 6b. Initial HTTP-only config (used before the SSL certificate exists)

```bash
cp ~/qcalc_dock/qcalc/setup/nginx/template_default.conf.init \
   ~/qcalc_dock/.local/nginx/conf/default.conf.init
```

Edit the file and replace `<replace_with_your_domain>` with your actual domain:

```bash
nano ~/qcalc_dock/.local/nginx/conf/default.conf.init
```

### 6c. Full HTTPS template (used after the SSL certificate is obtained)

```bash
cp ~/qcalc_dock/qcalc/setup/nginx/template_default.conf.template-prod.conf.conf \
   ~/qcalc_dock/.local/nginx/templates/default.conf.template.off
```

> The `.off` suffix prevents Nginx from processing this template before the SSL certificate exists.
> `${NGINX_HOST}` placeholders in this file are automatically replaced by the Nginx Docker container using the `NGINX_HOST` environment variable set in `docker-compose.yml`.

---

## 7. Configure Environment Files

### 7a. `setup.env`

```bash
cp ~/qcalc_dock/qcalc/setup/env/template_setup.env ~/qcalc_dock/qcalc/setup.env
nano ~/qcalc_dock/qcalc/setup.env
```

```env
QCALC_SCHEME='https'
QCALC_DOMAIN="<yourdomain.com>"
QCALC_ENV_FILE=".setup/prod.env"
DJANGO_SETTINGS_MODULE="config.settings.prod"
```

### 7b. Production `.env` file

```bash
cp ~/qcalc_dock/qcalc/setup/env/template_prod.env ~/qcalc_dock/qcalc/.setup/prod.env
nano ~/qcalc_dock/qcalc/.setup/prod.env
```

Key settings to fill in (see `setup/env/template_all_env_settings.env` for the full reference):
Set the DJANGO_SECRET_KEY value after generating the key using the command mentioned as the current value of the key.

Generate a strong secret key on the development system (as your app will run from docker, your server may not need python to be installed to generate secret) and add it to the `prod.env` file. Do not commit the production key to the git repository.

```env
DJANGO_DEBUG="False"
DJANGO_SECRET_KEY="<python -c 'import secrets; print(secrets.token_urlsafe(50))'>"

DB_ENGINE="django.db.backends.postgresql_psycopg2"
DB_NAME="qcalc"
DB_USER="qcalc"
DB_PASSWORD="<db_user_password>"       # matches POSTGRES_PASSWORD in docker-compose.yml
DB_HOST="postgres"                     # Docker service/container name, not localhost
DB_PORT="5432"

DEFAULT_CACHE_ALIAS="memcached"
MEMCACHE_HOST="memcached"    # Docker service/container name
MEMCACHE_PORT="11211"

# Paths inside the qcalc container (must match docker-compose.yml volumes)
FILE_UPLOAD_TEMP_DIR="/usr/src/qcalc_dock/.temp/"
JSON_FILES_DIR="/usr/src/qcalc_dock/qcalc_res/json/"
HELP_FILES_DIR="/usr/src/qcalc_dock/qcalc_res/help/"
DOCS_FILES_DIR="/usr/src/qcalc_dock/qcalc_res/docs/"
AI_MODELS_DIR="/usr/src/qcalc_dock/qcalc_res/model/"

FIXER_API_KEY="<your_fixer_api_key>"        # obtain an API key for currency rates update
OPENW_API_KEY="<your_openweather_api_key>"  # this is optional

DJANGO_EMAIL_BACKEND="django.core.mail.backends.smtp.EmailBackend"
DJANGO_EMAIL_HOST="<smtp.yourmailprovider.com>"
DJANGO_EMAIL_PORT="587"
DJANGO_EMAIL_USE_TLS="True"
DJANGO_EMAIL_HOST_USER="<you@yourdomain.com>"
DJANGO_EMAIL_HOST_PASSWORD="<your_email_password>"
```

> **Important:** `DB_HOST` and `MEMCACHE_HOST` must be the Docker **container/service names** (`postgres`, `memcached`), not `localhost`.

### 7c. `gpref.json`

```bash
cp ~/qcalc_dock/qcalc/setup/env/template_gpref.json ~/qcalc_dock/qcalc/gpref.json
```

---

## 8. Create Docker Named Volumes

```bash
docker volume create static
```

or if you have opted for postgres

```bash
docker volume create pgdata
```

or if you have opted for mysql

```bash
docker volume create mysqldata
```

---

## 9. Phase 1 — Start Containers with HTTP-Only Nginx

Activate the HTTP-only Nginx config so Certbot can complete the ACME challenge:

```bash
# Uses cp_conf_init.sh logic — copy init config into active default.conf
cp ~/qcalc_dock/.local/nginx/conf/default.conf.init \
   ~/qcalc_dock/.local/nginx/conf/default.conf
cd ~/qcalc_dock
docker compose up
```

---

## 10. Obtain the SSL Certificate

Run Certbot inside the certbot container to issue the certificate via the webroot method:

```bash
docker exec -it certbot certbot certonly \
  --webroot --webroot-path=/var/www/certbot \
  --email <your_email_id> \
  --agree-tos --no-eff-email \
  --cert-name <your_domain> \
  -d <your_domainm> -d www.<your_domain>
```

Expected output confirms certificate paths:

```
Certificate is saved at: /etc/letsencrypt/live/yourdomain.com/fullchain.pem
Key is saved at:         /etc/letsencrypt/live/yourdomain.com/privkey.pem
```

On the host these map to `~/qcalc_dock/.local/certbot/conf/live/<your_domain>/`.

---

## 11. Phase 2 — Switch Nginx to HTTPS


## 11a. Create qCalc Super User

```shell
docker exec -it qcalc python manage.py createsuperuser --username super
```
It will prompt you for the other required details (email and password)

## 11b. Switch to HTTPS

Remove the HTTP-only config and activate the full HTTPS template:

```bash
mv ~/qcalc_dock/.local/nginx/conf/default.conf \
   ~/qcalc_dock/.local/nginx/conf/default.conf.init
mv ~/qcalc_dock/.local/nginx/templates/default.conf.template.off \
   ~/qcalc_dock/.local/nginx/templates/default.conf.template
```

The Nginx container automatically processes `default.conf.template`, substitutes `${NGINX_HOST}` with `yourdomain.com`, and writes the result to `conf.d/default.conf`.

Restart the containers to pick up the new config:

```bash
cd ~/qcalc_dock
docker compose restart
```

Open `https://<your_domain>` in a browser to verify the site is live and the certificate is valid.

---

## 12. Post-Installation

- Log in to the Django admin at `https://<your_domain>/admin/` with the superuser created during `collectstatic`/`migrate` (the qCalc container runs these automatically on startup per `docker-compose.yml`). The default credentials are `super` / `super` — **change the password immediately**.
- Replace placeholder API keys in `.setup/prod.env` (Fixer.io, OpenWeather, OpenAI, etc.).
- Review `robots.txt` — copy and rename a template from `~/qcalc_dock/qcalc/setup/txt/` to `~/qcalc_dock/qcalc/qsite/static/qsiite/` folder.

```bash
cp ~/qcalc_dock/qcalc/setup/txt/template_robots.prod.txt \
   ~/qcalc_dock/qcalc/qsite/static/qsite/robots.txt
```
You verify it using the url: `https://<your_domain>/robots.txt`

---

## Day-to-Day Operations

### Pull latest code and redeploy

```bash
cd ~/qcalc_dock/
git pull
docker compose restart qcalc
```

### Verify static files inside the container

```bash
docker exec -it qcalc python manage.py findstatic qsite/js/qcalc.js
```

### Run a management command inside the container

```bash
docker exec -it qcalc python manage.py <command>
```

### View logs

```bash
# Gunicorn
tail -f ~/qcalc_dock/.local/log/gunicorn/error_1.log

# Nginx
tail -f ~/qcalc_dock/.local/log/nginx/access.log

# Container stdout
docker compose logs -f qcalc
docker compose logs -f nginx
```

### Some useful docker commands
---

```shell
docker exec -it qcalc bash   # docker shell access
docker logs --tail 100 qcalc # last 100 lines of log
docker logs qcalc            # follow the log LIVE
docker ps              # Running containers
docker stop qcalc      # Stop
docker start qcalc     # Start again
docker restart qcalc   # Restart
docker rm qcalc        # Remove a stopped container

```

## Quick Reference — Useful Commands

| Task | Command |
|------|---------|
| Start all containers | `docker compose up -d` |
| Stop all containers | `docker compose down` |
| Restart a single service | `docker compose restart qcalc` |
| Rebuild qcalc image | `docker compose build qcalc` |
| Rebuild and restart | `docker compose up -d --build qcalc` |
| Reset to HTTP-only nginx | `cp_conf_init.sh` (or its inline equivalent in step 9) |
| Activate HTTPS nginx | `cp_conf_template.sh` (or its inline equivalent in step 11) |
| Renew SSL certificate | `docker exec -it certbot certbot renew` |
| Open a shell in container | `docker exec -it qcalc bash` |

---

## Directory Layout Summary

```
~/qcalc_dock/                      # qCalc PROJECT dir (Git-managed)
├── docker-compose.yml             # Copied from qcalc/setup/docker/template_docker.yml
├── qcalc/                         # Django project, qCalc ROOT dir
│   ├── setup.env                  # Startup configuration (not in Git)
│   ├── .setup/                    # not in Git
│   │   └── prod.env               # Production secrets (not in Git)
│   └── qsite                      # qCalc APP dir
├── qcalc_res/                     # Resource files (json, help, model)
├── .local/                        # not in Git
│   ├── nginx/
│   │   ├── nginx.conf             # Nginx main config (host-mounted)
│   │   ├── conf/
│   │   │   ├── default.conf       # Active site config (switched per phase)
│   │   │   └── default.conf.init  # HTTP-only config (kept as backup)
│   │   └── templates/
│   │       ├── default.conf.template      # Active HTTPS template (Phase 2)
│   │       └── default.conf.template.off  # Inactive HTTPS template (Phase 1)
│   ├── certbot/
│   │   ├── conf/                  # Let's Encrypt certificates
│   │   └── www/                   # ACME challenge webroot
│   └── log/
│       ├── gunicorn/
│       ├── nginx/
│       └── certbot/
└──  .temp/                         # Temporary file uploads, not in Git
```
