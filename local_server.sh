#!/bin/sh
echo "Installing all dependencies"
pip install -r requirements.txt

echo "running uvicorn server (debug mode)"
uvicorn api.app:app --reload