#!/bin/bash

# Start the backend server
cd "$(dirname "$0")"
source venv/bin/activate
cd backend
export PYTHONPATH="$(pwd)/.."
python -m uvicorn main:app --host 0.0.0.0 --port 8000
