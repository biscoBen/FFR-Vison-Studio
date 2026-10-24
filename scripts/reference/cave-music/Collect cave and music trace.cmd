@echo off
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0Movie Playback Trace.ps1" -Action Collect
echo.
pause
