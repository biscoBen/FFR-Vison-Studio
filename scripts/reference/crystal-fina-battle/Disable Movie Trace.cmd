@echo off
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0Movie Playback Trace.ps1" -Action Disable %*
echo.
pause
