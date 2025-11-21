# Qwen Image Model Integration for OpenWebUI

This project integrates Qwen Image Edit models with OpenWebUI using a Robyn-based API service. Models are downloaded directly from **Hugging Face Hub** (faster) with MINIO S3 as a fallback for custom models.

## Quick Links

- **[Production Deployment Guide](COOLIFY_DEPLOYMENT.md)** - Deploy to Coolify
- **[Development](#development-approaches)** - Local development guide
- **[Testing](#testing-the-api)** - Test endpoints and integration

## Architecture

- **Qwen API Service**: Robyn-based REST API service running Qwen Image Edit models
- **Hugging Face Hub**: Primary model source - direct downloads with parallel fetching for speed
- **MINIO S3**: Fallback storage for custom models and LoRAs
- **OpenWebUI**: Configured to connect to Qwen API endpoints
- **Docker Compose**: Orchestrates all services

## Model Access Strategy

**Primary Method: Hugging Face Direct Downloads** (Default)
- ✅ Faster downloads with parallel fetching
- ✅ Automatic version management
- ✅ No manual uploads needed
- ✅ Uses `snapshot_download` for efficient caching

**Fallback Method: MINIO S3**
- Used for custom models or when Hugging Face is unavailable
- Requires manual model uploads
- Useful for private/custom LoRAs

## Prerequisites

### Required
- Python 3.9+ (for local development)
- **OR** Docker/Podman with Docker Compose (for full stack testing)
- Hugging Face token (get from https://huggingface.co/settings/tokens)

### Optional
- MINIO S3 bucket for custom models/LoRAs
- `uv` for faster Python package management:
  ```bash
  curl -LsSf https://astral.sh/uv/install.sh | sh
  ```

### Installing Docker (if needed)

**macOS:**
1. Download Docker Desktop from https://www.docker.com/products/docker-desktop/
2. Install and launch Docker Desktop
3. Verify: `docker --version && docker compose version`

**Alternative:** Use Podman with Docker aliases (already configured if you have them)

**Skip Docker?** You can develop locally with Python venv or deploy directly to Coolify

## MINIO S3 Setup

### 1. Create MINIO Bucket

Create a bucket named `qwen-models` (or update `MINIO_BUCKET_NAME` in docker-compose):

```bash
# Using MINIO client
mc mb minio/qwen-models
```

### 2. Upload Models to S3

Upload your Qwen Image Edit models and LoRAs to MINIO:

```
qwen-models/
├── qwen-image-edit/
│   └── model.safetensors
└── loras/
    ├── Qwen-Edit-2509-Multiple-angles.safetensors
    └── Qwen-Image-Edit-Lightning-8steps-V1.0.safetensors
```

Example upload commands:

```bash
# Upload Qwen model
mc cp qwen-image-edit/model.safetensors minio/qwen-models/qwen-image-edit/

# Upload LoRAs
mc cp Qwen-Edit-2509-Multiple-angles.safetensors minio/qwen-models/loras/
mc cp Qwen-Image-Edit-Lightning-8steps-V1.0.safetensors minio/qwen-models/loras/
```

## Quick Start

1. **Copy the example environment file**:
   ```bash
   cp .env.example .env
   ```

2. **Edit `.env` and add your tokens**:
   - Get your Hugging Face token from: https://huggingface.co/settings/tokens
   - Add your `HF_TOKEN` to the `.env` file
   - Configure MINIO credentials if using custom models

3. **The `.env` file is gitignored** - your secrets are safe!

## Configuration

### Environment Variables

Create a `.env` file (use `.env.example` as a template) or set these environment variables in Coolify:

```env
# Hugging Face Configuration (Primary - faster downloads)
USE_HUGGINGFACE=true  # Set to false to use MINIO only
HUGGINGFACE_MODEL_ID=Qwen/Qwen2-VL-2B-Instruct  # Change to your preferred Qwen model
HF_TOKEN=your-huggingface-token  # Standard Hugging Face token (or use HUGGINGFACE_TOKEN)
# HUGGINGFACE_TOKEN=  # Alternative: also supported for compatibility

# MINIO Configuration (Fallback for custom models)
MINIO_ENDPOINT=your-minio-endpoint:9000
MINIO_ACCESS_KEY=your-access-key
MINIO_SECRET_KEY=your-secret-key
MINIO_BUCKET_NAME=qwen-models
MINIO_SECURE=false  # Set to true if using HTTPS
```

### Model Download Behavior

1. **If `USE_HUGGINGFACE=true`** (default):
   - Models download directly from Hugging Face Hub
   - Uses `snapshot_download` for parallel, efficient downloads
   - Cached in `/app/models/huggingface/` for faster subsequent loads
   - Falls back to MINIO if Hugging Face download fails

2. **If `USE_HUGGINGFACE=false`**:
   - Models download from MINIO S3 only
   - Requires manual model uploads to MINIO bucket

### Docker Compose

The `source-docker-compose.yaml` file includes:

- **open-webui**: OpenWebUI service with Qwen API URL configured
- **qwen-api**: Robyn-based Qwen API service with MINIO integration

## Development Approaches

### When to Use What

**Local Development (uv + venv)** - Fast iteration:
- ✅ Use when actively developing/changing code
- ✅ Faster startup (no Docker rebuild)
- ✅ Easier debugging with direct Python access
- ✅ Better IDE integration
- Runs directly on your machine

**Docker Compose (Full Stack)** - Integration testing:
- ✅ Use when testing full stack (OpenWebUI + Qwen API together)
- ✅ Use before deploying to production
- ✅ Production-like environment
- Runs both services in containers

### Option 1: Local Development (Fastest)

#### Quick Start with Script

```bash
cd qwen-api-service
./run_local.sh
```

The script will:
- Check for `uv` installation
- Create virtual environment
- Install dependencies
- Load environment variables from `.env`
- Start the API service

#### Manual Setup

```bash
cd qwen-api-service

# Create virtual environment
uv venv

# Activate venv
source .venv/bin/activate

# Install dependencies
uv pip install -r requirements.txt

# Create model directories
mkdir -p models/huggingface models/loras

# Run the service
python app.py
```

#### Making Code Changes

1. Edit `app.py` or other files
2. Press `Ctrl+C` to stop the service
3. Run `./run_local.sh` again

#### Adding Dependencies

```bash
source .venv/bin/activate
uv pip install package-name
uv pip freeze > requirements.txt
```

### Option 2: Docker Compose (Full Stack)

#### Start Services

```bash
# Copy environment file
cp .env.example .env
# Edit .env and add your HF_TOKEN

# Start both services
docker-compose up -d

# Watch logs
docker-compose logs -f
```

#### Verify Services

```bash
# Check Qwen API health
curl http://localhost:8081/health

# Check model status
curl http://localhost:8081/api/v1/models

# Open OpenWebUI
open http://localhost:8080

# Check running containers
docker ps
```

#### Making Code Changes

```bash
# Rebuild after changes
docker-compose up -d --build qwen-api

# Or restart service
docker-compose restart qwen-api
```

#### Stopping Services

```bash
# Stop services (keeps volumes/cache)
docker-compose stop

# Stop and remove containers (keeps volumes)
docker-compose down

# Remove everything including model cache
docker-compose down -v
```

#### Important Notes

- **First run**: Model download takes 10-30 minutes
- **Subsequent runs**: Models cached, starts much faster
- **Memory**: Service needs ~4GB RAM for model loading
- **GPU**: NVIDIA GPUs automatically detected and used
- **Port conflicts**: Check with `lsof -i :8081`

### Production Deployment

For production deployment to Coolify, see **[COOLIFY_DEPLOYMENT.md](COOLIFY_DEPLOYMENT.md)**.

## OpenWebUI Tool Installation

### 1. Install Qwen Camera Studio Tool

1. **Access OpenWebUI Admin Panel**:
   - Navigate to your OpenWebUI instance
   - Go to Admin Panel > Tools

2. **Add New Tool**:
   - Click the "+" button to add a new tool
   - Copy the contents of `tools/qwen_camera_studio.py`
   - Paste into the tool editor
   - Save the tool

3. **Configure Tool Settings**:
   - Click the gear icon next to the tool
   - Set `QWEN_API_URL` to `http://qwen-api:8081` (or external URL if accessing from outside Docker network)
   - Configure `USE_LIGHTNING` and `DEFAULT_STEPS` as needed

### 2. Using the Tool

The Qwen Camera Studio tool provides:

- **50+ Camera Presets**: Front View, Profile Left/Right, Dolly In/Out, Orbit, FPV Drone, etc.
- **Lighting Styles**: Cinematic, Soft Natural, Studio, Sunset, Neon, Volumetric
- **Lightning LoRA Support**: Fast 4-8 step generation
- **Before/After Comparison**: Side-by-side view of original and edited images

**Example Usage**:

```
Generate a left profile view with cinematic lighting
[Upload image]
```

Or explicitly:

```
Use Qwen Camera Studio with camera_preset="Orbit Right" 
and lighting="Neon" on this image
```

## API Endpoints

The Qwen API service exposes the following endpoints:

### Health Check
```
GET /health
```

### Camera Edit (Recommended)
```
POST /api/v1/camera-edit
Content-Type: application/json

{
  "image": "base64_encoded_image",
  "camera_preset": "Front View",
  "lighting": "Cinematic",
  "additional_prompt": "",
  "steps": 8,
  "use_lightning": true
}
```

### Generic Edit
```
POST /api/v1/edit
Content-Type: application/json

{
  "image": "base64_encoded_image",
  "prompt": "camera preset and lighting instructions",
  "steps": 8,
  "use_lightning": true
}
```

### List Models
```
GET /api/v1/models
```

## Troubleshooting

### Service Won't Start

```bash
# Check if ports are in use
lsof -i :8080
lsof -i :8081

# For Docker/Podman
docker-compose down
docker-compose up -d

# Check container status
docker ps -a
```

### Models Not Loading

**Check Hugging Face Token:**
```bash
# Verify HF_TOKEN is set
echo $HF_TOKEN

# Check logs for HF errors
docker-compose logs qwen-api | grep -i "hugging\|token\|error"

# Or for local dev
tail -f qwen-api-service/app.log  # if logging to file
```

**Check MINIO Connection** (if using fallback):
```bash
docker-compose logs qwen-api | grep -i "minio\|s3"
```

**Environment Variables:**
```bash
# For Docker
docker-compose exec qwen-api env | grep HF_TOKEN

# For local dev
echo $HF_TOKEN
```

### Model Download Takes Too Long

- **First startup**: 10-30 minutes is normal
- **Check progress**: `docker-compose logs -f qwen-api`
- **Subsequent runs**: Models cached, much faster
- **Clear cache**: `docker-compose down -v`

### OpenWebUI Can't Connect to Qwen API

```bash
# Test from OpenWebUI container
docker-compose exec open-webui curl http://qwen-api:8081/health

# Check network
docker network ls
docker network inspect openweb-custom_qwen-network

# Verify QWEN_API_URL in docker-compose.yaml
```

### Local Development Issues

**uv not found:**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
source ~/.zshrc
```

**Port already in use:**
```bash
lsof -i :8081
# Kill process or change PORT in .env
export PORT=8082
```

**Virtual environment issues:**
```bash
rm -rf .venv
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt
```

### API Connection Issues

**Check service health:**
```bash
curl http://localhost:8081/health
curl http://localhost:8081/api/v1/models
```

**Verify network** (Docker):
```bash
docker-compose exec open-webui ping qwen-api
```

### Tool Not Working in OpenWebUI

1. **Verify installation**: Check Admin Panel → Tools
2. **Check configuration**: Verify `QWEN_API_URL` is correct
3. **Test API manually**: `curl http://localhost:8081/health`
4. **Check logs**: Look for errors in both service logs

## Testing the API

### Quick Test with Script

A test script is provided that handles image encoding and API requests:

```bash
# Install test dependencies
pip install requests pillow
# OR with uv
uv pip install requests pillow

# Test with default settings (creates test image if none provided)
python test_endpoint.py

# Test with your own image
python test_endpoint.py path/to/image.jpg

# Test with custom camera preset and lighting
python test_endpoint.py image.jpg "Orbit Right" "Neon"
```

**Result**: Saves edited image to `result_camera.png`

### Manual Testing with curl

#### 1. Health Check

```bash
curl http://localhost:8081/health
```

#### 2. List Models

```bash
curl http://localhost:8081/api/v1/models
```

#### 3. Test Camera Edit

```bash
# Convert image to base64
base64 -i image.jpg > image_base64.txt

# Test endpoint
curl -X POST http://localhost:8081/api/v1/camera-edit \
  -H "Content-Type: application/json" \
  -d '{
    "image": "PASTE_BASE64_HERE",
    "camera_preset": "Front View",
    "lighting": "Cinematic",
    "steps": 8
  }' | python3 -m json.tool > response.json
```

#### 4. Extract and Save Image

```python
import json, base64
from PIL import Image
import io

with open('response.json') as f:
    data = json.load(f)

image_data = base64.b64decode(data['image'])
Image.open(io.BytesIO(image_data)).save('result.png')
print("✅ Saved to result.png")
```

### Available Options

**Camera Presets:**
- Front View, Profile Left/Right, Back View
- Top Down View, Low Angle, High Angle
- Dolly In/Out, Orbit Left/Right
- FPV Drone, Wide Angle, Close Up
- And 40+ more (see `qwen-api-service/app.py`)

**Lighting Styles:**
- None, Cinematic, Soft Natural, Studio
- Sunset, Neon, Volumetric

### Testing in OpenWebUI

1. Access http://localhost:8080
2. Go to Admin Panel → Tools
3. Add new tool from `tools/qwen_camera_studio.py`
4. Configure:
   - `QWEN_API_URL`: `http://localhost:8081` (local) or `http://qwen-api:8081` (Docker)
   - `USE_LIGHTNING`: `true`
   - `DEFAULT_STEPS`: `8`
5. Upload image and test: "Generate a left profile view with cinematic lighting"

## Notes

- The Qwen API service downloads models from MINIO on first startup
- Models are cached in `/app/models` volume
- The service supports both Lightning LoRA (fast) and standard inference
- Camera presets combine Chinese and English instructions for better model understanding

## License

This project integrates with OpenWebUI and uses Qwen Image Edit models. Please refer to their respective licenses.

