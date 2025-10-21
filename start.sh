#!/bin/bash

# Create data directory if it doesn't exist
mkdir -p data

# Start the application
uvicorn api.main:app --host 0.0.0.0 --port $PORT