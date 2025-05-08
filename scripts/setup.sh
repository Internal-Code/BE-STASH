#!/bin/bash

# Change virtualenv dir location into root project dir and install dependencies
echo "Configuring virtual environment location and installing dependencies..."
uv sync

echo "Setup complete."
