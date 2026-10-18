@echo off
call "%~dp0BUILD-WINDOWS-INSTALLER.cmd" --portable-only
exit /b %errorlevel%
