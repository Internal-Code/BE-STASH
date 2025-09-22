#!/bin/sh

show_help() {
    log "Usage: sh scripts/run_server.sh [ --env <environment> ] [ --port <port> ] | [ --help ]"
    log ""
    log "--env       Set environment: dev | stg | prod"
    log "--port      Set port (default: 8000)"
    log "--help, -h  Show this help message."
    exit 1
}

log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') INFO $1"
}

log_error() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') ERROR $1" >&2
}

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

ENV=""
ENV_FILE=""
RELOAD_FLAG=""
IP_HOST=""
PORT=8000

while [ $# -gt 0 ]; do
    case "$1" in
    --env)
        shift
        ENV="$1"
        case "$ENV" in
        dev)
            ENV_FILE="$PROJECT_DIR/env/.env.development"
            RELOAD_FLAG="--reload"
            IP_HOST="127.0.0.1"
            ;;
        stg)
            ENV_FILE="$PROJECT_DIR/env/.env.staging"
            RELOAD_FLAG=""
            IP_HOST="127.0.0.1"
            ;;
        prod)
            ENV_FILE="$PROJECT_DIR/env/.env.production"
            RELOAD_FLAG=""
            IP_HOST="127.0.0.1"
            ;;
        *)
            log "Error: Invalid environment '$ENV'"
            show_help
            ;;
        esac
        ;;
    --port)
        shift
        if ! log "$1" | grep -Eq '^[0-9]+$'; then
            log "Error: --port requires an integer value"
            show_help
        fi
        PORT="$1"
        ;;
    --help | -h)
        show_help
        ;;
    *)
        log "Error: Unknown argument '$1'"
        show_help
        ;;
    esac
    shift
done

if [ -z "$ENV_FILE" ]; then
    log "Error: --env is required"
    show_help
fi

if [ ! -f "$ENV_FILE" ]; then
    log_error "Environment file not found: $ENV_FILE"
    exit 1
fi

export ENV_TYPE="$ENV"
export ENV_FILE="$ENV_FILE"
export $(grep -v '^#' "$ENV_FILE" | xargs)

log "Checking OS Environment"
if uname | grep -qiE "linux|darwin"; then
    log "Unix-based OS detected"
    . "$PROJECT_DIR/.venv/bin/activate"
else
    log_error "Unsupported OS. Please turn-on server manually."
    exit 1
fi

log "Running uvicorn server on $IP_HOST:$PORT with environment variables from $ENV_FILE..."
uvicorn src.main:app $RELOAD_FLAG --host "$IP_HOST" --port "$PORT"
