@echo off
rem This windows batch file should be RUN FROM qcalc_dock/qcalc/

rem This script Creates qCalc Dev System on Windows
rem The System will be based on SQlite database and File based caching
rem You can enhance it to use a database and caching services later

rem git clone qcalc from github
rem cd to qcalc folder
rem Then run this batch file setup\install_qcal

rem Ensure that python manager and python 3.12.10 are already installed
rem To install python manager use the following command in powershell or download from https://www.python.org

rem > winget install 9NQ7512CXL7T

rem To install python 3.12.10 issue the following command (either in powershell or command prompt)

rem > py install 3.12.10

py -3.12 -m venv .venv

call .venv\Scripts\activate

rem MS Visual C++ Runtime 14 or later is required
pip install -r requirements.txt

mkdir ..\.local\log\qcalc
mkdir ..\.temp
mkdir .setup
copy setup\env\template_setup.env setup.env
copy setup\env\template_dev_sqlite_file.env .setup\dev_sqlite_file.env
copy setup\env\template_gpref.json gpref.json

python manage.py migrate
set DJANGO_SUPERUSER_USERNAME=super
set DJANGO_SUPERUSER_EMAIL=admin@example.com
rem change super user password later
set DJANGO_SUPERUSER_PASSWORD=super
python manage.py createsuperuser --noinput
python manage.py collectstatic --noinput

rem If you want your database service to be mysql, also run
rem > pip install mysqlclient==2.2.1

rem finally start your qcalc dev server with following command
python manage.py runserver
