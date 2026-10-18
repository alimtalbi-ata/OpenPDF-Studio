@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (echo Missing venv; run BUILD-WINDOWS-INSTALLER.cmd first & exit /b 1)
".venv\Scripts\python.exe" smoke_windows_v284.py --launch --output qualification-windows-v28.4.json
exit /b %errorlevel%
