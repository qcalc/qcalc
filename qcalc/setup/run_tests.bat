@echo off
rem This windows batch file should be RUN FROM qcalc_dock/qcalc/

@REM coverage run -m unittest discover tests
coverage run -m pytest -q tests
