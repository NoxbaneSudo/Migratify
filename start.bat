@echo off
title Migratify
cd /d "%~dp0"

:: Проверяем, есть ли venv, если нет — ставим зависимости глобально
if exist "venv\Scripts\python.exe" (
    venv\Scripts\python.exe migrate.py
) else (
    python migrate.py
)

pause
