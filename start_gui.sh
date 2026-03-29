#!/bin/bash
cd "$(dirname "$0")"

# Install deps
if [ -d "venv" ]; then
    ./venv/bin/pip install -r requirements.txt --quiet 2>/dev/null
    ./venv/bin/python gui.py
else
    pip3 install -r requirements.txt --quiet 2>/dev/null
    python3 gui.py
fi
