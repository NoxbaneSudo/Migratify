@echo off
title Migratify GUI
cd /d "%~dp0"

:: Install dependencies if needed
if exist "venv\Scripts\python.exe" (
    venv\Scripts\pip.exe install -r requirements.txt --quiet 2>nul
    venv\Scripts\python.exe gui.py
) else (
    pip install -r requirements.txt --quiet 2>nul
    python gui.py
)

pause
