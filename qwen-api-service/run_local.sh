#!/bin/bash
# Run Qwen API service locally with uv and venv

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Setting up Qwen API service locally...${NC}"

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "❌ uv is not installed. Install it with:"
    echo "   curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

# Check if .env exists
if [ ! -f ../.env ]; then
    echo "⚠️  .env file not found. Copying from .env.example..."
    cp ../.env.example ../.env
    echo "📝 Please edit ../.env and add your HF_TOKEN"
    exit 1
fi

# Load environment variables
export $(cat ../.env | grep -v '^#' | xargs)

# Create venv if it doesn't exist (uv creates .venv by default)
if [ ! -d ".venv" ] && [ ! -d "venv" ]; then
    echo -e "${GREEN}📦 Creating virtual environment...${NC}"
    uv venv
fi

# Activate venv (uv creates .venv, but check for both)
echo -e "${GREEN}🔌 Activating virtual environment...${NC}"
if [ -d ".venv" ]; then
    source .venv/bin/activate
elif [ -d "venv" ]; then
    source venv/bin/activate
else
    echo "❌ Virtual environment not found!"
    exit 1
fi

# Install dependencies
echo -e "${GREEN}📥 Installing dependencies with uv...${NC}"
uv pip install -r requirements.txt

# Create models directory
mkdir -p models/huggingface models/loras

# Check if port is in use (but allow gvproxy - that's Podman's proxy)
PORT=${PORT:-8081}
PORT_IN_USE=$(lsof -Pi :$PORT -sTCP:LISTEN -t 2>/dev/null | grep -v "gvproxy" || true)
if [ ! -z "$PORT_IN_USE" ]; then
    echo -e "${BLUE}⚠️  Port $PORT is already in use${NC}"
    echo "   Checking what's using it..."
    lsof -i :$PORT | grep -v "gvproxy" || true
    echo ""
    echo "   Options:"
    echo "   1. Stop the existing service"
    echo "   2. Use a different port: PORT=8082 ./run_local.sh"
    exit 1
fi

# Run the service
echo -e "${GREEN}🎬 Starting Qwen API service on port $PORT...${NC}"
echo -e "${BLUE}   Health check: http://localhost:$PORT/health${NC}"
echo -e "${BLUE}   Models API: http://localhost:$PORT/api/v1/models${NC}"
echo ""
echo "Press Ctrl+C to stop"
echo ""

python app.py

