#!/bin/sh

# Load the environment variables
if [ -f "$ENV_FILE" ]; then
  echo "Loading environment variables from $ENV_FILE"
  set -a
  . "$ENV_FILE"
  set +a
else
  echo "Environment file $ENV_FILE not found!"
  exit 1
fi
