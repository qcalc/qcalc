# qCalc — Docker, Ubuntu Linux, VPS: Installation Guide

This guide covers a Docker-based deployment of qCalc on an Ubuntu VPS.
All services (qCalc/Gunicorn, Nginx, Certbot, PostgreSQL, Memcached) run as Docker containers defined in `setup/docker/template_docker.yml`.

---

## Prerequisites

- Ubuntu 22.04 LTS or 24.04 LTS VPS with root / sudo access
- A registered domain name pointed at the VPS IP address
- SSH access to the server

---

## 1. Initial Server Setup

Following instructions have used placeholders as <>. Replace these placeholders with appropriate values before executing the instructions.

### 1a. Create a non-root user

```bash
ssh root@<yourdomain.com>
adduser <user_name>
usermod -aG sudo <user_name>
exit
```

### 1b. Set up passwordless SSH access (from your local machine)

```bash
# On your local machine
cd ~/.ssh
ssh-keygen           # skip if a key already exists
scp id_rsa.pub <email@yourdomain.com>:~/.ssh/authorized_keys
```

Log in as the new user for all remaining steps:

```bash
ssh <user_name>@<yourdomain.com>
```

### 1c. Update the system

```bash
sudo apt update && sudo apt upgrade -y
```

### 1d. Create swap space 

This step is optional. It is recommended for small VPS having 2GB RAM or less.

```bash
sudo fallocate -l 1G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
# Make permanent
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

---

## 2. Install Docker Engine and Docker Compose

```bash
sudo apt install -y apt-transport-https ca-certificates curl software-properties-common
curl -fsSL https://download.docker.com/linux/ubuntu/gpg \
  | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] \
  https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" \
  | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt update
sudo apt install -y docker-ce docker-compose-plugin
sudo systemctl enable docker
# Allow the current user to run docker without sudo
sudo usermod -aG docker ${USER}
newgrp docker
docker info    # verify
```

---

## 3. Create the Project Directory Structure

```bash
mkdir -p ~/qcalc_dock/.local/nginx/conf
mkdir -p ~/qcalc_dock/.local/nginx/templates
mkdir -p ~/qcalc_dock/.local/certbot/conf
mkdir -p ~/qcalc_dock/.local/certbot/www
mkdir -p ~/qcalc_dock/.local/log/nginx
mkdir -p ~/qcalc_dock/.local/log/gunicorn
mkdir -p ~/qcalc_dock/.local/log/certbot
mkdir -p ~/qcalc_dock/.temp
mkdir -p ~/qcalc_dock/.cache
mkdir -p ~/qcalc_dock/qcalc_res
```

---

## 4. Deploy the qCalc Project

### 4a. Clone from Git

```bash
cd ~/qcalc_dock
git clone <your-qcalc-repo-url> qcalc
```

### 4b. Transfer resource files from your local machine (if not in Git)

```bash
# Run from your local machine
scp -r qcalc_res <user_name>@<yourdomain.com>:~/qcalc_dock/
```

---

## 5. Set Up the Docker Compose File

The compose template is at `qcalc/setup/docker/template_docker.yml`. Copy it one level up as `docker-compose.yml`:

```bash
cp ~/qcalc_dock/qcalc/setup/docker/template_docker.yml ~/qcalc_dock/docker-compose.yml
```

> The compose file uses `~/qcalc_dock/.local/` paths for all volumes. No edits are required unless you change the installation directory.

---

## 6. Set Up Nginx Configuration Files

### 6a. Main `nginx.conf`

```bash
cp ~/qcalc_dock/qcalc/setup/nginx/template_nginx.conf-v1.4j.conf \
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
cp ~/qcalc_dock/qcalc/setup/nginx/template_default.conf.template-v1.8j.conf \
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
DJANGO_SETTINGS_MODULE="config.settings.prd"
```

### 7b. Production `.env` file

```bash
mkdir -p ~/qcalc_dock/qcalc/.setup
cp ~/qcalc_dock/qcalc/setup/env/template_prod.env ~/qcalc_dock/qcalc/.setup/prod.env
nano ~/qcalc_dock/qcalc/.setup/prod.env
```

Key settings to fill in (see `setup/env/template_all_env_settings.env` for the full reference):
Set the DJANGO_SECRET_KEY value after generating the key using the command mentioned below.

```env
ROBOTS_TXT="robots.prod.txt"
DJANGO_DEBUG="False"
DJANGO_SECRET_KEY="<generate: python -c 'import secrets; print(secrets.token_urlsafe(50))'>"

DB_ENGINE="django.db.backends.postgresql_psycopg2"
DB_NAME="qcalc"
DB_USER="postgres"
DB_PASSWORD="postgres"       # matches POSTGRES_PASSWORD in docker-compose.yml
DB_HOST="postgres"           # Docker service/container name, not localhost
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
docker volume create pgdata
docker volume create static
```

---

## 9. Phase 1 — Start Containers with HTTP-Only Nginx

Activate the HTTP-only Nginx config so Certbot can complete the ACME challenge:

```bash
# Uses cp_conf_init.sh logic — copy init config into active default.conf
cp ~/qcalc_dock/.local/nginx/conf/default.conf.init \
   ~/qcalc_dock/.local/nginx/conf/default.conf
```

Start all containers:

```bash
cd ~/qcalc_dock
docker compose up -d
```

Verify all containers are running:

```bash
docker compose ps
```

---

## 10. Obtain the SSL Certificate

Run Certbot inside the certbot container to issue the certificate via the webroot method:

```bash
docker exec -it certbot certbot certonly \
  --webroot --webroot-path=/var/www/certbot \
  --email <you@yourdomain.com> \
  --agree-tos --no-eff-email \
  --cert-name <yourdomain.com> \
  -d <yourdomain.com> -d <www.yourdomain.com>
```

Expected output confirms certificate paths:

```
Certificate is saved at: /etc/letsencrypt/live/yourdomain.com/fullchain.pem
Key is saved at:         /etc/letsencrypt/live/yourdomain.com/privkey.pem
```

On the host these map to `~/qcalc_dock/.local/certbot/conf/live/yourdomain.com/`.

---

## 11. Phase 2 — Switch Nginx to HTTPS

Remove the HTTP-only config and activate the full HTTPS template:

```bash
# Uses cp_conf_template.sh logic
rm -f ~/qcalc_dock/.local/nginx/conf/default.conf
cp ~/qcalc_dock/.local/nginx/templates/default.conf.template.off \
   ~/qcalc_dock/.local/nginx/templates/default.conf.template
```

The Nginx container automatically processes `default.conf.template`, substitutes `${NGINX_HOST}` with `yourdomain.com`, and writes the result to `conf.d/default.conf`.

Restart the containers to pick up the new config:

```bash
cd ~/qcalc_dock
docker compose restart
```

Open `https://yourdomain.com` in a browser to verify the site is live and the certificate is valid.

---

## 12. Post-Installation

- Log in to the Django admin at `https://yourdomain.com/admin/` with the superuser created during `collectstatic`/`migrate` (the qCalc container runs these automatically on startup per `docker-compose.yml`). The default credentials are `super` / `super` — **change the password immediately**.
- Replace placeholder API keys in `.setup/prod.env` (Fixer.io, OpenWeather, OpenAI, etc.).
- Review `robots.txt` — copy and rename a template from `qcalc/qsite/static/txt/` to match `ROBOTS_TXT` in your `.env`.

---

## Day-to-Day Operations

### Pull latest code and redeploy

```bash
cd ~/qcalc_dock/qcalc
git pull
cd ~/qcalc_dock
docker compose restart qcalc
```

### Verify static files inside the container

```bash
docker exec -it qcalc python manage.py findstatic js/qcalc.js
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

---

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
