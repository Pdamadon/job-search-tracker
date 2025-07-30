#!/bin/bash

# Start script for Railway deployment
# Handles PORT environment variable properly

# Default to port 8000 if PORT is not set
PORT=${PORT:-8000}

echo "Starting server on port $PORT"

# Start the FastAPI server
uvicorn backend.app:app --host 0.0.0.0 --port $PORT