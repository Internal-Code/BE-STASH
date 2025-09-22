#!/bin/sh
set -eu

show_help() {
    log "Usage: sh scripts/run_migration.sh [ --env <environment> ] | [ --help ]"
    log ""
    log "--env       Set environment: dev | stg | prod"
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
MIGRATION_CODE="$PROJECT_DIR/services/postgre/migrations/migrate_table.py"

ENV=""
ENV_FILE=""

# Parse arguments
while [ $# -gt 0 ]; do
    case "$1" in
        --env)
            shift
            ENV="$1"
            case "$ENV" in
                dev)
                    ENV_FILE="$PROJECT_DIR/env/.env.development"
                    ;;
                stg)
                    ENV_FILE="$PROJECT_DIR/env/.env.staging"
                    ;;
                prod)
                    ENV_FILE="$PROJECT_DIR/env/.env.production"
                    ;;
                *)
                    log "Error: Invalid environment '$ENV'"
                    show_help
                    ;;
            esac
            ;;
        --help|-h)
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

# Load environment variables from file
export $(grep -v '^#' "$ENV_FILE" | xargs)
export ENV_TYPE="$ENV"

log "Running table migration script with environment '$ENV' using $ENV_FILE..."

if ! uv run "$MIGRATION_CODE"; then
    log_error "Migration failed for '$ENV'. Aborting."
    exit 1
fi
