@echo off
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0Collect Vision Save Check.ps1" %*
echo.
pause
