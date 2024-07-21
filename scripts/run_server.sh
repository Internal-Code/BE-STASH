#!/bin/bash

echo "Checking OS Environment"
case "$OSTYPE" in
  linux*)   
    echo "Linux based OS detected"
    . .venv/bin/activate
    ;;
  cygwin* | msys* | mingw*)  
    echo "Windows based OS detected"
    source .venv/Scripts/activate
    ;;
  *)
    echo "Unsupported OS detected. This feature is not developed yet."
    exit 1
    ;;
esac

echo "Running uvicorn server (debug mode)"
uvicorn src.main:app --reload