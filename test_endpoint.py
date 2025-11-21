#!/usr/bin/env python3
"""
Test script for Qwen API endpoints
Tests image editing with camera presets and prompts

Requirements:
    pip install requests pillow
    # OR with uv
    uv pip install requests pillow
"""

import requests
import base64
import json
import sys
from pathlib import Path

try:
    from PIL import Image
    import io
except ImportError:
    print("❌ Pillow not installed. Install with:")
    print("   pip install pillow")
    print("   # OR with uv: uv pip install pillow")
    sys.exit(1)

API_URL = "http://localhost:8081"

def image_to_base64(image_path):
    """Convert image file to base64 string"""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def base64_to_image(base64_string, output_path):
    """Save base64 string as image file"""
    image_data = base64.b64decode(base64_string)
    image = Image.open(io.BytesIO(image_data))
    image.save(output_path)
    print(f"✅ Saved result image to: {output_path}")

def test_health():
    """Test health endpoint"""
    print("🔍 Testing health endpoint...")
    try:
        response = requests.get(f"{API_URL}/health", timeout=10)
        if response.status_code == 200:
            print(f"✅ Health check passed: {response.json()}")
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print(f"❌ Cannot connect to {API_URL}")
        print("   Make sure the service is running:")
        print("   - Docker: docker-compose up -d")
        print("   - Local: cd qwen-api-service && ./run_local.sh")
        print("   - Check if port 8081 is in use: lsof -i :8081")
        return False
    except requests.exceptions.ReadTimeout:
        print(f"❌ Connection to {API_URL} timed out")
        print("   Service may be starting up (model download can take time)")
        print("   Try again in a few minutes or check service logs")
        return False

def test_camera_edit(image_path, camera_preset="Front View", lighting="Cinematic", output_path="result.png"):
    """Test camera edit endpoint"""
    print(f"\n🎬 Testing camera edit endpoint...")
    print(f"   Image: {image_path}")
    print(f"   Camera: {camera_preset}")
    print(f"   Lighting: {lighting}")
    
    # Convert image to base64
    try:
        image_base64 = image_to_base64(image_path)
    except FileNotFoundError:
        print(f"❌ Image file not found: {image_path}")
        return False
    
    # Prepare request
    payload = {
        "image": image_base64,
        "camera_preset": camera_preset,
        "lighting": lighting,
        "additional_prompt": "",
        "steps": 8,
        "use_lightning": True
    }
    
    # Make request
    try:
        print("⏳ Sending request...")
        response = requests.post(
            f"{API_URL}/api/v1/camera-edit",
            json=payload,
            timeout=300  # 5 minutes for image generation
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Request successful!")
            print(f"   Prompt used: {result.get('prompt', 'N/A')}")
            print(f"   Steps: {result.get('steps', 'N/A')}")
            
            # Save result image
            if "image" in result:
                base64_to_image(result["image"], output_path)
                return True
            else:
                print("❌ No image in response")
                return False
        else:
            print(f"❌ Request failed: {response.status_code}")
            print(f"   Error: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ Request timed out (took longer than 5 minutes)")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_generic_edit(image_path, prompt, output_path="result_generic.png"):
    """Test generic edit endpoint"""
    print(f"\n🎨 Testing generic edit endpoint...")
    print(f"   Image: {image_path}")
    print(f"   Prompt: {prompt}")
    
    # Convert image to base64
    try:
        image_base64 = image_to_base64(image_path)
    except FileNotFoundError:
        print(f"❌ Image file not found: {image_path}")
        return False
    
    # Prepare request
    payload = {
        "image": image_base64,
        "prompt": prompt,
        "steps": 8,
        "use_lightning": True
    }
    
    # Make request
    try:
        print("⏳ Sending request...")
        response = requests.post(
            f"{API_URL}/api/v1/edit",
            json=payload,
            timeout=300
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Request successful!")
            
            # Save result image
            if "image" in result:
                base64_to_image(result["image"], output_path)
                return True
            else:
                print("❌ No image in response")
                return False
        else:
            print(f"❌ Request failed: {response.status_code}")
            print(f"   Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def create_test_image(output_path="test_image.png"):
    """Create a simple test image"""
    print(f"📸 Creating test image: {output_path}")
    img = Image.new('RGB', (512, 512), color='lightblue')
    img.save(output_path)
    print(f"✅ Created: {output_path}")
    return output_path

def main():
    print("=" * 60)
    print("Qwen API Endpoint Tester")
    print("=" * 60)
    
    # Test health first
    if not test_health():
        sys.exit(1)
    
    # Check for image argument or create test image
    if len(sys.argv) > 1:
        image_path = sys.argv[1]
    else:
        print("\n📝 No image provided. Creating test image...")
        image_path = create_test_image()
        print("   (You can provide your own image as first argument)")
    
    if not Path(image_path).exists():
        print(f"❌ Image not found: {image_path}")
        sys.exit(1)
    
    # Test camera edit
    print("\n" + "=" * 60)
    camera_preset = sys.argv[2] if len(sys.argv) > 2 else "Front View"
    lighting = sys.argv[3] if len(sys.argv) > 3 else "Cinematic"
    
    success = test_camera_edit(
        image_path,
        camera_preset=camera_preset,
        lighting=lighting,
        output_path="result_camera.png"
    )
    
    if success:
        print("\n✅ Test completed successfully!")
        print("   Result saved to: result_camera.png")
    else:
        print("\n❌ Test failed")
        sys.exit(1)

if __name__ == "__main__":
    main()

