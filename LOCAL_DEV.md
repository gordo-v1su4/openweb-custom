# Local Development Guide (uv + venv)

This guide shows how to run the Qwen API service locally using `uv` and a virtual environment for faster development iteration.

## Prerequisites

- Python 3.9+ installed
- `uv` installed (fast Python package installer)
  ```bash
  curl -LsSf https://astral.sh/uv/install.sh | sh
  ```

## Quick Start

### Option 1: Using the Script (Easiest)

```bash
cd qwen-api-service
./run_local.sh
```

This script will:
- Check for `uv` installation
- Create a virtual environment
- Install dependencies
- Load environment variables from `.env`
- Start the service

### Option 2: Manual Setup

```bash
cd qwen-api-service

# Create virtual environment
uv venv

# Activate venv
source venv/bin/activate

# Install dependencies
uv pip install -r requirements.txt

# Load environment variables
export $(cat ../.env | grep -v '^#' | xargs)

# Create model directories
mkdir -p models/huggingface models/loras

# Run the service
python app.py
```

## Environment Variables

Make sure your `.env` file has:

```env
HF_TOKEN=your-huggingface-token
USE_HUGGINGFACE=true
HUGGINGFACE_MODEL_ID=Qwen/Qwen2-VL-2B-Instruct
```

## Testing the Service

Once running, test the endpoints:

```bash
# Health check
curl http://localhost:8081/health

# List models
curl http://localhost:8081/api/v1/models

# Test camera edit (requires base64 image)
curl -X POST http://localhost:8081/api/v1/camera-edit \
  -H "Content-Type: application/json" \
  -d '{
    "image": "base64_encoded_image",
    "camera_preset": "Front View",
    "lighting": "Cinematic",
    "steps": 8
  }'
```

## Development Workflow

### Making Code Changes

1. Edit `app.py` or other files
2. The service will need to be restarted to pick up changes
3. Press `Ctrl+C` to stop
4. Run `./run_local.sh` again

### Installing New Dependencies

```bash
# Activate venv
source venv/bin/activate

# Install new package
uv pip install package-name

# Update requirements.txt
uv pip freeze > requirements.txt
```

### Running Tests

```bash
source venv/bin/activate
python -m pytest tests/  # if you add tests
```

## Running OpenWebUI Separately

For full stack testing, you can:

1. **Run Qwen API locally** (this guide)
2. **Run OpenWebUI via Docker/Podman**:
   ```bash
   # In project root
   docker-compose up open-webui
   ```

   Update `.env` or docker-compose to point OpenWebUI to:
   ```env
   QWEN_API_URL=http://host.docker.internal:8081
   ```

   Or use your Mac's IP address if needed.

## Troubleshooting

### uv not found
```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Reload shell
source ~/.zshrc
```

### Port already in use
```bash
# Find what's using port 8081
lsof -i :8081

# Kill the process or change PORT in .env
export PORT=8082
```

### Model download issues
- Check `HF_TOKEN` is set correctly
- Check internet connection
- Models download on first run (can take 10-30 minutes)
- Check logs for Hugging Face errors

### Virtual environment issues
```bash
# Remove and recreate venv
rm -rf venv
uv venv
source venv/bin/activate
uv pip install -r requirements.txt
```

## Advantages of Local Development

- ✅ Faster iteration (no Docker rebuild)
- ✅ Easier debugging (direct Python access)
- ✅ Better IDE integration
- ✅ Faster startup (no container overhead)
- ✅ Direct access to logs

## When to Use Docker/Podman

Use Docker/Podman for:
- Full stack testing (both services together)
- Production-like environment testing
- Testing Docker builds before deployment

