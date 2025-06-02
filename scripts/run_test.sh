#!/bin/sh

show_help() {
  echo "Usage: sh scripts/run_test.sh [ --env <environment> ] | [ --test <test_type> ] | [ --help ]"
  echo ""
  echo "--env       Set project environment: dev | test"
  echo "--test      Set test type: api | unit | e2e"
  echo "--help, -h  Show this help message."
  exit 1
}

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

TEST_TYPE=""
TEST_DIR=""
ENV=""
ENV_FILE=""

COVERAGE_DIR="$PROJECT_DIR/coverage"
mkdir -p "$COVERAGE_DIR"

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
  --test)
    shift
    TEST_TYPE="$1"
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
      echo "Error: Invalid test type '$TEST_TYPE'"
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

if [ -z "$TEST_DIR" ]; then
  echo "Error: --test is required"
  show_help
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

echo "Running tests in $TEST_DIR on $ENV environment"
if ! coverage run --data-file="$COVERAGE_DIR/.coverage" --source="$TEST_DIR" -m pytest "$TEST_DIR" --verbose; then
  echo "Tests failed!"
  exit 1
fi

echo "Generating coverage report"
coverage report -m --skip-empty --data-file="$COVERAGE_DIR/.coverage"
coverage html -d "$COVERAGE_DIR" --data-file="$COVERAGE_DIR/.coverage"

echo "HTML coverage report generated at $COVERAGE_DIR/index.html"
