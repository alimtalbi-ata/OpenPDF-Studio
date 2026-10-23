@echo off
rem One-command Windows build, qualification, documentation and cumulative packaging.
rem Author: Abdelhalim Talbi
setlocal EnableExtensions DisableDelayedExpansion
set "ROOT=%~dp0.."
call "%~dp0BUILD-WINDOWS-INSTALLER.cmd" || exit /b 1
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0VERIFY-WINDOWS-RELEASE.ps1" || exit /b 1
set "PY=%ROOT%\03-Sources\.venv\Scripts\python.exe"
if not exist "%PY%" (echo Qualified Python environment missing & exit /b 1)
"%PY%" -m pip install "python-docx>=1.1,<2" "reportlab>=4,<5" "pypdf>=5,<7" || exit /b 1
"%PY%" "%~dp0generate_release_docs.py" || exit /b 1
"%PY%" "%~dp0package_cumulative_v434.py" --root "%ROOT%" --commit "%GITHUB_SHA%" || exit /b 1
echo Windows release built, qualified, documented and packaged.
exit /b 0
