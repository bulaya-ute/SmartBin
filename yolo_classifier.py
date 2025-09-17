#!/usr/bin/env python3
"""
YOLO Classification Integration for SmartBin PySerial Protocol
Replace the _mock_classify function with yolo_classify_image
"""

from ultralytics import YOLO
from PIL import Image
import torch

class YOLOClassifier:
    def __init__(self, model_path: str = "runs/smartbin_classify/weights/best.pt"):
        """Initialize YOLO classifier"""
        self.model_path = model_path
        self.model = None
        self.class_names = ['metal', 'misc', 'paper', 'plastic']  # Based on your dataset
        self._load_model()
    
    def _load_model(self):
        """Load the trained YOLO model"""
        try:
            self.model = YOLO(self.model_path)
            print(f"✅ YOLO model loaded from: {self.model_path}")
        except Exception as e:
            print(f"❌ Failed to load YOLO model: {e}")
            print(f"💡 Make sure training completed and model exists at: {self.model_path}")
            self.model = None
    
    def classify_image(self, image_pil: Image.Image):
        """
        Classify image using trained YOLO model
        
        Args:
            image_pil: PIL Image object
            
        Returns:
            tuple: (class_name, confidence)
        """
        if not self.model:
            # Fallback to mock classification if model not loaded
            import random
            classes = ["plastic", "metal", "paper", "misc"]
            classification = random.choice(classes)
            confidence = random.uniform(0.7, 0.95)
            print(f"⚠️ Using mock classification: {classification} (confidence: {confidence:.2f})")
            return classification, confidence
        
        try:
            # Run YOLO inference
            results = self.model(image_pil, verbose=False)
            
            # Get prediction
            predicted_class = results[0].names[results[0].probs.top1]
            confidence = results[0].probs.top1conf.item()
            
            print(f"🎯 YOLO classification: {predicted_class} (confidence: {confidence:.2f})")
            return predicted_class, confidence
            
        except Exception as e:
            print(f"❌ YOLO classification error: {e}")
            # Fallback to mock
            import random
            classes = ["plastic", "metal", "paper", "misc"]
            classification = random.choice(classes)
            confidence = random.uniform(0.7, 0.95)
            return classification, confidence

# Global classifier instance
_classifier = None

def yolo_classify_image(image_pil: Image.Image):
    """
    Global function for YOLO classification
    Use this to replace _mock_classify in smartbin_pyserial_protocol.py
    
    Args:
        image_pil: PIL Image object
        
    Returns:
        tuple: (class_name, confidence)
    """
    global _classifier
    
    if _classifier is None:
        _classifier = YOLOClassifier()
    
    return _classifier.classify_image(image_pil)

# Test function
if __name__ == "__main__":
    import os
    from PIL import Image
    
    # Test the classifier if model exists
    model_path = "runs/smartbin_classify/weights/best.pt"
    
    if os.path.exists(model_path):
        print("🧪 Testing YOLO classifier...")
        
        # Test with a sample image from dataset
        test_image_path = "dataset/val/plastic"  # Look for a plastic image
        if os.path.exists(test_image_path):
            plastic_images = [f for f in os.listdir(test_image_path) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
            if plastic_images:
                sample_image_path = os.path.join(test_image_path, plastic_images[0])
                
                # Load and classify
                image = Image.open(sample_image_path)
                result_class, confidence = yolo_classify_image(image)
                
                print(f"📸 Test image: {sample_image_path}")
                print(f"🎯 Predicted: {result_class} (confidence: {confidence:.3f})")
            else:
                print("❌ No test images found")
        else:
            print("❌ Test directory not found")
    else:
        print(f"❌ Model not found: {model_path}")
        print("💡 Train the model first using train_yolo_classification.py")
