@echo off
setlocal EnableExtensions
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (echo ERROR: run BUILD-WINDOWS-INSTALLER.cmd first & exit /b 1)
".venv\Scripts\python.exe" smoke_windows_v287.py --launch --screenshot "captures\windows-v28.7-real.png" --output "qualification-windows-v28.7.json"
exit /b %errorlevel%
