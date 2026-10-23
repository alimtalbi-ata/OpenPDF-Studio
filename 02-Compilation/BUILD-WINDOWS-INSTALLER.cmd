@echo off
setlocal EnableExtensions DisableDelayedExpansion
set "ROOT=%~dp0.."
for /f "usebackq delims=" %%V in ("%ROOT%\VERSION.txt") do set "VERSION=%%V"
if not defined VERSION exit /b 1
set "BINARY=%ROOT%\01-Application\binary"
set "STAGE=%BINARY%\.staging-v%VERSION%"
if exist "%STAGE%" rmdir /s /q "%STAGE%"
mkdir "%STAGE%" || exit /b 1
if not exist "%BINARY%" mkdir "%BINARY%"
cd /d "%ROOT%\03-Sources" || exit /b 1
set "LOG=%BINARY%\build-v%VERSION%.log"
set "PY_EXE="
set "PY_ARGS="
set "MODE=all"
if /I "%~1"=="--portable-only" set "MODE=portable"
if /I "%~1"=="--installer-only" set "MODE=installer"
if /I "%~1"=="--exe-only" set "MODE=portable"
rem Preserve previously validated executables until replacements pass all checks.
echo OpenPDF Studio V%VERSION% build started > "%LOG%"
where py >nul 2>&1
if not errorlevel 1 (
  py -3.12 -c "import sys;assert sys.version_info[:2]==(3,12)" >nul 2>&1
  if not errorlevel 1 (
    set "PY_EXE=py"
    set "PY_ARGS=-3.12"
  )
)
if not defined PY_EXE if exist "%LocalAppData%\Programs\Python\Python312\python.exe" set "PY_EXE=%LocalAppData%\Programs\Python\Python312\python.exe"
if not defined PY_EXE if exist "%ProgramFiles%\Python312\python.exe" set "PY_EXE=%ProgramFiles%\Python312\python.exe"
if not defined PY_EXE if defined CI goto missing_python
if not defined PY_EXE (
  where winget >nul 2>&1 || goto missing_python
  winget install --id Python.Python.3.12 --exact --source winget --accept-package-agreements --accept-source-agreements >> "%LOG%" 2>&1 || goto fail
  if exist "%LocalAppData%\Programs\Python\Python312\python.exe" set "PY_EXE=%LocalAppData%\Programs\Python\Python312\python.exe"
)
if not defined PY_EXE goto missing_python
"%PY_EXE%" %PY_ARGS% -m venv .venv >> "%LOG%" 2>&1 || goto fail
set "VPY=%CD%\.venv\Scripts\python.exe"
rem Source-closure gate is static and fails before downloading/building dependencies.
"%VPY%" openpdf_source_closure_v502.py --root "%ROOT%" --entry openpdf_studio --entry openpdf_build_preflight --entry openpdf_release_gate --entry openpdf_bind_smoke --entry openpdf_publish_binary --entry openpdf_binary_manifest --required-manifest "%ROOT%\07-Manifestes\V50.2-REQUIRED-RUNTIME-MODULES.json" --report "%STAGE%\source-closure-v%VERSION%.json" >> "%LOG%" 2>&1 || goto fail
"%VPY%" -m pip install --upgrade pip >> "%LOG%" 2>&1 || goto fail
"%VPY%" -m pip install -r requirements-windows-v260.txt "pyinstaller>=6,<7" "Pillow>=10,<13" >> "%LOG%" 2>&1 || goto fail
"%VPY%" openpdf_build_preflight.py >> "%LOG%" 2>&1 || goto fail
"%VPY%" -m unittest test_openpdf_v402 test_openpdf_v385 test_openpdf_v384 >> "%LOG%" 2>&1 || goto fail
if /I "%MODE%"=="portable" goto portable
"%VPY%" -m PyInstaller --noconfirm --clean --windowed --onedir --name OpenPDF-Studio --collect-all fitz --collect-all pymupdf --hidden-import tkinter --add-data "..\VERSION.txt;." openpdf_studio.py >> "%LOG%" 2>&1 || goto fail
if not exist "dist\OpenPDF-Studio\OpenPDF-Studio.exe" goto fail
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0TEST-WINDOWS-BINARIES.ps1" -Mode installer -SourceDir "%CD%" -ReportPath "%STAGE%\windows-smoke-installer.json" >> "%LOG%" 2>&1 || goto fail
set "ISCC=%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
if not exist "%ISCC%" set "ISCC=%ProgramFiles%\Inno Setup 6\ISCC.exe"
if not exist "%ISCC%" set "ISCC=%LocalAppData%\Programs\Inno Setup 6\ISCC.exe"
if not exist "%ISCC%" if exist "C:\ProgramData\chocolatey\bin\ISCC.exe" set "ISCC=C:\ProgramData\chocolatey\bin\ISCC.exe"
if not exist "%ISCC%" if defined CI goto missing_inno
if not exist "%ISCC%" (
  where winget >nul 2>&1 || goto missing_inno
  winget install --id JRSoftware.InnoSetup --exact --source winget --accept-package-agreements --accept-source-agreements >> "%LOG%" 2>&1 || goto fail
)
if not exist "%ISCC%" set "ISCC=%LocalAppData%\Programs\Inno Setup 6\ISCC.exe"
if not exist "%ISCC%" if exist "C:\ProgramData\chocolatey\bin\ISCC.exe" set "ISCC=C:\ProgramData\chocolatey\bin\ISCC.exe"
if not exist "%ISCC%" goto missing_inno
"%ISCC%" "OpenPDF-Studio-V%VERSION%.iss" >> "%LOG%" 2>&1 || goto fail
if not exist "%STAGE%\OpenPDF-Studio-V%VERSION%-Setup.exe" goto fail
for %%F in ("%STAGE%\OpenPDF-Studio-V%VERSION%-Setup.exe") do if %%~zF LEQ 0 goto fail
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0TEST-WINDOWS-INSTALLATION.ps1" -SetupExe "%STAGE%\OpenPDF-Studio-V%VERSION%-Setup.exe" -ReportPath "%STAGE%\windows-installation-v%VERSION%.json" >> "%LOG%" 2>&1 || goto fail
if /I "%MODE%"=="installer" goto publish
:portable
"%VPY%" -m PyInstaller --noconfirm --clean --windowed --onefile --name OpenPDF-Studio-Portable-V%VERSION% --collect-all fitz --collect-all pymupdf --hidden-import tkinter --add-data "..\VERSION.txt;." --distpath "%STAGE%" openpdf_studio.py >> "%LOG%" 2>&1 || goto fail
if not exist "%STAGE%\OpenPDF-Studio-Portable-V%VERSION%.exe" goto fail
for %%F in ("%STAGE%\OpenPDF-Studio-Portable-V%VERSION%.exe") do if %%~zF LEQ 0 goto fail
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
if exist "%STAGE%\source-closure-v%VERSION%.json" copy /y "%STAGE%\source-closure-v%VERSION%.json" "%BINARY%\source-closure-v%VERSION%.json" >nul
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
if exist "%STAGE%\source-closure-v%VERSION%.json" copy /y "%STAGE%\source-closure-v%VERSION%.json" "%BINARY%\failed-source-closure-v%VERSION%.json" >nul
if exist "%STAGE%" rmdir /s /q "%STAGE%"
echo BUILD FAILED. See "%LOG%". No validated binary is claimed.
exit /b 1
