#!/bin/sh

echo "Installing missing dependencies"
pip install -r requirements.txt --quiet

echo "Package installation success"

echo "Running uvicorn server (debug mode)"
uvicorn api.app:app --reload