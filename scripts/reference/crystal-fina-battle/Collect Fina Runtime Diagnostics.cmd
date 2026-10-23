@echo off
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0Collect Fina Runtime Diagnostics.ps1" %*
echo.
pause
