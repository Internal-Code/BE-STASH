#!/bin/sh

# Default value
HOST="127.0.0.1"
ENV_FILE="env/.env.development"

# Checking for existing processes on port 8000
echo "Checking for existing processes on port 8000"
PIDS=$(lsof -ti :8000)
if [ -n "$PIDS" ]; then
  echo "Killing existing processes on port 8000"
  kill -9 $PIDS
fi

# Show usage information
show_help() {
  echo "Usage: sh $0 [ --development | --staging | --production | --help ]"
  echo ""
  echo "--development    Run the server on localhost and load the .env.development file"
  echo "--staging        Run the server on the staging IP and load the .env.staging file"
  echo "--production     Run the server on the production IP address and load the .env.production file"
  echo "--help           Show this help message"
}

# Check command-line arguments
if [ "$1" = "--help" ]; then
  show_help
  exit 0
fi

# Parse arguments
case "$1" in
  --development)
    echo "Using development environment configuration"
    ENV_FILE="env/.env.development"
    HOST="127.0.0.1"
    ;;
  --staging)
    echo "Using staging environment configuration"
    ENV_FILE="env/.env.staging"
    CURRENT_IP=$(hostname -I | awk '{print $1}')
    if [ -z "$CURRENT_IP" ]; then
      echo "Unable to detect current IP address! Using default host"
    else
      HOST="$CURRENT_IP"
    fi
    ;;
  --production)
    echo "Using production environment configuration"
    CURRENT_IP=$(hostname -I | awk '{print $1}')
    if [ -z "$CURRENT_IP" ]; then
      echo "Unable to detect current IP address! Using default host"
    else
      HOST="$CURRENT_IP"
    fi
    ENV_FILE="env/.env.production"
    ;;
  *)
    echo "Invalid option: $1"
    show_help
    exit 1
    ;;
esac

#Load the environment variables using the external script
export $(grep -v '^#' $ENV_FILE | xargs)
sh ./scripts/load_env.sh

# Activate virtualenv
sh ./scripts/activate.sh

# Start the server
echo "Running uvicorn server in debug mode"
uvicorn src.main:app --host "$HOST" --port 8000 --reload --reload-dir=src
