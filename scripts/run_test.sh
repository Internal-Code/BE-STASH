#!/bin/sh

show_help() {
  echo "Usage: sh scripts/run_test.sh [ --env <env> ] [ --test <test_type> ] [ --help ]"
  echo ""
  echo "--env       Set environment: dev | stg"
  echo "--test      Set test type: api | unit | feature"
  echo "--help, -h  Show this help message."
  exit 1
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
      echo "Error: Unknown argument '$1'"
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
    echo "Error: Invalid or missing --env"
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
  *)
    echo "Error: Invalid or missing --test"
    show_help
    ;;
esac

[ ! -d "$TEST_DIR" ] && echo "Error: Test directory not found: $TEST_DIR" && exit 1
[ ! -f "$ENV_FILE" ] && echo "Environment file not found: $ENV_FILE" && exit 1

# Load env vars
export ENV_FILE="$ENV_FILE"
export $(grep -v '^#' "$ENV_FILE" | xargs)

# Activate venv
echo "Checking OS Environment"
if uname | grep -qiE "linux|darwin"; then
  echo "Unix-based OS detected"
  . "$PROJECT_DIR/.venv/bin/activate"
else
  echo "Unsupported OS. Please turn-on server manually."
  exit 1
fi

# Run tests
echo "Running $TEST_TYPE tests in $TEST_DIR with env $ENV_FILE"

if ! coverage run --data-file="$COVERAGE_DIR/.coverage" --source="$TEST_DIR" -m pytest "$TEST_DIR"; then
  echo "Tests failed!"
  exit 1
fi

echo "Generating coverage report"
coverage report -m --skip-empty --data-file="$COVERAGE_DIR/.coverages"
coverage html -d "$COVERAGE_DIR" --data-file="$COVERAGE_DIR/.coverages"

echo "HTML coverage report generated at $COVERAGE_DIR/index.html"
