#!/bin/bash

# Change virtualenv dir location into root project dir and install dependencies
echo "Configuring virtual environment location and installing dependencies..."
poetry config virtualenvs.in-project true && poetry install --no-root

echo "Setup complete."
