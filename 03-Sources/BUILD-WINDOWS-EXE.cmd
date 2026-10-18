@echo off
call "%~dp0BUILD-WINDOWS-INSTALLER.cmd" --exe-only
exit /b %errorlevel%
