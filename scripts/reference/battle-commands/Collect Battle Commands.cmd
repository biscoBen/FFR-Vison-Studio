@echo off
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0Battle Command Diagnostics.ps1" -Action Collect %*
echo.
pause
