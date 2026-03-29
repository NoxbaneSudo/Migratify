#!/bin/bash
cd "$(dirname "$0")"

# Используем venv если есть, иначе системный python
if [ -f "venv/bin/python" ]; then
    venv/bin/python migrate.py
else
    python3 migrate.py
fi

read -p "Press Enter to exit..."
