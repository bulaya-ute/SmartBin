#!/usr/bin/env python3
"""
Dummy Dataset Training Script for ESP32 TensorFlow Lite Testing
This script creates synthetic data and trains a minimal model for compilation testing
"""

import tensorflow as tf
import numpy as np
import os
from tensorflow.keras import layers, models
import matplotlib.pyplot as plt

# Model configuration (same as real training script)
IMG_HEIGHT = 48
IMG_WIDTH = 48
IMG_CHANNELS = 3
BATCH_SIZE = 32
EPOCHS = 5  # Just enough to create a valid model
NUM_CLASSES = 4  # metal, misc, paper, plastic

# Class names (must match the order in your dataset)
CLASS_NAMES = ['metal', 'misc', 'paper', 'plastic']

def create_dummy_dataset(num_samples_per_class=100):
    """
    Create synthetic dataset with random images and labels
    """
    print(f"Creating dummy dataset with {num_samples_per_class} samples per class...")
    
    # Generate random images
    total_samples = num_samples_per_class * NUM_CLASSES
    X = np.random.randint(0, 256, (total_samples, IMG_HEIGHT, IMG_WIDTH, IMG_CHANNELS), dtype=np.uint8)
    
    # Create labels (one-hot encoded)
    y = np.zeros((total_samples, NUM_CLASSES))
    for i in range(total_samples):
        class_idx = i // num_samples_per_class
        y[i, class_idx] = 1
    
    # Normalize images to [0, 1]
    X = X.astype(np.float32) / 255.0
    
    # Split into train and validation
    split_idx = int(0.8 * total_samples)
    
    X_train, X_val = X[:split_idx], X[split_idx:]
    y_train, y_val = y[:split_idx], y[split_idx:]
    
    print(f"Training samples: {X_train.shape[0]}")
    print(f"Validation samples: {X_val.shape[0]}")
    
    return (X_train, y_train), (X_val, y_val)

def create_model():
    """
    Create the exact same model architecture as the real training script
    """
    model = models.Sequential([
        # First convolutional block
        layers.Conv2D(16, (3, 3), activation='relu', input_shape=(IMG_HEIGHT, IMG_WIDTH, IMG_CHANNELS)),
        layers.BatchNormalization(),
        layers.MaxPooling2D((2, 2)),
        layers.Dropout(0.25),
        
        # Second convolutional block
        layers.Conv2D(32, (3, 3), activation='relu'),
        layers.BatchNormalization(),
        layers.MaxPooling2D((2, 2)),
        layers.Dropout(0.25),
        
        # Third convolutional block
        layers.Conv2D(64, (3, 3), activation='relu'),
        layers.BatchNormalization(),
        layers.MaxPooling2D((2, 2)),
        layers.Dropout(0.25),
        
        # Flatten and dense layers
        layers.Flatten(),
        layers.Dense(128, activation='relu'),
        layers.BatchNormalization(),
        layers.Dropout(0.5),
        layers.Dense(NUM_CLASSES, activation='softmax')
    ])
    
    return model

def convert_to_tflite(model, model_path):
    """
    Convert trained model to TensorFlow Lite format for ESP32
    """
    # Convert to TensorFlow Lite
    converter = tf.lite.TFLiteConverter.from_keras_model(model)
    
    # Optimization for microcontrollers
    converter.optimizations = [tf.lite.Optimize.DEFAULT]
    converter.target_spec.supported_types = [tf.float32]
    
    tflite_model = converter.convert()
    
    # Save the TFLite model
    tflite_path = model_path.replace('.h5', '.tflite')
    with open(tflite_path, 'wb') as f:
        f.write(tflite_model)
    
    print(f"TensorFlow Lite model saved to: {tflite_path}")
    print(f"Model size: {len(tflite_model)} bytes")
    
    return tflite_path

def generate_header_file(tflite_path, header_path):
    """
    Generate C++ header file with model data for ESP32
    """
    with open(tflite_path, 'rb') as f:
        model_data = f.read()
    
    with open(header_path, 'w') as f:
        f.write('#include "Classification.h"\n\n')
        f.write('// Auto-generated model data (DUMMY MODEL FOR TESTING)\n')
        f.write('// Replace this file with a real trained model when ready\n')
        f.write('const unsigned char waste_classification_model[] = {\n')
        
        for i, byte in enumerate(model_data):
            if i % 16 == 0:
                f.write('  ')
            f.write(f'0x{byte:02x}')
            if i < len(model_data) - 1:
                f.write(', ')
            if i % 16 == 15:
                f.write('\n')
        
        f.write('\n};\n\n')
        f.write(f'const int waste_classification_model_len = {len(model_data)};\n')
    
    print(f"Header file generated: {header_path}")

def test_model_inference(model, sample_data):
    """
    Test the model with sample data to ensure it works
    """
    print("Testing model inference...")
    
    # Test with a single sample
    test_input = sample_data[0][:1]  # Take first sample
    prediction = model.predict(test_input)
    
    print("Test prediction:")
    for i, class_name in enumerate(CLASS_NAMES):
        print(f"  {class_name}: {prediction[0][i]:.3f}")
    
    predicted_class = np.argmax(prediction[0])
    print(f"Predicted class: {CLASS_NAMES[predicted_class]} ({prediction[0][predicted_class]:.3f})")

def train_dummy_model(output_dir):
    """
    Main training function for dummy model
    """
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Create dummy dataset
    (X_train, y_train), (X_val, y_val) = create_dummy_dataset()
    
    # Create model
    print("Creating model...")
    model = create_model()
    
    # Compile model
    model.compile(
        optimizer='adam',
        loss='categorical_crossentropy',
        metrics=['accuracy']
    )
    
    # Print model summary
    print("\nModel Architecture:")
    model.summary()
    
    # Train model (just a few epochs for testing)
    print(f"\nTraining dummy model for {EPOCHS} epochs...")
    history = model.fit(
        X_train, y_train,
        batch_size=BATCH_SIZE,
        epochs=EPOCHS,
        validation_data=(X_val, y_val),
        verbose=1
    )
    
    # Test model inference
    test_model_inference(model, (X_val, y_val))
    
    # Save model
    model_path = os.path.join(output_dir, 'dummy_waste_classifier.h5')
    model.save(model_path)
    print(f"Dummy model saved to: {model_path}")
    
    # Convert to TensorFlow Lite
    tflite_path = convert_to_tflite(model, model_path)
    
    # Generate header file for ESP32
    header_path = os.path.join(output_dir, 'model_data.cpp')
    generate_header_file(tflite_path, header_path)
    
    # Plot training history
    plt.figure(figsize=(12, 4))
    
    plt.subplot(1, 2, 1)
    plt.plot(history.history['accuracy'], label='Training Accuracy')
    plt.plot(history.history['val_accuracy'], label='Validation Accuracy')
    plt.title('Dummy Model Accuracy')
    plt.xlabel('Epoch')
    plt.ylabel('Accuracy')
    plt.legend()
    
    plt.subplot(1, 2, 2)
    plt.plot(history.history['loss'], label='Training Loss')
    plt.plot(history.history['val_loss'], label='Validation Loss')
    plt.title('Dummy Model Loss')
    plt.xlabel('Epoch')
    plt.ylabel('Loss')
    plt.legend()
    
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'dummy_training_history.png'))
    plt.show()
    
    print(f"\n✅ Dummy model training completed!")
    print(f"📁 Files saved to: {output_dir}")
    print(f"📋 Next steps:")
    print(f"   1. Copy {header_path} to your ESP32 project")
    print(f"   2. Replace the existing model_data.cpp file")
    print(f"   3. Compile and test on ESP32")
    print(f"   4. When ready, replace with real trained model using same process")
    
    return model_path, tflite_path, header_path

if __name__ == "__main__":
    print("🤖 Dummy Model Training for ESP32 TensorFlow Lite Testing")
    print("=" * 60)
    print(f"📊 Model Configuration:")
    print(f"   - Input size: {IMG_WIDTH}x{IMG_HEIGHT}x{IMG_CHANNELS}")
    print(f"   - Classes: {NUM_CLASSES} ({', '.join(CLASS_NAMES)})")
    print(f"   - Training epochs: {EPOCHS} (minimal for testing)")
    print(f"   - Purpose: Compilation and integration testing")
    print("=" * 60)
    
    # Configuration
    OUTPUT_DIR = "dummy_model_output"
    
    # Train dummy model
    model_path, tflite_path, header_path = train_dummy_model(OUTPUT_DIR)
    
    print(f"\n🎯 IMPORTANT NOTES:")
    print(f"   - This is a DUMMY model trained on random data")
    print(f"   - It will NOT classify waste accurately")
    print(f"   - Use it ONLY to test ESP32 compilation and inference")
    print(f"   - Replace with real trained model when ready")
