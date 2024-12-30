#!/bin/sh

# Default host value
HOST="127.0.0.1"

# Check command-line arguments
if [ "$1" = "--prod" ]; then
  echo "Using production environment configuration"
  CURRENT_IP=$(hostname -I | awk '{print $1}')
  if [ -z "$CURRENT_IP" ]; then
    echo "Unable to detect current IP address! Using default host"
  else
    HOST="$CURRENT_IP"
  fi
else
  # Default to local if no argument or if --local is passed
  echo "Using local environment configuration"
fi

# Checking for existing processes on port 8000
echo "Checking for existing processes on port 8000"
PIDS=$(lsof -ti :8000)
if [ -n "$PIDS" ]; then
  echo "Killing existing processes on port 8000"
  kill -9 $PIDS
fi

# Checking OS Environment
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
      . .venv/Scripts/activate
      ;;
    *)
      echo "Unsupported OS detected. This feature is not developed yet."
      exit 1
      ;;
  esac
fi

echo "Running uvicorn server in debug mode"
uvicorn src.main:app --host "$HOST" --port 8000 --reload
