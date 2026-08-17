@echo off
rem This windows batch file can be RUN FROM any folder

rem Replace the REDIS_PATH with your installation path before use
rem For dev server laragon wont run redis, download unzip and run independently
set "REDIS_PATH=S:\PORTABLES\Redis-8.0.1-Windows-x64-msys2"
%REDIS_PATH%\redis-server.exe

