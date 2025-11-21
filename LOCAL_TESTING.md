# Local Testing Guide

This guide explains how to test the Qwen Image Integration locally before deploying to Coolify.

## Prerequisites

- Docker and Docker Compose installed
- Git repository cloned
- Hugging Face token (get from https://huggingface.co/settings/tokens)

## Quick Start

### 1. Set Up Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit .env and add your Hugging Face token
nano .env  # or use your preferred editor
```

Required in `.env`:
```env
HF_TOKEN=your-huggingface-token-here
```

### 2. Start Services

```bash
# Start both services
docker-compose up -d

# Watch logs
docker-compose logs -f
```

### 3. Verify Services

```bash
# Check Qwen API health
curl http://localhost:8081/health

# Check model status
curl http://localhost:8081/api/v1/models

# OpenWebUI should be accessible at
open http://localhost:8080
```

## Testing the Integration

### 1. Check Service Logs

```bash
# Qwen API logs
docker-compose logs qwen-api

# OpenWebUI logs
docker-compose logs open-webui

# Follow logs in real-time
docker-compose logs -f qwen-api
```

### 2. Test Qwen API Endpoints

```bash
# Health check
curl http://localhost:8081/health

# List models
curl http://localhost:8081/api/v1/models

# Test camera edit (requires base64 image)
curl -X POST http://localhost:8081/api/v1/camera-edit \
  -H "Content-Type: application/json" \
  -d '{
    "image": "base64_encoded_image_here",
    "camera_preset": "Front View",
    "lighting": "Cinematic",
    "steps": 8
  }'
```

### 3. Install OpenWebUI Tool

1. Open http://localhost:8080
2. Go to Admin Panel → Tools
3. Click "+" to add new tool
4. Copy contents of `tools/qwen_camera_studio.py`
5. Paste into tool editor
6. Configure tool settings:
   - `QWEN_API_URL`: `http://localhost:8081` (for local testing)
   - `USE_LIGHTNING`: `true`
   - `DEFAULT_STEPS`: `8`
7. Save tool

### 4. Test Camera Studio Tool

1. In OpenWebUI chat, upload an image
2. Try: "Generate a left profile view with cinematic lighting"
3. Or explicitly: "Use Qwen Camera Studio with camera_preset='Orbit Right'"

## Troubleshooting

### Services Won't Start

```bash
# Check if ports are in use
lsof -i :8080
lsof -i :8081

# Stop existing containers
docker-compose down

# Remove volumes (clears model cache)
docker-compose down -v
```

### Model Download Issues

```bash
# Check Qwen API logs for Hugging Face errors
docker-compose logs qwen-api | grep -i "hugging\|error\|token"

# Verify HF_TOKEN is set
docker-compose exec qwen-api env | grep HF_TOKEN

# Test Hugging Face connection manually
docker-compose exec qwen-api python -c "from huggingface_hub import snapshot_download; print('OK')"
```

### OpenWebUI Can't Connect to Qwen API

```bash
# Test from OpenWebUI container
docker-compose exec open-webui curl http://qwen-api:8081/health

# Check network
docker network ls
docker network inspect openweb-custom_qwen-network
```

### Model Loading Takes Too Long

- First startup downloads models (can take 10-30 minutes)
- Subsequent starts use cached models (much faster)
- Check progress: `docker-compose logs -f qwen-api`

## Development Workflow

### Making Changes to Qwen API

```bash
# Rebuild after code changes
docker-compose build qwen-api

# Restart service
docker-compose restart qwen-api

# Or rebuild and restart
docker-compose up -d --build qwen-api
```

### Testing Code Changes

```bash
# Run Qwen API locally (without Docker)
cd qwen-api-service
pip install -r requirements.txt
python app.py

# Test on different port
PORT=8082 python app.py
```

### Viewing Model Cache

```bash
# Check what's cached
docker volume inspect openweb-custom_qwen-models

# Access cache directory
docker-compose exec qwen-api ls -la /app/models/

# Clear cache (removes downloaded models)
docker-compose down -v
```

## Stopping Services

```bash
# Stop services (keeps volumes)
docker-compose stop

# Stop and remove containers (keeps volumes)
docker-compose down

# Stop and remove everything including volumes
docker-compose down -v
```

## Performance Tips

1. **First Run**: Model download takes time - be patient
2. **Subsequent Runs**: Models cached, starts much faster
3. **Memory**: Qwen API needs ~4GB RAM for model loading
4. **GPU**: If you have NVIDIA GPU, models will use it automatically

## Next Steps

Once local testing works:
1. Review `COOLIFY_DEPLOYMENT.md` for production deployment
2. Push changes to GitHub
3. Deploy to Coolify using the guide

