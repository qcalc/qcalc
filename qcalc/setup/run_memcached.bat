@echo off
rem This windows batch file can be RUN FROM any folder

rem Replace the MEMCACHED_PATH with your installation path before use
rem However, for dev server laragon is recommended which has builtin mysql, memcached
set "MEMCACHED_PATH=S:\PORTABLES\memcached-1.6.8-win64-mingw\bin"
%MEMCACHED_PATH%\memcached --daemon

