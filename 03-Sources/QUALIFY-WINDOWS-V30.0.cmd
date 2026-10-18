@echo off
setlocal EnableExtensions
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (echo ERROR: run BUILD-WINDOWS-INSTALLER.cmd first & exit /b 1)
".venv\Scripts\python.exe" smoke_windows_v300.py --launch --screenshot "captures\windows-v30.0-real.png" --output "qualification-windows-v30.0.json"
exit /b %errorlevel%
