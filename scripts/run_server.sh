#!/bin/sh

show_help() {
    echo "Usage: sh scripts/run_server.sh [ --env <environment> ] | [ --help ]"
    echo ""
    echo "--env       Set project environment: dev | test"
    echo "--help, -h  Show this help message."
    exit 1
}

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

ENV=""
ENV_FILE=""
RELOAD_FLAG=""

while [ $# -gt 0 ]; do
    case "$1" in
    --env)
        shift
        ENV="$1"
        case "$ENV" in
        dev)
            ENV_FILE="$PROJECT_DIR/env/.env.development"
            RELOAD_FLAG="--reload"
            ;;
        test)
            ENV_FILE="$PROJECT_DIR/env/.env.test"
            RELOAD_FLAG="--reload"
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

export ENV_TYPE="$ENV"
export ENV_FILE="$ENV_FILE"
export $(grep -v '^#' "$ENV_FILE" | xargs)

echo "Checking OS Environment"
if uname | grep -qiE "linux|darwin"; then
    echo "Unix-based OS detected"
    . "$PROJECT_DIR/.venv/bin/activate"
else
    echo "Unsupported OS. Please turn-on server manually."
    exit 1
fi

echo "Running uvicorn server with environment variables from $ENV_FILE..."
uvicorn src.main:app $RELOAD_FLAG
