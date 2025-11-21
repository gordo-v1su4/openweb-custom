"""
Qwen Image Edit API Service using Robyn
Provides REST API endpoints for Qwen Image Edit with camera controls and LoRA support
"""

import os
import json
import base64
import io
import asyncio
from typing import Optional
from robyn import Robyn, Request
from robyn.robyn import Response
from minio import Minio
from minio.error import S3Error
import torch
from PIL import Image
import logging
from huggingface_hub import snapshot_download, hf_hub_download
from transformers import AutoModel, AutoProcessor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Robyn(__file__)

# Model Configuration
USE_HUGGINGFACE = os.getenv("USE_HUGGINGFACE", "true").lower() == "true"
HUGGINGFACE_MODEL_ID = os.getenv("HUGGINGFACE_MODEL_ID", "Qwen/Qwen2-VL-2B-Instruct")
# Support both HF_TOKEN (standard) and HUGGINGFACE_TOKEN
HF_TOKEN = os.getenv("HF_TOKEN") or os.getenv("HUGGINGFACE_TOKEN") or ""

# MINIO Configuration (fallback for custom models)
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "localhost:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "")
MINIO_BUCKET_NAME = os.getenv("MINIO_BUCKET_NAME", "qwen-models")
MINIO_SECURE = os.getenv("MINIO_SECURE", "false").lower() == "true"

# Model paths
MODEL_CACHE_DIR = "/app/models"
HUGGINGFACE_CACHE_DIR = os.path.join(MODEL_CACHE_DIR, "huggingface")
LORA_DIR = os.path.join(MODEL_CACHE_DIR, "loras")

# Initialize MINIO client
minio_client = None
if MINIO_ACCESS_KEY and MINIO_SECRET_KEY:
    try:
        minio_client = Minio(
            MINIO_ENDPOINT,
            access_key=MINIO_ACCESS_KEY,
            secret_key=MINIO_SECRET_KEY,
            secure=MINIO_SECURE
        )
        logger.info(f"Connected to MINIO at {MINIO_ENDPOINT}")
    except Exception as e:
        logger.error(f"Failed to connect to MINIO: {e}")

# Global model state
qwen_model = None
lora_models = {}


def download_from_minio(bucket_name: str, object_name: str, file_path: str) -> bool:
    """Download a file from MINIO S3 bucket"""
    if not minio_client:
        logger.warning("MINIO client not initialized")
        return False
    
    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        minio_client.fget_object(bucket_name, object_name, file_path)
        logger.info(f"Downloaded {object_name} from MINIO to {file_path}")
        return True
    except S3Error as e:
        logger.error(f"MINIO error downloading {object_name}: {e}")
        return False
    except Exception as e:
        logger.error(f"Error downloading {object_name}: {e}")
        return False


def load_models_from_huggingface():
    """Load Qwen models directly from Hugging Face Hub (faster downloads)"""
    global qwen_model, lora_models
    
    os.makedirs(HUGGINGFACE_CACHE_DIR, exist_ok=True)
    
    try:
        logger.info(f"Downloading Qwen model from Hugging Face: {HUGGINGFACE_MODEL_ID}")
        
        # Use snapshot_download for faster parallel downloads
        model_path = snapshot_download(
            repo_id=HUGGINGFACE_MODEL_ID,
            cache_dir=HUGGINGFACE_CACHE_DIR,
            token=HF_TOKEN if HF_TOKEN else None,
            resume_download=True,
            local_files_only=False
        )
        
        logger.info(f"Model downloaded to: {model_path}")
        
        # Load model and processor
        try:
            qwen_model = AutoModel.from_pretrained(
                model_path,
                torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
                device_map="auto" if torch.cuda.is_available() else None,
                trust_remote_code=True,
                token=HF_TOKEN if HF_TOKEN else None
            )
            logger.info("Model loaded into memory successfully")
        except Exception as e:
            logger.warning(f"Could not load model into memory: {e}. Will use model path for inference.")
            qwen_model = {"path": model_path, "loaded": False}
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to load models from Hugging Face: {e}")
        return False


def load_models_from_minio():
    """Load Qwen models and LoRAs from MINIO S3 (fallback for custom models)"""
    global qwen_model, lora_models
    
    os.makedirs(MODEL_CACHE_DIR, exist_ok=True)
    os.makedirs(LORA_DIR, exist_ok=True)
    
    # Download Qwen Image Edit model
    qwen_model_path = os.path.join(MODEL_CACHE_DIR, "qwen-image-edit")
    if not os.path.exists(qwen_model_path):
        logger.info("Downloading Qwen Image Edit model from MINIO...")
        download_from_minio(MINIO_BUCKET_NAME, "qwen-image-edit/model.safetensors", 
                          os.path.join(qwen_model_path, "model.safetensors"))
    
    # Download LoRAs
    loras = [
        "Qwen-Edit-2509-Multiple-angles.safetensors",
        "Qwen-Image-Edit-Lightning-8steps-V1.0.safetensors"
    ]
    
    for lora_name in loras:
        lora_path = os.path.join(LORA_DIR, lora_name)
        if not os.path.exists(lora_path):
            logger.info(f"Downloading LoRA {lora_name} from MINIO...")
            download_from_minio(MINIO_BUCKET_NAME, f"loras/{lora_name}", lora_path)
    
    logger.info("Models downloaded from MINIO successfully")


def load_models():
    """Load models from Hugging Face (primary) or MINIO (fallback)"""
    if USE_HUGGINGFACE:
        logger.info("Attempting to load models from Hugging Face Hub...")
        if load_models_from_huggingface():
            logger.info("✓ Models loaded from Hugging Face")
            return
        else:
            logger.warning("Hugging Face download failed, falling back to MINIO...")
    
    # Fallback to MINIO
    if minio_client:
        logger.info("Loading models from MINIO S3...")
        load_models_from_minio()
        logger.info("✓ Models loaded from MINIO")
    else:
        logger.warning("Neither Hugging Face nor MINIO configured. Models not loaded.")


@app.get("/health")
async def health_check(request: Request):
    """Health check endpoint"""
    return Response(
        status_code=200,
        body=json.dumps({"status": "healthy", "service": "qwen-api"}),
        headers={"Content-Type": "application/json"}
    )


@app.post("/api/v1/edit")
async def edit_image(request: Request):
    """
    Edit image using Qwen Image Edit model
    
    Request body:
    {
        "image": "base64_encoded_image",
        "prompt": "camera preset and lighting instructions",
        "steps": 8,
        "use_lightning": true
    }
    """
    try:
        body = json.loads(request.body)
        
        image_base64 = body.get("image")
        prompt = body.get("prompt", "")
        steps = body.get("steps", 8)
        use_lightning = body.get("use_lightning", True)
        
        if not image_base64:
            return Response(
                status_code=400,
                body=json.dumps({"error": "Missing image data"}),
                headers={"Content-Type": "application/json"}
            )
        
        # Decode image
        image_data = base64.b64decode(image_base64)
        image = Image.open(io.BytesIO(image_data))
        
        # Process image with Qwen model
        # TODO: Implement actual Qwen model inference
        # This is a placeholder that returns the original image
        # In production, you would:
        # 1. Load the Qwen Image Edit model
        # 2. Apply LoRAs if needed
        # 3. Run inference with the prompt
        # 4. Return the edited image
        
        # Placeholder: return original image for now
        output_buffer = io.BytesIO()
        image.save(output_buffer, format="PNG")
        output_base64 = base64.b64encode(output_buffer.getvalue()).decode()
        
        return Response(
            status_code=200,
            body=json.dumps({
                "image": output_base64,
                "prompt": prompt,
                "steps": steps,
                "lightning": use_lightning
            }),
            headers={"Content-Type": "application/json"}
        )
        
    except json.JSONDecodeError:
        return Response(
            status_code=400,
            body=json.dumps({"error": "Invalid JSON"}),
            headers={"Content-Type": "application/json"}
        )
    except Exception as e:
        logger.error(f"Error processing image: {e}")
        return Response(
            status_code=500,
            body=json.dumps({"error": str(e)}),
            headers={"Content-Type": "application/json"}
        )


@app.get("/api/v1/models")
async def list_models(request: Request):
    """List available models and LoRAs"""
    model_info = {
        "loaded": qwen_model is not None,
        "source": "huggingface" if USE_HUGGINGFACE else "minio",
        "model_id": HUGGINGFACE_MODEL_ID if USE_HUGGINGFACE else None,
        "path": HUGGINGFACE_CACHE_DIR if USE_HUGGINGFACE else MODEL_CACHE_DIR
    }
    
    if isinstance(qwen_model, dict):
        model_info["path"] = qwen_model.get("path", "unknown")
        model_info["loaded"] = qwen_model.get("loaded", False)
    
    models = {
        "qwen_image_edit": model_info,
        "loras": {
            "available": list(lora_models.keys()) if lora_models else [],
            "path": LORA_DIR
        },
        "cache_dirs": {
            "huggingface": HUGGINGFACE_CACHE_DIR,
            "minio": MODEL_CACHE_DIR,
            "loras": LORA_DIR
        }
    }
    
    return Response(
        status_code=200,
        body=json.dumps(models),
        headers={"Content-Type": "application/json"}
    )


@app.post("/api/v1/camera-edit")
async def camera_edit(request: Request):
    """
    Camera-controlled image edit with presets
    
    Request body:
    {
        "image": "base64_encoded_image",
        "camera_preset": "Front View",
        "lighting": "Cinematic",
        "additional_prompt": "",
        "steps": 8,
        "use_lightning": true
    }
    """
    try:
        body = json.loads(request.body)
        
        image_base64 = body.get("image")
        camera_preset = body.get("camera_preset", "Front View")
        lighting = body.get("lighting", "Cinematic")
        additional_prompt = body.get("additional_prompt", "")
        steps = body.get("steps", 8)
        use_lightning = body.get("use_lightning", True)
        
        if not image_base64:
            return Response(
                status_code=400,
                body=json.dumps({"error": "Missing image data"}),
                headers={"Content-Type": "application/json"}
            )
        
        # Build full prompt from camera preset and lighting
        camera_presets = {
            "Front View": "正面视角, front view, facing camera directly",
            "Profile Left": "左侧轮廓, left profile view, 90 degree side angle",
            "Profile Right": "右侧轮廓, right profile view, 90 degree side angle",
            "Back View": "背面视角, back view, rear angle",
            "Three-Quarter Left": "左侧四分之三视角, left three-quarter view",
            "Three-Quarter Right": "右侧四分之三视角, right three-quarter view",
            "Top Down View": "俯视图, top-down view, bird's eye perspective",
            "Low Angle": "仰角视图, low angle shot looking up",
            "Eye Level": "平视, eye level view, neutral height",
            "High Angle": "俯角, high angle looking down",
            "Dolly In": "向前推进, camera dollies forward, push in",
            "Dolly Out": "向后拉出, camera dollies backward, pull out",
            "Crane Up": "摇臂上升, crane shot moving upward",
            "Crane Down": "摇臂下降, crane shot moving downward",
            "Orbit Left": "向左环绕, orbit rotating left around subject",
            "Orbit Right": "向右环绕, orbit rotating right around subject",
            "Pan Left": "向左平移, camera pans to the left",
            "Pan Right": "向右平移, camera pans to the right",
            "FPV Drone": "第一人称无人机, FPV drone shot, dynamic motion",
            "Crash Zoom In": "快速推进, rapid zoom in, dramatic focus",
            "Wide Angle": "广角镜头, wide angle lens, expansive view",
            "Close Up": "特写镜头, close-up shot, tight framing",
            "Dutch Angle": "荷兰角度, tilted angle, canted frame",
        }
        
        lighting_presets = {
            "None": "",
            "Cinematic": "cinematic lighting, dramatic shadows",
            "Soft Natural": "soft natural lighting, diffused",
            "Studio": "studio lighting setup, professional",
            "Sunset": "warm sunset lighting, golden hour",
            "Neon": "neon lighting, vibrant colors",
            "Volumetric": "volumetric lighting, atmospheric rays",
        }
        
        camera_instruction = camera_presets.get(camera_preset, camera_preset)
        lighting_instruction = lighting_presets.get(lighting, "")
        
        full_prompt = camera_instruction
        if lighting_instruction:
            full_prompt += f", {lighting_instruction}"
        if additional_prompt:
            full_prompt += f", {additional_prompt}"
        
        # Decode image
        image_data = base64.b64decode(image_base64)
        image = Image.open(io.BytesIO(image_data))
        
        # Process image with Qwen model
        # TODO: Implement actual Qwen model inference with LoRAs
        # Placeholder: return original image for now
        output_buffer = io.BytesIO()
        image.save(output_buffer, format="PNG")
        output_base64 = base64.b64encode(output_buffer.getvalue()).decode()
        
        return Response(
            status_code=200,
            body=json.dumps({
                "image": output_base64,
                "camera_preset": camera_preset,
                "lighting": lighting,
                "prompt": full_prompt,
                "steps": steps,
                "lightning": use_lightning
            }),
            headers={"Content-Type": "application/json"}
        )
        
    except json.JSONDecodeError:
        return Response(
            status_code=400,
            body=json.dumps({"error": "Invalid JSON"}),
            headers={"Content-Type": "application/json"}
        )
    except Exception as e:
        logger.error(f"Error processing camera edit: {e}")
        return Response(
            status_code=500,
            body=json.dumps({"error": str(e)}),
            headers={"Content-Type": "application/json"}
        )


# Initialize models on startup
@app.startup_handler
async def startup():
    """Load models from Hugging Face or MINIO on startup"""
    logger.info("Starting Qwen API service...")
    load_models()
    logger.info("Qwen API service started")


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8081))
    app.start(port=port, host="0.0.0.0")

