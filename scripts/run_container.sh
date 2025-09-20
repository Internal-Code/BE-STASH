#!/bin/sh

show_help() {
    echo "Usage: sh scripts/run_container.sh [ --env <environment> ] | [ --help ]"
    echo ""
    echo "--env       Set project environment: dev | test"
    echo "--help, -h  Show this help message."
    exit 1
}

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

ENV=""
ENV_FILE=""

while [ $# -gt 0 ]; do
    case "$1" in
    --env)
        shift
        ENV="$1"
        case "$ENV" in
        dev)
            ENV_FILE="$PROJECT_DIR/env/.env.development"
            ;;
        test)
            ENV_FILE="$PROJECT_DIR/env/.env.test"
            ;;
        *)
            echo "Error: Invalid environment '$ENV'"
            show_help
            ;;
        esac
        ;;
    --help | -h)
        show_help
        ;;
    *)
        echo "Error: Unknown argument '$1'"
        show_help
        ;;
    esac
    shift
done

if [ -z "$ENV_FILE" ]; then
    echo "Error: --env is required"
    show_help
fi

if [ ! -f "$ENV_FILE" ]; then
  echo "Environment file not found: $ENV_FILE"
  exit 1
fi

echo "Using env file: $ENV_FILE"
echo "Starting container with environment variables from $ENV_FILE..."

docker compose --env-file "$ENV_FILE" up -d
