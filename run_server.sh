#!/bin/bash
source .venv/bin/activate

echo "Installing missing dependencies"
poetry install --no-root

echo "Package installation success"

echo "Running uvicorn server (debug mode)"
uvicorn src.main:app --reload