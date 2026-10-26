@echo off
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0Esper Mastery Diagnostics.ps1" -Action Disable %*
echo.
pause
