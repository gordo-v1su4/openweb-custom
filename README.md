# Qwen Image Model Integration for OpenWebUI

This project integrates Qwen Image Edit models with OpenWebUI using a Robyn-based API service. Models are downloaded directly from **Hugging Face Hub** (faster) with MINIO S3 as a fallback for custom models.

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

- Docker and Docker Compose installed
- (Optional) MINIO S3 bucket for custom models/LoRAs
- (Optional) Hugging Face token for private models

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

## Deployment

### Using Coolify

1. **Upload docker-compose.yaml**:
   - Use `source-docker-compose.yaml` as your base configuration
   - Coolify will generate the deployed version automatically

2. **Set Environment Variables**:
   - In Coolify, add the Hugging Face and MINIO environment variables listed above
   - **Important**: Set `HF_TOKEN` (or `HUGGINGFACE_TOKEN`) for:
     - Private/gated models
     - Higher rate limits
     - Access to restricted repositories
   - Ensure `QWEN_API_URL` is set to `http://qwen-api:8081` (internal Docker network)

3. **Deploy**:
   - Coolify will build and deploy both services
   - The qwen-api service will download models from MINIO on startup

### Local Development

1. **Set environment variables**:
   ```bash
   export MINIO_ENDPOINT=localhost:9000
   export MINIO_ACCESS_KEY=your-key
   export MINIO_SECRET_KEY=your-secret
   export MINIO_BUCKET_NAME=qwen-models
   ```

2. **Start services**:
   ```bash
   docker-compose -f source-docker-compose.yaml up -d
   ```

3. **Check health**:
   ```bash
   curl http://localhost:8081/health
   ```

4. **Check model status**:
   ```bash
   curl http://localhost:8081/api/v1/models
   ```
   This will show which models are loaded and their source (Hugging Face or MINIO).

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

### Models Not Loading

1. **Check Hugging Face Token**:
   - If downloading from Hugging Face fails, verify `HF_TOKEN` is set correctly
   - Get your token from: https://huggingface.co/settings/tokens
   - Token is required for:
     - Private/gated models
     - Higher download rate limits
     - Access to restricted repositories
   ```bash
   docker logs qwen-api | grep -i "hugging\|token\|error"
   ```

2. **Check MINIO Connection** (if using fallback):
   ```bash
   docker logs qwen-api
   ```
   Look for MINIO connection errors

3. **Verify Bucket Structure**:
   Ensure models are uploaded to the correct paths in MINIO

4. **Check Environment Variables**:
   Verify `HF_TOKEN` (or `HUGGINGFACE_TOKEN`) and MINIO credentials are set correctly

### API Connection Issues

1. **Check Service Health**:
   ```bash
   curl http://localhost:8081/health
   ```

2. **Verify Network**:
   Ensure both services are on the same Docker network (`qwen-network`)

3. **Check OpenWebUI Logs**:
   ```bash
   docker logs open-webui
   ```

### Tool Not Appearing

1. **Verify Tool Installation**:
   - Check Admin Panel > Tools
   - Ensure tool code was pasted correctly

2. **Check Tool Configuration**:
   - Verify `QWEN_API_URL` is set correctly
   - Test API endpoint manually

## Development

### Building Qwen API Service

```bash
cd qwen-api-service
docker build -t qwen-api .
```

### Running Tests

```bash
# Test health endpoint
curl http://localhost:8081/health

# Test camera edit endpoint
curl -X POST http://localhost:8081/api/v1/camera-edit \
  -H "Content-Type: application/json" \
  -d '{
    "image": "base64_image_data",
    "camera_preset": "Front View",
    "lighting": "Cinematic",
    "steps": 8
  }'
```

## Notes

- The Qwen API service downloads models from MINIO on first startup
- Models are cached in `/app/models` volume
- The service supports both Lightning LoRA (fast) and standard inference
- Camera presets combine Chinese and English instructions for better model understanding

## License

This project integrates with OpenWebUI and uses Qwen Image Edit models. Please refer to their respective licenses.

