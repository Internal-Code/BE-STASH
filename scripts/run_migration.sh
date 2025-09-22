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


ENV=""
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

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

if [ -z "$ENV" ]; then
    log "Error: --env is required"
    show_help
fi

log "Running all migrations for environment '$ENV'..."

# Run each migration script. If one fails, the script exits immediately.
sh "$PROJECT_DIR/scripts/run_migrate_table.sh" --env "$ENV"
sh "$PROJECT_DIR/scripts/run_migrate_country.sh" --env "$ENV"

log "All migrations completed successfully for environment '$ENV'."
