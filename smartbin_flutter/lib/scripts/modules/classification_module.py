#!/usr/bin/env python3

import random
from typing import Dict, Any, Optional
import json


class ClassificationModule:
    """Classification module with static methods and fields"""

    # Static fields
    _initialized = False
    _model = None

    # Known classes for classification
    _classes = ['aluminium', 'plastic', 'paper', 'glass', 'organic', 'metal', 'cardboard']

    @staticmethod
    def handle_command(args: list):
        """Handle classification commands"""
        if not args:
            print("Error: No classification subcommand provided")
            return

        subcommand = args[0]

        if subcommand == 'init':
            ClassificationModule.init()

        elif subcommand == 'get-classes':
            classes = ClassificationModule.get_classes()
            print(json.dumps(classes))

        elif len(args) >= 1:  # classify with image path
            if not ClassificationModule.is_initialized():
                print("Error: Classification not initialized")
                return

            image_path = ' '.join(args)  # Join all args as image path
            if not image_path:
                print(json.dumps({"error": "No image path provided"}))
                return

            result = ClassificationModule.classify(image_path)
            if result:
                print(json.dumps(result))
            else:
                print(json.dumps({"error": "Classification failed"}))

        else:
            print("Error: Unknown classification subcommand")

    @staticmethod
    def is_initialized() -> bool:
        """Check if classification module is initialized"""
        return ClassificationModule._initialized

    @staticmethod
    def init() -> bool:
        """Initialize classification module with lazy imports"""
        if ClassificationModule._initialized:
            print("Success")
            return True

        try:
            # print("Initializing classification module...")

            # Lazy import of heavy libraries only when needed
            try:
                global YOLO
                from ultralytics import YOLO
                print("✅ YOLO imported successfully")

                # TODO: Replace with actual model loading
                # ClassificationModule._model = YOLO('yolo11n-cls.pt')
                # print("✅ YOLO model loaded")

                # For now, just set a placeholder
                ClassificationModule._model = "mock_model"

            except ImportError as e:
                print(f"Error: {e}. Using mock classification.")
                ClassificationModule._model = "mock_model"
            except Exception as e:
                print(f"⚠️ Model loading failed: {e}. Using mock classification.")
                ClassificationModule._model = "mock_model"

            ClassificationModule._initialized = True
            return True

        except Exception as e:
            print(f"Error initializing classification: {e}")
            return False

    @staticmethod
    def classify(image_path: str) -> Optional[Dict[str, Any]]:
        """Classify an image and return confidence scores"""
        if not ClassificationModule._initialized:
            print("Error: Classification not initialized")
            return None

        try:
            # Basic validation - check if path is not empty
            if not image_path:
                return {"error": "No image path provided"}

            # TODO: Replace with actual classification when model is loaded
            if ClassificationModule._model == "mock_model":
                return ClassificationModule._mock_classify(image_path)
            else:
                # Actual YOLO classification
                return ClassificationModule._yolo_classify(image_path)

        except Exception as e:
            print(f"Error during classification: {e}")
            return {"error": f"Classification failed: {str(e)}"}

    @staticmethod
    def stop():
        """Stop the classification module and free resources"""
        if ClassificationModule._initialized:
            ClassificationModule._cleanup()

    @staticmethod
    def _cleanup():
        """Clean up classification resources"""
        try:
            # Free model memory if loaded
            if ClassificationModule._model and ClassificationModule._model != "mock_model":
                del ClassificationModule._model
                print("✅ Classification model freed from memory")

            ClassificationModule._model = None
            ClassificationModule._initialized = False

        except Exception as e:
            print(f"⚠️ Classification cleanup warning: {e}")

    @staticmethod
    def _mock_classify(image_path: str) -> Dict[str, float]:
        """
        Perform mock classification by generating random confidence values
        that sum to approximately 1.0
        """
        print(f"🎭 Mock classifying: {image_path}")

        # Generate random weights
        weights = [random.random() for _ in ClassificationModule._classes]
        total_weight = sum(weights)

        # Normalize to create confidence values
        confidences = {
            cls: round(weight / total_weight, 2)
            for cls, weight in zip(ClassificationModule._classes, weights)
        }

        return confidences

    @staticmethod
    def _yolo_classify(image_path: str) -> Dict[str, Any]:
        """
        Perform actual YOLO classification
        """
        try:
            print(f"🔍 YOLO classifying: {image_path}")

            # TODO: Implement actual YOLO classification
            # results = ClassificationModule._model(image_path)
            #
            # # Process results and convert to confidence dictionary
            # confidences = {}
            # for result in results:
            #     probs = result.probs
            #     for i, prob in enumerate(probs.data):
            #         class_name = ClassificationModule._classes[i] if i < len(ClassificationModule._classes) else f"class_{i}"
            #         confidences[class_name] = float(prob)
            #
            # return confidences

            # For now, return mock data
            return ClassificationModule._mock_classify(image_path)

        except Exception as e:
            print(f"❌ YOLO classification error: {e}")
            return {"error": f"YOLO classification failed: {str(e)}"}

    @staticmethod
    def get_classes() -> list:
        """Get the list of supported classification classes"""
        return ClassificationModule._classes.copy()

    @staticmethod
    def set_classes(classes: list):
        """Set the list of classification classes"""
        ClassificationModule._classes = classes.copy()
        print(f"✅ Classification classes updated: {ClassificationModule._classes}")

    @staticmethod
    def get_model_info() -> Dict[str, Any]:
        """Get information about the loaded model"""
        return {
            "initialized": ClassificationModule._initialized,
            "model_type": "mock" if ClassificationModule._model == "mock_model" else "yolo",
            "classes": ClassificationModule._classes,
            "num_classes": len(ClassificationModule._classes)
        }
