# Coolify Deployment Guide

This guide explains how to deploy the Qwen Image Integration to Coolify.

## Prerequisites

- Coolify instance running
- GitHub repository: `https://github.com/gordo-v1su4/openweb-custom`
- Hugging Face token (optional but recommended)

## Deployment Methods

### Method 1: Docker Compose Application (Recommended)

Coolify supports Docker Compose applications natively. This is the easiest way to deploy.

#### Steps:

1. **Create New Application in Coolify**:
   - Go to your Coolify dashboard
   - Click "New Resource" → "Docker Compose"
   - Name it: `openweb-qwen`

2. **Connect GitHub Repository**:
   - Repository: `gordo-v1su4/openweb-custom`
   - Branch: `main`
   - Docker Compose File: `docker-compose.yaml`

3. **Set Environment Variables**:
   
   In Coolify's environment variables section, add:
   
   ```env
   # Hugging Face (Required for model downloads)
   USE_HUGGINGFACE=true
   HUGGINGFACE_MODEL_ID=Qwen/Qwen2-VL-2B-Instruct
   HF_TOKEN=your-huggingface-token-here
   
   # MINIO (Optional - only if using custom models)
   MINIO_ENDPOINT=your-minio-endpoint:9000
   MINIO_ACCESS_KEY=your-access-key
   MINIO_SECRET_KEY=your-secret-key
   MINIO_BUCKET_NAME=qwen-models
   MINIO_SECURE=false
   ```

4. **Configure Ports**:
   - OpenWebUI: `8080` (Coolify will handle routing)
   - Qwen API: `8081` (internal only, no need to expose)

5. **Deploy**:
   - Click "Deploy"
   - Coolify will:
     - Clone your repository
     - Build the `qwen-api` service
     - Start both services
     - Set up networking between them

### Method 2: Separate Services (More Control)

If you want more control over each service, deploy them separately:

#### Deploy Qwen API Service:

1. **Create New Service**:
   - Type: "Docker Compose" or "Dockerfile"
   - Name: `qwen-api`

2. **Build Configuration**:
   - Build Pack: Dockerfile
   - Dockerfile Path: `qwen-api-service/Dockerfile`
   - Build Context: `qwen-api-service/`

3. **Environment Variables**:
   ```env
   PORT=8081
   USE_HUGGINGFACE=true
   HUGGINGFACE_MODEL_ID=Qwen/Qwen2-VL-2B-Instruct
   HF_TOKEN=your-token
   ```

4. **Port**: `8081` (internal only)

#### Deploy OpenWebUI:

1. **Create New Service**:
   - Type: "Docker Image"
   - Image: `ghcr.io/open-webui/open-webui:main`

2. **Environment Variables**:
   ```env
   PORT=8080
   QWEN_API_URL=http://qwen-api:8081
   ```
   
   **Important**: Use the internal Docker network name for `QWEN_API_URL`:
   - If services are in same project: `http://qwen-api:8081`
   - If different projects: Use Coolify's internal DNS

3. **Port**: `8080`

## Important Notes for Coolify

### Network Configuration

- Both services must be in the **same Coolify project** to communicate
- Use service names for internal communication: `http://qwen-api:8081`
- Coolify automatically creates a Docker network for each project

### Environment Variables

- Set `HF_TOKEN` in Coolify's environment variables (not in `.env` file)
- Coolify will inject these into containers automatically
- Secrets are encrypted in Coolify's database

### Volume Persistence

- Model cache is stored in Docker volume: `qwen-models`
- This persists across deployments
- To clear cache: Remove volume in Coolify dashboard

### Health Checks

Both services have health checks configured:
- OpenWebUI: Checks `/` endpoint
- Qwen API: Checks `/health` endpoint

Coolify will wait for health checks before marking services as "running".

## Troubleshooting

### Qwen API Not Starting

1. **Check Logs**:
   ```bash
   # In Coolify dashboard, view qwen-api logs
   ```

2. **Common Issues**:
   - Missing `HF_TOKEN` → Add token in environment variables
   - Model download timeout → Increase health check `start_period`
   - Out of memory → Increase container memory limit in Coolify

### OpenWebUI Can't Connect to Qwen API

1. **Verify Network**:
   - Both services in same Coolify project?
   - Check `QWEN_API_URL` environment variable

2. **Test Connection**:
   ```bash
   # From OpenWebUI container
   curl http://qwen-api:8081/health
   ```

### Model Download Issues

1. **Check Hugging Face Token**:
   - Token valid? Check at https://huggingface.co/settings/tokens
   - Token has read permissions?

2. **Check Logs**:
   ```bash
   # Look for Hugging Face download errors
   docker logs qwen-api | grep -i "hugging\|error"
   ```

## Post-Deployment

### 1. Verify Services

```bash
# Check Qwen API health
curl https://your-domain.com/qwen-api/health

# Check OpenWebUI
curl https://your-domain.com/
```

### 2. Install OpenWebUI Tool

1. Access OpenWebUI admin panel
2. Go to Admin Panel → Tools
3. Add `tools/qwen_camera_studio.py`
4. Configure `QWEN_API_URL`:
   - Internal: `http://qwen-api:8081`
   - External: `https://your-domain.com/qwen-api`

### 3. Test Integration

1. Upload an image in OpenWebUI
2. Use the Qwen Camera Studio tool
3. Select a camera preset
4. Generate edited image

## Updating Deployment

When you push changes to GitHub:

1. Coolify will detect the push (if webhook configured)
2. Or manually trigger "Redeploy" in Coolify dashboard
3. Coolify will rebuild `qwen-api` if Dockerfile changed
4. Services will restart with new code

## Recommended Coolify Settings

- **Auto Deploy**: Enable for automatic updates on git push
- **Health Checks**: Keep enabled (already configured)
- **Resource Limits**:
  - Qwen API: 4GB RAM, 2 CPU cores (for model loading)
  - OpenWebUI: 2GB RAM, 1 CPU core
- **Backup**: Enable volume backups for `qwen-models` volume

