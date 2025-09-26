#!/usr/bin/env python3

import random
from typing import Dict, Any, Optional
import json
import os

YOLO: Any = None

class ClassificationModule:
    """Classification module with static methods and fields"""

    is_initialized = False
    model: Any = None

    # Known classes for classification
    known_classes = ['aluminium', 'carton', 'e_waste', 'glass', 'organic_waste', 'paper_and_cardboard', 'plastic', "textile", "wood"]

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
            if not ClassificationModule.is_initialized:
                print("Error: Classification not initialized")
                return

            image_path = ' '.join(args)  # Join all args as image path
            if not image_path:
                print(json.dumps({"error": "No image path provided"}))
                return

            result = ClassificationModule.classify(image_path)
            if result:
                print(f"Results: {json.dumps(result)}")
            else:
                print(json.dumps({"error": "Classification failed"}))

        else:
            print("Error: Unknown classification subcommand")


    @staticmethod
    def init() -> bool:
        """Initialize classification module with lazy imports"""
        if ClassificationModule.is_initialized:
            print("Success - classification already initialized.")
            return True

        try:
            # Lazy import of heavy libraries only when needed
            try:
                global YOLO
                if YOLO is None:
                    from ultralytics import YOLO

                # // Load model
                model_path = os.path.abspath('classifier_model_yolo.pt')
                ClassificationModule.model = YOLO(model_path)

            except Exception as e:
                print(f"⚠️ Model loading failed: {e}. ")
                return False

            ClassificationModule.is_initialized = True
            print("Success - classification initialized.")
            return True

        except Exception as e:
            print(f"Error initializing classification: {e}")
            return False

    @staticmethod
    def classify(image_path: str) -> Optional[Dict[str, Any]]:
        """Classify an image and return confidence scores"""
        if not ClassificationModule.is_initialized:
            print("Error: Classification not initialized")
            return None

        try:
            # Basic validation - check if path is not empty
            if not image_path:
                return {"error": "No image path provided"}

            if ClassificationModule.model == "mock_model":
                return ClassificationModule._mock_classify(image_path)
            else:
                # Actual YOLO classification
                return ClassificationModule._yolo_classify(image_path)

        except Exception as e:
            print(f"Error during classification: {e}")
            return None

    @staticmethod
    def stop():
        """Stop the classification module and free resources"""
        if ClassificationModule.is_initialized:
            ClassificationModule._cleanup()

    @staticmethod
    def _cleanup():
        """Clean up classification resources"""
        try:
            # Free model memory if loaded
            if ClassificationModule.model and ClassificationModule.model != "mock_model":
                del ClassificationModule.model
                print("✅ Classification model freed from memory")

            ClassificationModule.model = None
            ClassificationModule.is_initialized = False

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
        weights = [random.random() for _ in ClassificationModule.known_classes]
        total_weight = sum(weights)

        # Normalize to create confidence values
        confidences = {
            cls: round(weight / total_weight, 2)
            for cls, weight in zip(ClassificationModule.known_classes, weights)
        }

        return confidences

    @staticmethod
    def _yolo_classify(image_path: str):
        """
        Perform actual YOLO classification
        """
        image_path = os.path.abspath(image_path)
        # print(f"Abs path: {image_path}")
        model = ClassificationModule.model
        if model is None:
            print("Error: YOLO model not loaded")
            return None

        # Run inference
        results = model.predict(image_path, verbose=False)

        class_names: dict[int, str] = results[0].names
        probs = [round(float(i), 3) for i in list(results[0].probs.data)]

        class_confidences = {}

        for class_index, class_name in class_names.items():
            class_confidences[class_name] = probs[class_index]

        return class_confidences

    @staticmethod
    def get_classes() -> list:
        """Get the list of supported classification classes"""
        return ClassificationModule.known_classes.copy()

    @staticmethod
    def set_classes(classes: list):
        """Set the list of classification classes"""
        ClassificationModule.known_classes = classes.copy()
        print(f"✅ Classification classes updated: {ClassificationModule.known_classes}")

    @staticmethod
    def get_model_info() -> Dict[str, Any]:
        """Get information about the loaded model"""
        return {
            "initialized": ClassificationModule.is_initialized,
            "model_type": "mock" if ClassificationModule.model == "mock_model" else "yolo",
            "classes": ClassificationModule.known_classes,
            "num_classes": len(ClassificationModule.known_classes)
        }
