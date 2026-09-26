@echo off
rem This windows batch file can be RUN FROM any folder

rem Replace QCALC_DOCK_PATH with your qcalc_dock location before use
set "QCALC_DOCK_PATH=s:\PROJECTS\QCALC\github\qcalc_dock"
set "scss_folder=%QCALC_DOCK_PATH%\qcalc\qsite\static\css\scss\"
set "css_folder=%QCALC_DOCK_PATH%\qcalc\qsite\static\css\"

for %%f in (qcalc-default ^
             qcalc-elegance ^
             qcalc-lumen ^
             qcalc-serenity ^
             qcalc-tranquil ^
             qcalc-vibe ^
             tree-default ^
             tree-elegance ^
             tree-lumen ^
             tree-serenity ^
             tree-tranquil ^
             tree-vibe ^
             ) do (
    call sass %scss_folder%%%f.scss %css_folder%%%f.css
    echo %%f.scss converted to %%f.css
)
