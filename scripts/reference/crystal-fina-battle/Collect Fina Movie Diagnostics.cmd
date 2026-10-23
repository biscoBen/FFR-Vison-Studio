@echo off
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0Collect Fina Movie Diagnostics.ps1" %*
echo.
pause
