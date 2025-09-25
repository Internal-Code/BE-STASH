#!/bin/sh

show_help() {
  log "Usage: sh scripts/run_test.sh [ --env <env> ] [ --test <test_type> ] [ --help ]"
  log ""
  log "--env       Set environment: dev | stg"
  log "--test      Set test type: api | unit | e2e"
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
TEST_TYPE=""
TEST_DIR=""
ENV_FILE=""
COVERAGE_DIR="$PROJECT_DIR/coverages"

mkdir -p "$COVERAGE_DIR"
rm -rf "$COVERAGE_DIR"/*

# Combined argument parsing
while [ $# -gt 0 ]; do
  case "$1" in
    --env)
      shift
      ENV="$1"
      ;;
    --test)
      shift
      TEST_TYPE="$1"
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

# Validate env
case "$ENV" in
  dev)
    ENV_FILE="$PROJECT_DIR/env/.env.development"
    ;;
  stg)
    ENV_FILE="$PROJECT_DIR/env/.env.staging"
    ;;
  *)
    log "Error: Invalid or missing --env"
    show_help
    ;;
esac

# Validate test type
case "$TEST_TYPE" in
  api)
    TEST_DIR="$PROJECT_DIR/tests/api"
    ;;
  unit)
    TEST_DIR="$PROJECT_DIR/tests/unit"
    ;;
  e2e)
    TEST_DIR="$PROJECT_DIR/tests/e2e"
    ;;
  *)
    log "Error: Invalid or missing --test"
    show_help
    ;;
esac

[ ! -d "$TEST_DIR" ] && log_error "Error: Test directory not found: $TEST_DIR" && exit 1
[ ! -f "$ENV_FILE" ] && log_error "Environment file not found: $ENV_FILE" && exit 1

# Load env vars
export ENV_FILE="$ENV_FILE"
export $(grep -v '^#' "$ENV_FILE" | xargs)

# Activate venv
log "Checking OS Environment"
if uname | grep -qiE "linux|darwin"; then
  log "Unix-based OS detected"
  . "$PROJECT_DIR/.venv/bin/activate"
else
  log_error "Unsupported OS. Please turn-on server manually."
  exit 1
fi

# Run tests
log "Running $TEST_TYPE tests in $TEST_DIR with env $ENV_FILE"

if ! coverage run --data-file="$COVERAGE_DIR/.coverage" --source="$TEST_DIR" -m pytest "$TEST_DIR"; then
  log_error "Tests failed!"
  exit 1
fi

log "Generating coverage report"
coverage report -m --skip-empty --data-file="$COVERAGE_DIR/.coverages"
coverage html -d "$COVERAGE_DIR" --data-file="$COVERAGE_DIR/.coverages"

log "HTML coverage report generated at $COVERAGE_DIR/index.html"
