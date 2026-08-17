@echo off
rem This windows batch file should be RUN FROM qcalc_dock/qcalc/

coverage run -m unittest discover tests
