#!/usr/bin/env python3
"""
Test script to verify YOLO classification integration
"""
import os
import sys
from PIL import Image
import tempfile
import subprocess
import json

def test_classification():
    """Test the classification backend integration"""
    print("🧪 Testing YOLO Classification Integration")
    print("=" * 50)
    
    # Check if model exists
    model_path = "runs/smartbin_classify2/weights/best.pt"
    if not os.path.exists(model_path):
        print(f"❌ Model file not found: {model_path}")
        return False
    
    print(f"✅ Model file found: {model_path}")
    
    # Check if virtual environment python exists
    venv_python = ".venv/bin/python"
    if not os.path.exists(venv_python):
        print(f"❌ Virtual environment python not found: {venv_python}")
        return False
    
    print(f"✅ Virtual environment python found: {venv_python}")
    
    # Create a test image (simple colored square)
    test_image = Image.new('RGB', (224, 224), color='red')
    
    with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp_file:
        test_image.save(tmp_file.name, 'JPEG')
        tmp_path = tmp_file.name
    
    try:
        print(f"🖼️  Created test image: {tmp_path}")
        
        # Test the backend script
        cmd = [
            venv_python, "yolo_classification_backend.py",
            "--model", model_path,
            "--image", tmp_path,
            "--json"
        ]
        
        print(f"🔄 Running command: {' '.join(cmd)}")
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        print(f"📤 Return code: {result.returncode}")
        
        if result.stdout:
            print(f"📋 Stdout ({len(result.stdout)} chars):")
            print(result.stdout)
        
        if result.stderr:
            print(f"❌ Stderr:")
            print(result.stderr)
        
        if result.returncode == 0 and result.stdout.strip():
            try:
                classification_data = json.loads(result.stdout)
                print("\n✅ JSON parsing successful!")
                print(f"Success: {classification_data.get('success', 'unknown')}")
                print(f"Result: {classification_data.get('result', 'unknown')}")
                print(f"Confidence: {classification_data.get('confidence', 'unknown')}")
                print(f"Method: {classification_data.get('method', 'unknown')}")
                return True
            except json.JSONDecodeError as e:
                print(f"❌ JSON parsing failed: {e}")
                return False
        else:
            print("❌ Classification failed")
            return False
            
    finally:
        # Clean up
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
            print(f"🧹 Cleaned up test image: {tmp_path}")

if __name__ == "__main__":
    success = test_classification()
    print("\n" + "=" * 50)
    if success:
        print("🎉 Classification integration test PASSED!")
        sys.exit(0)
    else:
        print("💥 Classification integration test FAILED!")
        sys.exit(1)
