# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Project Overview

This project integrates Qwen Image Edit models with OpenWebUI using a Robyn-based API service. It provides camera control presets and lighting effects for AI image editing through a REST API.

**Architecture:**
- **qwen-api-service/**: Robyn-based Python REST API that loads Qwen models and handles image editing requests
- **OpenWebUI**: Frontend interface that connects to the Qwen API via custom tools
- **Model Sources**: Primary downloads from Hugging Face Hub, with MinIO S3 fallback for custom models
- **Deployment**: Docker Compose for local testing, Coolify for production

## Common Commands

### Local Development (Fast Iteration)
```bash
# Run API service locally with uv + venv
cd qwen-api-service
./run_local.sh

# Manual setup if needed
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt
python app.py
```

### Docker Compose (Full Stack Testing)
```bash
# Start both services (OpenWebUI + Qwen API)
docker-compose up -d

# View logs
docker-compose logs -f qwen-api
docker-compose logs -f open-webui

# Rebuild after code changes
docker-compose up -d --build qwen-api

# Stop services
docker-compose down

# Stop and clear volumes (removes model cache)
docker-compose down -v
```

### Testing
```bash
# Test API endpoints with provided script
python test_endpoint.py [optional_image_path]

# Install test dependencies first
pip install -r requirements-test.txt

# Health check
curl http://localhost:8081/health

# List loaded models
curl http://localhost:8081/api/v1/models

# Test camera edit endpoint
curl -X POST http://localhost:8081/api/v1/camera-edit \
  -H "Content-Type: application/json" \
  -d '{"image": "base64_data", "camera_preset": "Front View", "lighting": "Cinematic", "steps": 8}'
```

## Code Architecture

### API Service (`qwen-api-service/app.py`)
- **Framework**: Robyn (async Python web framework)
- **Model Loading**: 
  - Primary: Downloads models directly from Hugging Face Hub using `snapshot_download` for parallel fetching
  - Fallback: MinIO S3 for custom models/LoRAs
  - Models cached in `/app/models` (Docker) or `qwen-api-service/models` (local)
- **Key Functions**:
  - `load_models_from_huggingface()`: Downloads and loads models from HF Hub
  - `load_models_from_minio()`: Fallback loader for custom models from S3
  - `load_models()`: Orchestrates primary/fallback loading strategy

### API Endpoints
- `GET /health`: Health check
- `POST /api/v1/camera-edit`: Camera preset-based image editing (recommended)
- `POST /api/v1/edit`: Generic prompt-based image editing
- `GET /api/v1/models`: List loaded models and their sources

### OpenWebUI Tool (`tools/qwen_camera_studio.py`)
- Provides 50+ camera presets (Front View, Profile, Dolly, Orbit, FPV Drone, etc.)
- Lighting presets (Cinematic, Soft Natural, Studio, Sunset, Neon, Volumetric)
- Uses bilingual prompts (Chinese + English) for better model understanding
- Returns before/after comparison HTML view

### Camera Preset System
Camera presets combine Chinese and English instructions because the Qwen model was trained on bilingual data. Format: `"中文描述, english description"`. Examples in `tools/qwen_camera_studio.py` lines 38-76.

## Environment Configuration

### Required Variables
```bash
# Get token from: https://huggingface.co/settings/tokens
HF_TOKEN=your-huggingface-token
```

### Optional Variables
```bash
USE_HUGGINGFACE=true  # Set false to use MinIO only
HUGGINGFACE_MODEL_ID=Qwen/Qwen2-VL-2B-Instruct
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=your-key
MINIO_SECRET_KEY=your-secret
MINIO_BUCKET_NAME=qwen-models
PORT=8081
```

**Important**: The `.env` file is gitignored. Always use `.env.example` as template.

## Development Workflow

### When to Use What
- **Local venv (`./run_local.sh`)**: Active development, fast iteration, easier debugging
- **Docker Compose**: Full stack integration testing, production-like environment, pre-deployment validation

### Making Code Changes
1. Edit `qwen-api-service/app.py` or other files
2. For local dev: Stop service (Ctrl+C) and re-run `./run_local.sh`
3. For Docker: Run `docker-compose up -d --build qwen-api`

### Adding Dependencies
```bash
cd qwen-api-service
source .venv/bin/activate
uv pip install package-name
uv pip freeze > requirements.txt
```

### Model Download Behavior
- First startup downloads models (10-30 minutes depending on model size)
- Subsequent starts use cached models (much faster)
- HF_TOKEN required for private/gated models and higher rate limits
- Check download progress: `docker-compose logs -f qwen-api` or watch local terminal

## Key Constraints

### Python Environment
- **Docker**: Uses Python 3.11-slim, runs as root (normal for containers)
- **Local**: Requires Python 3.9+, managed via uv + venv
- Docker and local venv are completely isolated environments

### Port Configuration
- Qwen API: 8081 (configurable via PORT env var)
- OpenWebUI: 8080
- Check port conflicts: `lsof -i :8081`

### Model Loading
- Models require ~4GB RAM minimum
- CUDA/GPU automatically used if available (NVIDIA GPUs)
- Service has 40s start period before health checks begin (Docker)

### API Service Details
- **Working Directory**: Robyn requires writable directory, so `app.py` changes to script directory on startup (lines 27-31)
- **Token Handling**: Supports both `HF_TOKEN` and `HUGGINGFACE_TOKEN` environment variables (line 37)
- **Async Framework**: Built on Robyn for async request handling

## Documentation

- `README.md`: Comprehensive guide covering overview, local development, Docker testing, API testing, and troubleshooting
- `COOLIFY_DEPLOYMENT.md`: Production deployment instructions for Coolify
- `WARP.md`: This file - guidance for AI assistants working with this repository

## Important Notes

- **Never commit to source repository**: Only push to your own fork (per user preferences)
- **Use Coolify deployment**: Always use `.yaml` extension for docker-compose (not `.yml`)
- **Environment variables**: The `docker-compose.yaml` in repo is the source file; Coolify generates deployed version
- **MinIO usage**: User prefers MinIO for S3-compatible storage
- **Python environment**: User prefers `uv` for managing Python virtual environments
