@echo off
setlocal EnableExtensions
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (echo ERROR: run BUILD-WINDOWS-INSTALLER.cmd first & exit /b 1)
".venv\Scripts\python.exe" ui_audit_v300.py --output "qualification-ui-v30.0.json"
exit /b %errorlevel%
