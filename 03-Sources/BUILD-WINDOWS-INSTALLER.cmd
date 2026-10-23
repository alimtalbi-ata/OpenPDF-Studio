@echo off
rem Compatibility shim. Canonical Windows build lives in 02-Compilation.
rem Author: Abdelhalim Talbi. No independent version or build logic here.
setlocal EnableExtensions DisableDelayedExpansion
call "%~dp0..\02-Compilation\BUILD-WINDOWS-INSTALLER.cmd" %*
exit /b %errorlevel%
