#!/usr/bin/env bash
# This linux shell script should be RUN FROM qcalc_dock/qcalc

# This script Creates qCalc Dev System on linux
# The System will be based on SQlite database and File based caching
# You can enhance it to use a database and caching services later
set -euo pipefail

# Ensure that python 3.12 is already installed
# You can use the following commands to install it on ubuntu linux

# > sudo apt update
# > sudo apt install software-properties-common -y
# > sudo add-apt-repository ppa:deadsnakes/ppa -y
# > sudo apt update
# > sudo apt install python3.12 python3.12-venv python3.12-dev

# If you want your database service to be mysql, also install
# sudo apt install build-essential pkg-config libmysqlclient-dev -y

python3.12 -m venv .venv

source .venv/bin/activate
pip install -r requirements.txt

mkdir -p ../.local
mkdir -p ../.temp
mkdir -p .setup
cp setup/env/template_setup.env setup.env
cp setup/env/template_dev_sqlite_file.env .setup/dev_sqlite_file.env
cp setup/env/template_gpref.json gpref.json

python manage.py migrate
export DJANGO_SUPERUSER_USERNAME=super
export DJANGO_SUPERUSER_EMAIL=admin@example.com
# change super user password later
export DJANGO_SUPERUSER_PASSWORD=super
python manage.py createsuperuser --noinput
python manage.py collectstatic --noinput

# If you want your database service to be mysql, also run
# > pip install mysqlclient==2.2.1

# finally start your qcalc dev server with following command
# > python manage.py runserver
