@echo off
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0Collect Shrine Schemas.ps1" %*
pause
