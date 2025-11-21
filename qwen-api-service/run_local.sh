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

# Create venv if it doesn't exist
if [ ! -d "venv" ]; then
    echo -e "${GREEN}📦 Creating virtual environment...${NC}"
    uv venv
fi

# Activate venv
echo -e "${GREEN}🔌 Activating virtual environment...${NC}"
source venv/bin/activate

# Install dependencies
echo -e "${GREEN}📥 Installing dependencies with uv...${NC}"
uv pip install -r requirements.txt

# Create models directory
mkdir -p models/huggingface models/loras

# Run the service
echo -e "${GREEN}🎬 Starting Qwen API service on port 8081...${NC}"
echo -e "${BLUE}   Health check: http://localhost:8081/health${NC}"
echo -e "${BLUE}   Models API: http://localhost:8081/api/v1/models${NC}"
echo ""
echo "Press Ctrl+C to stop"
echo ""

python app.py

