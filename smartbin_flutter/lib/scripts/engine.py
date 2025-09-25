#!/usr/bin/env python3

import sys
import json
import random
import re

# Known classes for mock classification
CLASSES = ['aluminium', 'plastic', 'paper', 'glass', 'organic', 'metal', 'cardboard']

commands = {
    ""
}

def mock_classify(image_path):
    """
    Perform mock classification by generating random confidence values
    that sum to approximately 1.0
    """
    # Generate random weights
    weights = [random.random() for _ in CLASSES]
    total_weight = sum(weights)

    # Normalize to create confidence values
    confidences = {cls: round(weight / total_weight, 2) for cls, weight in zip(CLASSES, weights)}

    return confidences


def main():
    # Check if the script is called with "start" argument
    if len(sys.argv) != 2 or sys.argv[1] != "start":
        print("Usage: python script.py start")
        sys.exit(1)

    print("Ready")

    while True:
        try:
            # Get user input
            user_input = input().strip()

            # Handle exit commands
            if user_input.lower() in ['exit', 'quit']:
                break

            # Handle classify command
            if user_input.startswith('classify '):
                # Extract the image path (everything after "classify ")
                image_path = user_input[9:].strip()

                # Basic validation - check if path is not empty
                if not image_path:
                    print(json.dumps({"error": "No image path provided"}))
                    continue

                # Perform mock classification
                result = mock_classify(image_path)
                print(json.dumps(result))

            else:
                # Unknown command
                print(json.dumps({"error": "Unknown command. Use 'classify <path>' or 'exit/quit'"}))

        except KeyboardInterrupt:
            # Handle Ctrl+C gracefully
            print()
            break
        except EOFError:
            # Handle Ctrl+D or end of input
            break

if __name__ == "__main__":
    main()