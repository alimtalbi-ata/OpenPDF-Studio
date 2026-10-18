@echo off
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (echo Build first & exit /b 1)
".venv\Scripts\python.exe" qualify_portable_v296.py
exit /b %errorlevel%
