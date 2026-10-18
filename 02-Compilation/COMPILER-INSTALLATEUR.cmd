@echo off
call "%~dp0BUILD-WINDOWS-INSTALLER.cmd" --installer-only
exit /b %errorlevel%
