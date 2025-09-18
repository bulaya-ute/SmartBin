#!/usr/bin/env python3
"""
SmartBin YOLO Classification Backend
Provides real YOLO classification functionality for the GUI application
REQUIRES: Trained YOLO model file (best.pt) - No fallback classification
"""

import argparse
import sys
import json
from pathlib import Path
from PIL import Image
import torch
from ultralytics import YOLO
from typing import Dict, Tuple, Optional
import io
import base64

class SmartBinYOLOClassifier:
    def __init__(self, model_path: str = "best.pt", quiet: bool = False):
        """Initialize the YOLO classifier
        
        Args:
            model_path: Path to the trained YOLO model file
            quiet: If True, suppress debug output
        
        Raises:
            FileNotFoundError: If model file doesn't exist
            Exception: If model cannot be loaded
        """
        self.model_path = Path(model_path)
        self.model = None
        self.quiet = quiet
        self.class_mapping = {
            0: "plastic",
            1: "metal", 
            2: "paper",
            3: "misc"
        }
        
        # Load the model (required)
        self._load_model()
    
    def _load_model(self) -> bool:
        """Load the YOLO model
        
        Raises:
            FileNotFoundError: If model file doesn't exist
            Exception: If model cannot be loaded
        """
        if not self.model_path.exists():
            raise FileNotFoundError(f"❌ REQUIRED: Model file not found: {self.model_path}")
        
        try:
            if not self.quiet:
                print(f"🔄 Loading YOLO model from {self.model_path}...")
            self.model = YOLO(str(self.model_path))
            if not self.quiet:
                print("✅ YOLO model loaded successfully")
            return True
            
        except Exception as e:
            raise Exception(f"❌ CRITICAL: Failed to load YOLO model: {e}")
    
    def is_model_loaded(self) -> bool:
        """Check if the model is properly loaded"""
        return self.model is not None
    
    def classify_image(self, image_path: Optional[str] = None, image_data: Optional[bytes] = None) -> Dict:
        """Classify an image using YOLO
        
        Args:
            image_path: Path to image file (optional)
            image_data: Raw image bytes (optional)
            
        Returns:
            Dictionary with classification results
            
        Raises:
            ValueError: If neither image_path nor image_data provided
            RuntimeError: If model is not loaded
        """
        if not self.is_model_loaded():
            raise RuntimeError("❌ YOLO model is not loaded. Cannot perform classification.")
        
        try:
            # Load image
            if image_path:
                image = Image.open(image_path)
            elif image_data:
                image = Image.open(io.BytesIO(image_data))
            else:
                raise ValueError("Either image_path or image_data must be provided")
            
            # Perform YOLO classification
            return self._classify_with_yolo(image)
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "result": None,
                "confidence": 0.0,
                "all_confidences": {}
            }
    
    def _classify_with_yolo(self, image: Image.Image) -> Dict:
        """Perform real YOLO classification"""
        try:
            # Run YOLO inference
            results = self.model(image, verbose=False)
            
            if not results or len(results) == 0:
                return {
                    "success": False,
                    "error": "No YOLO results returned",
                    "result": None,
                    "confidence": 0.0,
                    "all_confidences": {}
                }
            
            # Get the first result
            result = results[0]
            
            # Extract predictions
            if hasattr(result, 'probs') and result.probs is not None:
                # Classification format
                probs = result.probs.data.cpu().numpy()
                top_class_idx = int(result.probs.top1)
                top_confidence = float(result.probs.top1conf)
                
                # Map class index to name
                predicted_class = self.class_mapping.get(top_class_idx, "misc")
                
                # Create confidence dictionary for all classes
                all_confidences = {}
                for idx, class_name in self.class_mapping.items():
                    if idx < len(probs):
                        all_confidences[class_name] = float(probs[idx])
                    else:
                        all_confidences[class_name] = 0.0
                
            else:
                # Detection format - use highest confidence detection
                boxes = result.boxes
                if boxes is not None and len(boxes) > 0:
                    # Get highest confidence detection
                    confidences = boxes.conf.cpu().numpy()
                    classes = boxes.cls.cpu().numpy()
                    
                    best_idx = confidences.argmax()
                    top_class_idx = int(classes[best_idx])
                    top_confidence = float(confidences[best_idx])
                    
                    predicted_class = self.class_mapping.get(top_class_idx, "misc")
                    
                    # Create confidence dictionary
                    all_confidences = {name: 0.0 for name in self.class_mapping.values()}
                    all_confidences[predicted_class] = top_confidence
                    
                    # Distribute remaining confidence among other classes
                    remaining = 1.0 - top_confidence
                    other_classes = [name for name in all_confidences.keys() if name != predicted_class]
                    if other_classes:
                        per_other = remaining / len(other_classes)
                        for cls in other_classes:
                            all_confidences[cls] = per_other
                else:
                    # No detections
                    return {
                        "success": False,
                        "error": "No objects detected in image",
                        "result": None,
                        "confidence": 0.0,
                        "all_confidences": {}
                    }
            
            return {
                "success": True,
                "result": predicted_class,
                "confidence": top_confidence,
                "all_confidences": all_confidences,
                "method": "yolo"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"YOLO classification error: {e}",
                "result": None,
                "confidence": 0.0,
                "all_confidences": {}
            }
    
    def classify_base64(self, base64_data: str) -> Dict:
        """Classify an image from base64 data
        
        Args:
            base64_data: Base64 encoded image data
            
        Returns:
            Dictionary with classification results
        """
        try:
            # Decode base64 to image data
            image_data = base64.b64decode(base64_data)
            return self.classify_image(image_data=image_data)
        except Exception as e:
            return {
                "success": False,
                "error": f"Base64 decode error: {e}",
                "result": None,
                "confidence": 0.0,
                "all_confidences": {}
            }

def main():
    """Command line interface for the classifier"""
    parser = argparse.ArgumentParser(description="SmartBin YOLO Classification Backend")
    parser.add_argument("--model", "-m", default="best.pt", help="Path to YOLO model file")
    parser.add_argument("--image", "-i", help="Path to image file to classify")
    parser.add_argument("--base64", "-b", help="Base64 encoded image data")
    parser.add_argument("--json", "-j", action="store_true", help="Output results as JSON")
    
    args = parser.parse_args()
    
    try:
        # Initialize classifier
        classifier = SmartBinYOLOClassifier(model_path=args.model, quiet=args.json)
        
        if args.image:
            # Classify from image file
            result = classifier.classify_image(image_path=args.image)
        elif args.base64:
            # Classify from base64 data
            result = classifier.classify_base64(args.base64)
        else:
            print("❌ Please provide either --image or --base64 argument")
            sys.exit(1)
        
        # Output results
        if args.json:
            print(json.dumps(result, indent=2))
        else:
            if result["success"]:
                print(f"🎯 Classification: {result['result']}")
                print(f"📊 Confidence: {result['confidence']:.2%}")
                print(f"🔧 Method: {result['method']}")
                print("\n📈 All Confidences:")
                for cls, conf in result["all_confidences"].items():
                    print(f"  {cls}: {conf:.2%}")
            else:
                print(f"❌ Classification failed: {result['error']}")
                
    except Exception as e:
        print(f"❌ CRITICAL ERROR: {e}")
        if args.json:
            error_result = {
                "success": False,
                "error": str(e),
                "result": None,
                "confidence": 0.0,
                "all_confidences": {}
            }
            print(json.dumps(error_result, indent=2))
        sys.exit(1)

if __name__ == "__main__":
    main()
