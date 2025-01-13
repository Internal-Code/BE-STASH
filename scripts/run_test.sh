#!/bin/sh

show_help() {
  echo "Usage: sh $0 [ --development | --staging ] [--unit_test | --api_test | --e2e | --help ]"
  echo ""
  echo "Environment Options:"
  echo "  --development    Set the environment to development."
  echo "  --staging        Set the environment to staging."
  echo ""
  echo "Test Options:"
  echo "  --unit_test      Run unit tests located in tests/unit_test."
  echo "  --api_test       Run API tests located in tests/api_test."
  echo "  --e2e            Run end-to-end tests located in tests/e2e."
  echo ""
  echo "--help             Show this help message."
}

# Default values for environment and test type
ENV_FILE=""
TEST_DIR=""

# Parse arguments
while [ $# -gt 0 ]; do
  case "$1" in
    --development)
      ENV_FILE="env/.env.development"
      ;;
    --staging)
      ENV_FILE="env/.env.staging"
      ;;
    --unit_test)
      TEST_DIR="tests/unit_test"
      ;;
    --api_test)
      TEST_DIR="tests/api_test"
      ;;
    --e2e)
      TEST_DIR="tests/e2e"
      ;;
    --help)
      show_help
      exit 0
      ;;
    *)
      echo "Invalid option: $1"
      show_help
      exit 1
      ;;
  esac
  shift
done

# Validate inputs
if [ -z "$ENV_FILE" ]; then
  echo "Error: No environment specified. Please provide one of --development, or --staging."
  show_help
  exit 1
fi

if [ -z "$TEST_DIR" ]; then
  echo "Error: No test type specified. Please provide one of --unit_test, --api_test, or --e2e."
  show_help
  exit 1
fi

# Load environment variables
set -a
while IFS='=' read -r key value; do
  # Skip comments and empty lines
  if [ -n "$key" ] && [ "${key#\#}" != "$key" ]; then
    # Preserve multi-word values by quoting them
    export "$key=$value"
  fi
done < "$ENV_FILE"
set +a
sh ./scripts/load_env.sh

# Activate the virtual environment
sh ./scripts/activate.sh

# Run the tests
echo "Running tests in $TEST_DIR on $ENV_FILE environment"
if ! coverage run -m  --source=$TEST_DIR pytest $TEST_DIR --verbose; then
  echo "Tests failed!"
  exit 1
fi

# Generate the coverage report
echo "Generating coverage report"
coverage report -m --skip-empty
coverage html

echo "Test finished"
