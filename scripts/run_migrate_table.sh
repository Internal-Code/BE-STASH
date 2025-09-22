#!/bin/sh
set -eu

show_help() {
    echo "Usage: sh scripts/run_migration.sh [ --env <environment> ] | [ --help ]"
    echo ""
    echo "--env       Set environment: dev | stg | prod"
    echo "--help, -h  Show this help message."
    exit 1
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
                    echo "Error: Invalid environment '$ENV'"
                    show_help
                    ;;
            esac
            ;;
        --help|-h)
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

# Load environment variables from file
export $(grep -v '^#' "$ENV_FILE" | xargs)
export ENV_TYPE="$ENV"

echo "Running table migration script with environment '$ENV' using $ENV_FILE..."

if ! uv run "$MIGRATION_CODE"; then
    echo "Migration failed for '$ENV'. Aborting."
    exit 1
fi
