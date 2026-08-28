# qCalc — Dockerless, Ubuntu Linux, VPS: Installation Guide

This guide covers a bare-metal (no Docker) deployment of qCalc on an Ubuntu VPS using:
**Python 3.12 · Django 5 · Gunicorn · PostgreSQL/MySQL · Memcached · Nginx · Certbot (Let's Encrypt)**

---

## Prerequisites

- Ubuntu 22.04 LTS or 24.04 LTS VPS with root / sudo access
- A registered domain name pointed at the VPS IP address
- SSH access to the server

---

## 1. Initial Linux Server Setup

Follow [Initial Linux Server Setup](related-topics/initial-linux-server-setup.md) if you do not have a user account in linux


## 2. Install Python 3.12

```bash
sudo apt install software-properties-common -y
sudo add-apt-repository ppa:deadsnakes/ppa -y
sudo apt update
sudo apt install python3.12 python3.12-venv python3.12-dev -y
```

Verify:
```bash
python3.12 --version
```

---

## 3. Install System Dependencies

```bash
# Required by several Python packages (OpenCV, image processing)
sudo apt install -y libgl1-mesa-glx libglib2.0-0

# Build tools (required if using mysqlclient)
# sudo apt install build-essential pkg-config libmysqlclient-dev -y

# Git
sudo apt install git -y
```

---

## 4. Clone the qCalc Repository from Git

```bash
cd ~
git clone https://github.com/qcalc/qcalc.git qcalc_dock
cd ~/qcalc_dock/qcalc
```

## 5. Create the Python Virtual Environment

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install gunicorn
```

## 6. Create the Project Directory Structure

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
mkdir -p ~/qcalc_dock/.cache
```

## 7. Copy Configuration Templates

```bash
cd ~/qcalc_dock/qcalc
cp setup/env/template_setup.env setup.env
cp setup/env/template_prod.env .setup/prod.env
cp setup/env/template_gpref.json gpref.json
```

## 8. Install Database Service

### 8a. Install PostgreSQL

```bash
sudo apt install postgresql postgresql-contrib -y
sudo systemctl enable postgresql
sudo systemctl start postgresql
```

Create the database and user:

```bash
sudo -u postgres psql
```

```sql
CREATE DATABASE qcalc;
CREATE USER qcalc WITH PASSWORD '<pg_user_password>';
GRANT ALL PRIVILEGES ON DATABASE qcalc TO qcalc;
```
> Replace `pg_user_password` with a strong password. Record it — you will need it later.

Install the PostgreSQL dependency:

```bash
cd ~/qcalc_dock/qcalc
source .venv/bin/activate
pip install psycopg2-binary==2.9.9
```

### 8b. (Optional) Install MySQL instead of PostgreSQL

```bash
sudo apt install mysql-server -y
sudo systemctl enable mysql
sudo systemctl start mysql
sudo mysql_secure_installation
```

Create the database and user:

```bash
sudo mysql -u root -p
```

```sql
CREATE DATABASE qcalc;
CREATE USER 'qcalc'@'localhost' IDENTIFIED BY '<mysql_user_password>';
GRANT ALL PRIVILEGES ON qcalc.* TO 'qcalc'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

Install the Python MySQL client (also install the build deps from step 3 if not already done):

```bash
sudo apt install build-essential pkg-config libmysqlclient-dev -y
cd ~/qcalc_dock/qcalc
source .venv/bin/activate
pip install mysqlclient==2.2.1
```

### 8c. Edit `.setup/prod.env` to Update Database Environment

From `~/qcalc_dock/qcalc/`:

```bash
nano .setup/prod.env
```
If you have installed MySQL:

```env
DB_ENGINE="django.db.backends.mysql"
DB_NAME="qcalc"
DB_USER="qcalc"
DB_PASSWORD="<db_user_password>"
DB_HOST="127.0.0.1"
DB_PORT="3306"
```

If you have installed PostgreSQL:

```env
DB_ENGINE="django.db.backends.postgresql_psycopg2"
DB_NAME="qcalc"
DB_USER="qcalc"
DB_PASSWORD="<db_user_password>"
DB_HOST="127.0.0.1"
DB_PORT="5432"
```

---

## Install Caching Service

Install either redis or memcached.

### 9a. Install Redis

Redis is recommended for production environment

```bash
sudo apt install redis-server -y
sudo systemctl enable redis-server
sudo systemctl start redis-server
```

Verify Redis is responding:

```bash
redis-cli ping
# Expected output: PONG
```

### 9b. Install Memcached

Memcached is not recommended for production environment. Especially if you want
multi instance setup and multiple gunicorn worker per instance, please install redis.

```bash
sudo apt install memcached libmemcached-tools -y
sudo systemctl enable memcached
sudo systemctl start memcached
```

Memcached listens on `127.0.0.1:11211` by default. 
Edit `/etc/memcached.conf` to set the cache size (e.g. `-m 256` for 256 MB).


### 9c. Edit `.setup/prod.env` to Update Caching Environment:

If you have installed Memcached:

```env
DEFAULT_CACHE_ALIAS="memcached"
MEMCACHE_HOST="127.0.0.1"
MEMCACHE_PORT="11211"
```

If you have installed Redis:

```env
DEFAULT_CACHE_ALIAS="redis"
REDIS_PUBSUB="1"
REDIS_HOST="127.0.0.1"
REDIS_PORT="6379"
REDIS_DB="1"
```

---

## 10. Install Nginx

```bash
sudo apt install nginx -y
sudo systemctl enable nginx
```

---

## 11. Install Certbot

```bash
sudo snap install --classic certbot
sudo ln -s /snap/bin/certbot /usr/bin/certbot
```

---

## 10. Configure Environment Files

### 10a. Edit `~/qcalc_dock/qcalc/setup.env`

```bash
nano ~/qcalc_dock/qcalc/setup.env
```

Set production values:

```env
QCALC_SCHEME='https'
QCALC_DOMAIN="<yourdomain.com>"
QCALC_ENV_FILE=".setup/prod.env"
DJANGO_SETTINGS_MODULE="config.settings.prod"
```

### 10b. Production `.setup/prod.env` File

```bash
nano ~/qcalc_dock/qcalc/.setup/prod.env
```

Edit the environment variables as appropriate (see `setup/env/template_all_env_settings.env` for full reference):

```env
DJANGO_DEBUG="False"
DJANGO_SECRET_KEY="<generate with: python -c 'import secrets; print(secrets.token_urlsafe(50))'>"

# Keep the Databse Environment Variables as we edited before
# Keep the Caching Environment Variables as we edited before

FILE_UPLOAD_TEMP_DIR="/home/<user_id>/qcalc_dock/.temp/"
JSON_FILES_DIR="/home/<user_id>/qcalc_dock/qcalc_res/json/"
HELP_FILES_DIR="/home/<user_id>/qcalc_dock/qcalc_res/help/"
DOCS_FILES_DIR="/home/<user_id>/qcalc_dock/qcalc_res/docs/"
AI_MODELS_DIR="/home/<user_id>/qcalc_dock/qcalc_res/model/"

FIXER_API_KEY="<your_fixer_api_key>" # Your own key recommended for currency updates

# Optional API keys
OPENW_API_KEY="<your_openweather_api_key>"

DJANGO_EMAIL_BACKEND="django.core.mail.backends.smtp.EmailBackend"
DJANGO_EMAIL_HOST="<smtp.yourmailprovider.com>"
DJANGO_EMAIL_PORT="587"
DJANGO_EMAIL_USE_TLS="True"
DJANGO_EMAIL_HOST_USER="<you@yourdomain.com>"
DJANGO_EMAIL_HOST_PASSWORD="<your_email_password>"
```

### 10c. Edit Global Preferences `gpref.json`

You can keep the file as it is for time being.

```bash
nano ~/qcalc_dock/qcalc/gpref.json
```

---

## 11. Initialize Django

If you are not already in virtual environment

```bash
cd ~/qcalc_dock/qcalc
source .venv/bin/activate
```

```bash
python manage.py migrate
python manage.py collectstatic --noinput

# Create superuser
export DJANGO_SUPERUSER_USERNAME=super
export DJANGO_SUPERUSER_EMAIL=<your_email_address>
export DJANGO_SUPERUSER_PASSWORD=super    # change this now or immediately after first login
python manage.py createsuperuser --noinput
```

---

## 12. Configure Gunicorn as a systemd Service

Create a systemd unit file that mirrors the three-instance setup used in Docker:

```bash
sudo nano /etc/systemd/system/qcalc.service
```
Replace <user_id> with your actual linux user_id. qCalc supports multiple workers per application instance. 
This file has defined 2 application instances and 2 workers per instances (`--workers 2`). Depending on number of potential users you can decide and change them.
If you want a stable low load in-house production environment you can keep just 1 instance and 1 worker. 

```ini
[Unit]
Description=qCalc Gunicorn workers
After=network.target postgresql.service memcached.service

[Service]
User=<user_id>
Group=<user_id>
WorkingDirectory=/home/<user_id>/qcalc_dock/qcalc
Environment="PATH=/home/<user_id>/qcalc_dock/qcalc/.venv/bin"
ExecStart=/bin/bash -c '\
  export GUNICORN_INSTANCE_ID=instance_1; \
  /home/<user_id>/qcalc_dock/qcalc/.venv/bin/gunicorn config.wsgi:application \
    --bind 127.0.0.1:8001 --workers 2 --timeout 900 \
    --access-logfile /home/<user_id>/qcalc_dock/.local/log/gunicorn/access_1.log \
    --error-logfile /home/<user_id>/qcalc_dock/.local/log/gunicorn/error_1.log \
    --log-file /home/<user_id>/qcalc_dock/.local/log/gunicorn/qcalc_1.log & \
  export GUNICORN_INSTANCE_ID=instance_2; \
  /home/<user_id>/qcalc_dock/qcalc/.venv/bin/gunicorn config.wsgi:application \
    --bind 127.0.0.1:8002 --workers 2 --timeout 900 \
    --access-logfile /home/<user_id>/qcalc_dock/.local/log/gunicorn/access_2.log \
    --error-logfile /home/<user_id>/qcalc_dock/.local/log/gunicorn/error_2.log \
    --log-file /home/<user_id>/qcalc_dock/.local/log/gunicorn/qcalc_2.log & \
  wait'
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable qcalc
sudo systemctl start qcalc
sudo systemctl status qcalc
```

---

## 13. Configure Nginx

### 13a. Main `nginx.conf`

Base your config on `setup/nginx/template_default.conf.template-prod.conf`:

```bash
sudo cp ~/qcalc_dock/qcalc/setup/nginx/template_default.conf.template-prod.conf /etc/nginx/nginx.conf
```

Review and adjust `worker_processes`, `worker_connections`, and `client_max_body_size` as needed.

### 13b. Initial HTTP-Only Site (Before SSL Certificate)

Before obtaining the SSL certificate, create a minimal HTTP config so Certbot can complete the ACME challenge. Based on `setup/nginx/template_default.conf.init`:

```bash
sudo nano /etc/nginx/conf.d/default.conf
```

```nginx
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;

    location / {
        root /usr/share/nginx/html;
        index index.html index.htm;
    }

    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }
}
```

```bash
sudo mkdir -p /var/www/certbot
sudo nginx -t
sudo systemctl reload nginx
```

---

## 14. Obtain the SSL Certificate

```bash
sudo certbot certonly --webroot \
  --webroot-path=/var/www/certbot \
  --email <your_email_address> \
  --agree-tos --no-eff-email \
  --cert-name <your_domain> \
  -d <your_domain> -d www.<your_domain>
```

Certificates are written to `/etc/letsencrypt/live/yourdomain.com/`.

Set up automatic renewal:

```bash
sudo systemctl enable snap.certbot.renew.timer
```

---

## 15. Configure Nginx for HTTPS

Based on `setup/nginx/template_default.conf.template-prod.conf.conf`. Replace the HTTP-only config with the full production config. Adapt the upstream block and all path/domain placeholders:

```bash
sudo nano /etc/nginx/conf.d/default.conf
```

Replace **every occurrence** of `${NGINX_HOST}` with `yourdomain.com` and replace the Docker upstream hostnames (`qcalc:800x`) with `127.0.0.1:800x`.

Key changes from the template for a non-Docker setup:

```nginx
# Upstream — use localhost instead of Docker container name
upstream qcalc_servers {
    server 127.0.0.1:8001;
    server 127.0.0.1:8002;
}

# Static files — use the local filesystem path
location ^~ /static/ {
    alias /home/ubuntu/qcalc_dock/qcalc/staticfiles/;
    expires 1y;
    add_header Cache-Control "public, immutable";
    access_log off;
}

# SSL certificate paths
ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;

# Log files
access_log /home/ubuntu/qcalc_dock/.local/log/nginx/access.log;
```

Validate and reload:

```bash
sudo nginx -t
sudo systemctl reload nginx
```

---

## 16. File Permissions

Ensure Nginx can read static files:

```bash
chmod o+x /home/ubuntu
chmod -R o+r /home/ubuntu/qcalc_dock/qcalc/staticfiles/
```

---

## 17. Verify the Installation

```bash
# Check all services are running
sudo systemctl status qcalc
sudo systemctl status nginx
sudo systemctl status postgresql
sudo systemctl status memcached

# Tail logs for errors
tail -f ~/qcalc_dock/.local/log/gunicorn/error_1.log
tail -f ~/qcalc_dock/.local/log/nginx/access.log
```

Open `https://yourdomain.com` in a browser to confirm the site is live.

---

## 18. Post-Installation

- Log in to the Django admin at `https://yourdomain.com/admin/` with username `super` and **immediately change the password**.
- Replace the placeholder API keys in `.setup/prod.env` (Fixer.io, OpenWeather, OpenAI, etc.) with your own keys.
- Review `robots.txt` — copy and rename a template from `~/qcalc_dock/qcalc/setup/txt/` to `~/qcalc_dock/qcalc/qsite/static/qsiite/` folder.

```bash
cp ~/qcalc_dock/qcalc/setup/txt/template_robots.prod.txt \
   ~/qcalc_dock/qcalc/qsite/static/qsite/robots.txt
```
---

## Directory Layout Summary

```
~/qcalc_dock/                      # qCalc PROJECT dir (Git-managed)
├── qcalc/                         # Django project, qCalc ROOT dir 
│   ├── .venv/                     # Python virtual environment
│   ├── setup.env                  # Startup configuration (not in Git)
│   ├── .setup/                    # not in Git
│   │   └── prod.env               # Production secrets (not in Git)
│   └── qsite                      # qCalc APP dir
├── qcalc_res/                     # Resource files (json, help, model)
├── .local/                        # not in Git
│   └── log/
│       ├── gunicorn/
│       └── nginx/
└── .temp/                         # Temporary file uploads, # not in Git
```

---

## Quick Reference — Useful Commands

| Task | Command |
|------|---------|
| Restart qcalc | `sudo systemctl restart qcalc` |
| Reload Nginx | `sudo systemctl reload nginx` |
| Activate venv | `source ~/qcalc_dock/qcalc/.venv/bin/activate` |
| Run migrations | `python manage.py migrate` |
| Collect static | `python manage.py collectstatic --noinput` |
| Renew certificate | `sudo certbot renew` |
| View Gunicorn log | `tail -f ~/qcalc_dock/.local/log/gunicorn/error_1.log` |
| View Nginx log | `tail -f ~/qcalc_dock/.local/log/nginx/access.log` |
