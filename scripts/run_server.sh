#!/bin/bash

echo "Checking for existing processes on port 8000"
PIDS=$(lsof -ti :8000)
if [ -n "$PIDS" ]; then
  echo "Killing existing processes on port 8000"
  kill -9 $PIDS
fi

echo "Checking OS Environment"
if grep -qEi "(Microsoft|WSL)" /proc/version &>/dev/null; then
  echo "WSL detected"
  . .venv/bin/activate
else
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
fi


echo "Running uvicorn server (debug mode)"
uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
