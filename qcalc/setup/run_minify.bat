@echo off
rem Minifies own CSS/JS into *.min.css / *.min.js (only changed sources). Run from any folder.
rem   run_minify.bat           one pass
rem   run_minify.bat --watch   keep running, rebuild on save
rem   run_minify.bat --force   rebuild everything
rem Run setup/run_sass.bat first when scss changed, so css/*.css is current.

rem esbuild is installed once globally (npm -g); NODE_PATH lets minify.js find it.
for /f "delims=" %%i in ('npm root -g') do set "NODE_PATH=%%i"
if not exist "%NODE_PATH%\esbuild" call npm install -g esbuild

node "%~dp0minify\minify.js" %*
