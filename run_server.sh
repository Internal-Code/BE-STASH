#!/bin/sh
echo "Installing missing dependencies"
pip install -r src/requirements/dev.txt --quiet

echo "Package installation success"

echo "Running uvicorn server (debug mode)"
uvicorn src.main:app --reload