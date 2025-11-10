#!/bin/bash

# Start Backend Server with uv
echo "🚀 Starting FastAPI backend server with uv..."

# Load environment variables from .env if it exists
if [ -f .env ]; then
	echo "Loading environment variables from .env..."
	# Read .env file line by line and export variables
	while IFS= read -r line || [ -n "$line" ]; do
		# Skip comments and empty lines
		if [[ "$line" =~ ^[[:space:]]*# ]] || [[ -z "$line" ]]; then
			continue
		fi
		# Export KEY=value pairs
		if [[ "$line" =~ ^[[:space:]]*([^=]+)=(.*)$ ]]; then
			key="${BASH_REMATCH[1]}"
			value="${BASH_REMATCH[2]}"
			# Remove quotes if present
			value="${value#\"}"
			value="${value%\"}"
			value="${value#\'}"
			value="${value%\'}"
			export "$key=$value"
		fi
	done < .env
fi

# Check if uv is installed
if ! command -v uv &>/dev/null; then
	echo "❗️Error: uv is required but not installed or not found in PATH."
	echo "Install uv with: curl -LsSf https://astral.sh/uv/install.sh | sh"
	exit 1
fi

# Check if we're in the project root directory
if [ ! -f "pyproject.toml" ] && [ ! -f "requirements.txt" ]; then
	echo "❗️Error: Please run this script from the project root directory."
	echo "Usage: ./start-backend.sh"
	exit 1
fi

# Create venv if it doesn't exist. By default, uv creates a .venv directory
if [ ! -d ".venv" ]; then
	echo "Creating Python virtual environment (.venv)..."
	if [ -z "$UV_PYTHON_VERSION" ]; then
		echo "⚠️ UV_PYTHON_VERSION is not set. Using default Python 3.11"
		UV_PYTHON_VERSION="3.11"
	fi
	uv venv --python $UV_PYTHON_VERSION
fi

# Install dependencies with uv
echo "Installing Python dependencies with uv..."
if [ -f "pyproject.toml" ]; then
	uv sync
elif [ -f "requirements.txt" ]; then
	echo "Installing dependencies from requirements.txt..."
	uv pip install -r requirements.txt
else
	echo "❗️Error: No pyproject.toml or requirements.txt found."
	exit 1
fi

# Set PYTHONPATH for backend imports
export PYTHONPATH="$(pwd)/backend/src:$PYTHONPATH"

# Start the server
echo "🌐 Backend server starting on http://localhost:8000"
echo "📚 API documentation available at http://localhost:8000/docs"
echo "🛑 Press Ctrl+C to stop the server"

if [ -z "$APP_HOST" ]; then
	echo "⚠️ APP_HOST is not set. Using default host 0.0.0.0"
	APP_HOST="0.0.0.0"
fi

if [ -z "$APP_PORT" ]; then
	echo "⚠️ APP_PORT is not set. Using default port 8000"
	APP_PORT="8000"
fi

uv run uvicorn api.v2.main:app --reload --host $APP_HOST --port $APP_PORT

