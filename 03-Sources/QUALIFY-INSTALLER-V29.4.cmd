@echo off
setlocal EnableExtensions
cd /d "%~dp0"
echo WARNING: use only on a disposable Windows VM with no existing OpenPDF Studio installation.
if not exist ".venv\Scripts\python.exe" (echo ERROR: run BUILD-WINDOWS-INSTALLER.cmd first & exit /b 1)
".venv\Scripts\python.exe" qualify_installer_v294.py --allow-install-test --output "qualification-install-v29.4.json"
exit /b %errorlevel%
