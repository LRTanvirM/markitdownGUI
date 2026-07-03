@echo off
rem Double-click to install MarkItDown (per-user, no admin needed).
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0Install-MarkItDown.ps1"
echo.
pause
