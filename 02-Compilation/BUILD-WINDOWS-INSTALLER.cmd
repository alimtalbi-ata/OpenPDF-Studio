@echo off
setlocal EnableExtensions DisableDelayedExpansion
set "ROOT=%~dp0.."
set "BINARY=%ROOT%\01-Application\binary"
set "STAGE=%BINARY%\.staging-v39.8"
if exist "%STAGE%" rmdir /s /q "%STAGE%"
mkdir "%STAGE%" || exit /b 1
if not exist "%BINARY%" mkdir "%BINARY%"
cd /d "%ROOT%\03-Sources" || exit /b 1
set "LOG=%BINARY%\build-v39.8.log"
set "PY="
set "MODE=all"
if /I "%~1"=="--portable-only" set "MODE=portable"
if /I "%~1"=="--installer-only" set "MODE=installer"
if /I "%~1"=="--exe-only" set "MODE=portable"
rem Preserve previously validated executables until replacements pass all checks.
echo OpenPDF Studio V39.8 build started > "%LOG%"
where py >nul 2>&1
if not errorlevel 1 (py -3.12 -c "import sys;assert sys.version_info[:2]==(3,12)" >nul 2>&1 && set "PY=py -3.12")
if not defined PY if exist "%LocalAppData%\Programs\Python\Python312\python.exe" set "PY=%LocalAppData%\Programs\Python\Python312\python.exe"
if not defined PY if exist "%ProgramFiles%\Python312\python.exe" set "PY=%ProgramFiles%\Python312\python.exe"
if not defined PY (
  where winget >nul 2>&1 || goto missing_python
  winget install --id Python.Python.3.12 --exact --source winget --accept-package-agreements --accept-source-agreements >> "%LOG%" 2>&1 || goto fail
  if exist "%LocalAppData%\Programs\Python\Python312\python.exe" set "PY=%LocalAppData%\Programs\Python\Python312\python.exe"
)
if not defined PY goto missing_python
%PY% -m venv .venv >> "%LOG%" 2>&1 || goto fail
set "VPY=%CD%\.venv\Scripts\python.exe"
"%VPY%" -m pip install --upgrade pip >> "%LOG%" 2>&1 || goto fail
"%VPY%" -m pip install -r requirements-windows-v260.txt "pyinstaller>=6,<7" "Pillow>=10,<13" >> "%LOG%" 2>&1 || goto fail
"%VPY%" openpdf_build_preflight.py >> "%LOG%" 2>&1 || goto fail
"%VPY%" -m unittest test_openpdf_v398 test_openpdf_v394 test_openpdf_v393 test_openpdf_v392 test_openpdf_v390 test_openpdf_v387 test_openpdf_v386 test_openpdf_v385 test_openpdf_v384 test_openpdf_v383 test_openpdf_v382 >> "%LOG%" 2>&1 || goto fail
if /I "%MODE%"=="portable" goto portable
"%VPY%" -m PyInstaller --noconfirm --clean --windowed --onedir --name OpenPDF-Studio --collect-all fitz --collect-all pymupdf --hidden-import tkinter openpdf_studio.py >> "%LOG%" 2>&1 || goto fail
if not exist "dist\OpenPDF-Studio\OpenPDF-Studio.exe" goto fail
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0TEST-WINDOWS-BINARIES.ps1" -Mode installer -SourceDir "%CD%" -ReportPath "%STAGE%\windows-smoke-installer.json" >> "%LOG%" 2>&1 || goto fail
set "ISCC=%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
if not exist "%ISCC%" set "ISCC=%ProgramFiles%\Inno Setup 6\ISCC.exe"
if not exist "%ISCC%" set "ISCC=%LocalAppData%\Programs\Inno Setup 6\ISCC.exe"
if not exist "%ISCC%" (
  where winget >nul 2>&1 || goto missing_inno
  winget install --id JRSoftware.InnoSetup --exact --source winget --accept-package-agreements --accept-source-agreements >> "%LOG%" 2>&1 || goto fail
)
if not exist "%ISCC%" set "ISCC=%LocalAppData%\Programs\Inno Setup 6\ISCC.exe"
if not exist "%ISCC%" goto missing_inno
"%ISCC%" "OpenPDF-Studio-V39.8.iss" >> "%LOG%" 2>&1 || goto fail
if not exist "%STAGE%\OpenPDF-Studio-V39.8-Setup.exe" goto fail
for %%F in ("%STAGE%\OpenPDF-Studio-V39.8-Setup.exe") do if %%~zF LEQ 0 goto fail
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0TEST-WINDOWS-INSTALLATION.ps1" -SetupExe "%STAGE%\OpenPDF-Studio-V39.8-Setup.exe" -ReportPath "%STAGE%\windows-installation-v39.8.json" >> "%LOG%" 2>&1 || goto fail
if /I "%MODE%"=="installer" goto publish
:portable
"%VPY%" -m PyInstaller --noconfirm --clean --windowed --onefile --name OpenPDF-Studio-Portable-V39.8 --collect-all fitz --collect-all pymupdf --hidden-import tkinter --distpath "%STAGE%" openpdf_studio.py >> "%LOG%" 2>&1 || goto fail
if not exist "%STAGE%\OpenPDF-Studio-Portable-V39.8.exe" goto fail
for %%F in ("%STAGE%\OpenPDF-Studio-Portable-V39.8.exe") do if %%~zF LEQ 0 goto fail
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0TEST-WINDOWS-BINARIES.ps1" -Mode portable -SourceDir "%CD%" -ReportPath "%STAGE%\windows-smoke-portable.json" >> "%LOG%" 2>&1 || goto fail
:publish
rem Attach final artifact SHA256 to the staged smoke report, then publish both together.
"%VPY%" openpdf_bind_smoke.py "%STAGE%" "%MODE%" >> "%LOG%" 2>&1 || goto fail
rem Reject incomplete or mismatched artifacts BEFORE touching published binaries.
"%VPY%" openpdf_release_gate.py "%STAGE%" "%MODE%" >> "%LOG%" 2>&1 || goto fail
rem Validate and publish with rollback if a copy or replacement fails.
"%VPY%" openpdf_publish_binary.py "%STAGE%" "%BINARY%" "%MODE%" >> "%LOG%" 2>&1 || goto fail
:success
"%VPY%" openpdf_binary_manifest.py "%BINARY%" >> "%LOG%" 2>&1 || goto fail
"%VPY%" openpdf_release_gate.py "%BINARY%" "%MODE%" >> "%LOG%" 2>&1 || goto fail
if exist "%STAGE%" rmdir /s /q "%STAGE%"
echo BUILD SUCCESS. Binaries: "%BINARY%". See "%LOG%".
exit /b 0
:missing_python
echo Python 3.12 unavailable. See "%LOG%".
exit /b 1
:missing_inno
echo Inno Setup 6 unavailable. See "%LOG%".
exit /b 1
:fail
if exist "%STAGE%" rmdir /s /q "%STAGE%"
echo BUILD FAILED. See "%LOG%". No validated binary is claimed.
exit /b 1
