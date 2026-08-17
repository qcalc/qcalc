@echo off
rem This windows batch file should be RUN FROM qcalc_dock/qcalc/

rem Startup qCalc development server
call .venv\Scripts\activate

rem python.exe manage.py runserver --noreload
python.exe manage.py runserver
pause
