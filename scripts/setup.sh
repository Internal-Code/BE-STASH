#!/bin/bash

log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') INFO $1"
}

log "Configuring virtual environment location and installing dependencies..."
uv sync

log "Setup complete."
