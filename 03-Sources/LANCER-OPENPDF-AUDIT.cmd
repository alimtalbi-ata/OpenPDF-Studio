@echo off
setlocal EnableExtensions
cd /d "%~dp0"
set "PYEXE="
where py >nul 2>nul && (py -3 -c "import sys; assert sys.version_info >= (3,9)" >nul 2>nul && set "PYEXE=py -3")
if not defined PYEXE (
  where python >nul 2>nul && (python -c "import sys; assert sys.version_info >= (3,9)" >nul 2>nul && set "PYEXE=python")
)
if not defined PYEXE (
  echo [ERREUR] Python 3.9+ introuvable. Installer Python avec Tcl/Tk.
  pause
  exit /b 1
)
%PYEXE% windows_preflight_v258.py
if errorlevel 1 (
  echo [ERREUR] Prerequis incomplets. L'assistant ne sera pas lance.
  pause
  exit /b 1
)
%PYEXE% audit_assistant_v257.py
if errorlevel 1 (
  echo [ERREUR] L'interface n'a pas pu demarrer.
  pause
  exit /b 1
)
endlocal
