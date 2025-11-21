"""
Qwen Camera Studio - OpenWebUI Tool
Higgsfield-style camera control interface for Qwen-Image-Edit
Uses Robyn API service instead of ComfyUI

title: Qwen Camera Studio
author: gonzalez
version: 1.0.0
description: Higgsfield-style camera control interface for Qwen-Image-Edit
required_open_webui_version: 0.5.3
"""

import os
import requests
import base64
import io
from typing import Callable, Any
from pydantic import BaseModel, Field
from PIL import Image

class Tools:
    class Valves(BaseModel):
        QWEN_API_URL: str = Field(
            default="http://qwen-api:8081",
            description="Qwen API service URL"
        )
        USE_LIGHTNING: bool = Field(
            default=True,
            description="Use Lightning LoRA for 4-8 step generation"
        )
        DEFAULT_STEPS: int = Field(
            default=8,
            description="Number of inference steps (4-8 for Lightning, 20-50 without)"
        )

    def __init__(self):
        self.valves = self.Valves()
        self.camera_presets = {
            # Basic moves
            "Front View": "正面视角, front view, facing camera directly",
            "Profile Left": "左侧轮廓, left profile view, 90 degree side angle",
            "Profile Right": "右侧轮廓, right profile view, 90 degree side angle", 
            "Back View": "背面视角, back view, rear angle",
            "Three-Quarter Left": "左侧四分之三视角, left three-quarter view",
            "Three-Quarter Right": "右侧四分之三视角, right three-quarter view",
            
            # Vertical angles
            "Top Down View": "俯视图, top-down view, bird's eye perspective",
            "Low Angle": "仰角视图, low angle shot looking up",
            "Eye Level": "平视, eye level view, neutral height",
            "High Angle": "俯角, high angle looking down",
            
            # Camera movements
            "Dolly In": "向前推进, camera dollies forward, push in",
            "Dolly Out": "向后拉出, camera dollies backward, pull out",
            "Crane Up": "摇臂上升, crane shot moving upward",
            "Crane Down": "摇臂下降, crane shot moving downward",
            "Orbit Left": "向左环绕, orbit rotating left around subject",
            "Orbit Right": "向右环绕, orbit rotating right around subject",
            "Pan Left": "向左平移, camera pans to the left",
            "Pan Right": "向右平移, camera pans to the right",
            
            # Advanced cinematic
            "FPV Drone": "第一人称无人机, FPV drone shot, dynamic motion",
            "Crash Zoom In": "快速推进, rapid zoom in, dramatic focus",
            "Wide Angle": "广角镜头, wide angle lens, expansive view",
            "Close Up": "特写镜头, close-up shot, tight framing",
            "Dutch Angle": "荷兰角度, tilted angle, canted frame",
            
            # Rotations
            "Rotate 45° Left": "向左旋转45度, rotate camera 45 degrees left",
            "Rotate 45° Right": "向右旋转45度, rotate camera 45 degrees right",
            "Rotate 90° Left": "向左旋转90度, rotate camera 90 degrees left",
            "Rotate 90° Right": "向右旋转90度, rotate camera 90 degrees right",
            "Rotate 180°": "旋转180度, rotate camera 180 degrees, complete flip",
        }
        
        self.lighting_presets = {
            "None": "",
            "Cinematic": "cinematic lighting, dramatic shadows",
            "Soft Natural": "soft natural lighting, diffused",
            "Studio": "studio lighting setup, professional",
            "Sunset": "warm sunset lighting, golden hour",
            "Neon": "neon lighting, vibrant colors",
            "Volumetric": "volumetric lighting, atmospheric rays",
        }

    async def execute_camera_edit(
        self,
        image_path: str,
        camera_preset: str,
        lighting: str,
        additional_prompt: str,
        steps: int,
        __user__: dict = {},
        __event_emitter__: Callable[[dict], Any] = None,
    ) -> str:
        """
        Execute Qwen-Image-Edit with camera controls using Robyn API
        
        :param image_path: Path or URL to input image
        :param camera_preset: Camera movement/angle preset
        :param lighting: Lighting style preset
        :param additional_prompt: Additional editing instructions
        :param steps: Number of inference steps
        :return: HTML with result image
        """
        
        await __event_emitter__({
            "type": "status",
            "data": {
                "description": f"🎬 Setting up {camera_preset}...",
                "done": False
            }
        })
        
        # Load image
        if image_path.startswith('http'):
            response = requests.get(image_path)
            image = Image.open(io.BytesIO(response.content))
        else:
            image = Image.open(image_path)
        
        # Convert to base64
        buffered = io.BytesIO()
        image.save(buffered, format="PNG")
        img_base64 = base64.b64encode(buffered.getvalue()).decode()
        
        await __event_emitter__({
            "type": "status",
            "data": {
                "description": f"🎥 Generating with: {camera_preset}",
                "done": False
            }
        })
        
        # Call Qwen API via Robyn service
        try:
            api_url = f"{self.valves.QWEN_API_URL}/api/v1/camera-edit"
            payload = {
                "image": img_base64,
                "camera_preset": camera_preset,
                "lighting": lighting,
                "additional_prompt": additional_prompt,
                "steps": steps,
                "use_lightning": self.valves.USE_LIGHTNING
            }
            
            response = requests.post(
                api_url,
                json=payload,
                timeout=300  # 5 minute timeout for image generation
            )
            response.raise_for_status()
            
            result_data = response.json()
            result_image = result_data.get("image")
            full_prompt = result_data.get("prompt", "")
            
            if not result_image:
                raise ValueError("No image returned from API")
            
            # Return HTML with comparison view
            html = f"""
            <div style="max-width: 100%; margin: 20px 0;">
                <div style="background: #1a1a1a; border-radius: 12px; padding: 20px; color: white;">
                    <h3 style="margin-top: 0;">📸 {camera_preset}</h3>
                    <p style="opacity: 0.8; font-size: 14px;">{full_prompt}</p>
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin-top: 15px;">
                        <div>
                            <p style="font-size: 12px; opacity: 0.6; margin-bottom: 5px;">ORIGINAL</p>
                            <img src="data:image/png;base64,{img_base64}" 
                                 style="width: 100%; border-radius: 8px; border: 2px solid #333;">
                        </div>
                        <div>
                            <p style="font-size: 12px; opacity: 0.6; margin-bottom: 5px;">RESULT</p>
                            <img src="data:image/png;base64,{result_image}" 
                                 style="width: 100%; border-radius: 8px; border: 2px solid #4a9eff;">
                        </div>
                    </div>
                    <div style="margin-top: 15px; font-size: 12px; opacity: 0.6;">
                        ⚡ Generated in {steps} steps • Lightning: {'Yes' if self.valves.USE_LIGHTNING else 'No'}
                    </div>
                </div>
            </div>
            """
            
            await __event_emitter__({
                "type": "status",
                "data": {
                    "description": "✅ Camera edit complete!",
                    "done": True
                }
            })
            
            return html
            
        except requests.exceptions.RequestException as e:
            error_msg = f"API request failed: {str(e)}"
            if hasattr(e.response, 'text'):
                error_msg += f" - {e.response.text}"
            
            await __event_emitter__({
                "type": "status",
                "data": {
                    "description": f"❌ Error: {error_msg}",
                    "done": True
                }
            })
            return f"Error generating image: {error_msg}"
        except Exception as e:
            await __event_emitter__({
                "type": "status",
                "data": {
                    "description": f"❌ Error: {str(e)}",
                    "done": True
                }
            })
            return f"Error generating image: {str(e)}"

    # Main user-facing function with Valves for UI controls
    async def qwen_camera_studio(
        self,
        image_url: str,
        camera_preset: str = "Front View",
        lighting: str = "Cinematic",
        additional_prompt: str = "",
        steps: int = 8,
        __user__: dict = {},
        __event_emitter__: Callable[[dict], Any] = None,
    ) -> str:
        """
        🎬 Qwen Camera Studio - Higgsfield-style camera control for anime/image editing
        
        Upload an image and use cinematic camera controls to generate new angles and movements!
        
        :param image_url: URL or path to your input image
        :param camera_preset: Select camera angle/movement from presets
        :param lighting: Choose lighting style
        :param additional_prompt: Add extra instructions (optional)
        :param steps: Inference steps (4-8 for fast, 20+ for quality)
        :return: Before/after comparison with your edited image
        """
        
        return await self.execute_camera_edit(
            image_url,
            camera_preset,
            lighting,
            additional_prompt,
            steps if steps else self.valves.DEFAULT_STEPS,
            __user__,
            __event_emitter__
        )

