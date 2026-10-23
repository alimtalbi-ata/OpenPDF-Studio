@echo off
rem One command: build, native qualification, documentation and cumulative ZIP.
rem Author: Abdelhalim Talbi.
setlocal EnableExtensions DisableDelayedExpansion
set "ROOT=%~dp0"
call "%ROOT%02-Compilation\BUILD-AND-PACKAGE-WINDOWS.cmd"
exit /b %errorlevel%
