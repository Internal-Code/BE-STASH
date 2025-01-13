#!/bin/sh

# Function to show the help message
show_help() {
  echo "Usage: sh $0 [ --development | --staging | --production | --help ]"
  echo ""
  echo "--development   Use .env.development file for environment variables."
  echo "--staging       Use .env.staging file for environment variables."
  echo "--production    Use .env.production file for environment variables."
  echo "--help          Show this help message."
}

# Parse the command-line arguments
case $1 in
    --development)
        echo "Using development environment configuration"
        ENV_FILE="./env/.env.development"
        shift
        ;;
    --staging)
        echo "Using staging environment configuration"
        ENV_FILE="./env/.env.staging"
        shift
        ;;
    --production)
        echo "Using production environment configuration"
        ENV_FILE="./env/.env.production"
        shift
        ;;
    --help)
        show_help
        exit 0
        ;;
    *)
        echo "Unknown parameter: $1"
        show_help
        exit 1
        ;;
esac

export ENV_FILE
sh ./scripts/load_env.sh

# Run the Docker container using the appropriate environment settings
echo "Starting container with environment variables from $ENV_FILE..."
docker-compose --env-file $ENV_FILE up -d
