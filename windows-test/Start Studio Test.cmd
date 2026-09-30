@echo off
setlocal
title Sephira Studio Test
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0Launch Studio Test.ps1"
if errorlevel 1 pause
