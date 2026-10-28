@echo off
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0Collect Resonance Crash.ps1" -WatchGame -OpenOutput %*
if errorlevel 1 (
  echo.
  pause
)
