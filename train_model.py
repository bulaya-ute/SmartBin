#!/usr/bin/env python3
"""
TensorFlow Lite Model Training Script for Waste Classification
This script trains a lightweight CNN model for ESP32 deployment
"""

import tensorflow as tf
import numpy as np
import os
from tensorflow.keras import layers, models
from tensorflow.keras.preprocessing.image import ImageDataGenerator
import matplotlib.pyplot as plt

# Model configuration
IMG_HEIGHT = 48
IMG_WIDTH = 48
IMG_CHANNELS = 3
BATCH_SIZE = 32
EPOCHS = 50
NUM_CLASSES = 4  # metal, misc, paper, plastic

# Class names (must match the order in your dataset)
CLASS_NAMES = ['metal', 'misc', 'paper', 'plastic']

def create_model():
    """
    Create a lightweight CNN model optimized for ESP32
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

def prepare_data(data_dir):
    """
    Prepare training and validation data with augmentation
    Expected directory structure:
    data_dir/
        train/
            metal/
            misc/
            paper/
            plastic/
        val/
            metal/
            misc/
            paper/
            plastic/
    """
    
    # Data augmentation for training
    train_datagen = ImageDataGenerator(
        rescale=1./255,
        rotation_range=20,
        width_shift_range=0.2,
        height_shift_range=0.2,
        horizontal_flip=True,
        zoom_range=0.2,
        shear_range=0.2,
        fill_mode='nearest'
    )
    
    # Only rescaling for validation
    val_datagen = ImageDataGenerator(rescale=1./255)
    
    train_generator = train_datagen.flow_from_directory(
        os.path.join(data_dir, 'train'),
        target_size=(IMG_HEIGHT, IMG_WIDTH),
        batch_size=BATCH_SIZE,
        class_mode='categorical',
        classes=CLASS_NAMES
    )
    
    val_generator = val_datagen.flow_from_directory(
        os.path.join(data_dir, 'val'),
        target_size=(IMG_HEIGHT, IMG_WIDTH),
        batch_size=BATCH_SIZE,
        class_mode='categorical',
        classes=CLASS_NAMES
    )
    
    return train_generator, val_generator

def convert_to_tflite(model, model_path):
    """
    Convert trained model to TensorFlow Lite format for ESP32
    """
    # Convert to TensorFlow Lite
    converter = tf.lite.TFLiteConverter.from_keras_model(model)
    
    # Optimization for microcontrollers
    converter.optimizations = [tf.lite.Optimize.DEFAULT]
    converter.target_spec.supported_types = [tf.float32]
    
    # For even smaller models, you can use quantization:
    # converter.target_spec.supported_types = [tf.int8]
    # converter.inference_input_type = tf.int8
    # converter.inference_output_type = tf.int8
    
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
        f.write('// Auto-generated model data\n')
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

def train_model(data_dir, output_dir):
    """
    Main training function
    """
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Prepare data
    print("Preparing data...")
    train_gen, val_gen = prepare_data(data_dir)
    
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
    model.summary()
    
    # Define callbacks
    callbacks = [
        tf.keras.callbacks.EarlyStopping(patience=10, restore_best_weights=True),
        tf.keras.callbacks.ReduceLROnPlateau(factor=0.5, patience=5),
        tf.keras.callbacks.ModelCheckpoint(
            os.path.join(output_dir, 'best_model.h5'),
            save_best_only=True
        )
    ]
    
    # Train model
    print("Training model...")
    history = model.fit(
        train_gen,
        epochs=EPOCHS,
        validation_data=val_gen,
        callbacks=callbacks
    )
    
    # Save final model
    model_path = os.path.join(output_dir, 'waste_classifier.h5')
    model.save(model_path)
    
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
    plt.title('Model Accuracy')
    plt.xlabel('Epoch')
    plt.ylabel('Accuracy')
    plt.legend()
    
    plt.subplot(1, 2, 2)
    plt.plot(history.history['loss'], label='Training Loss')
    plt.plot(history.history['val_loss'], label='Validation Loss')
    plt.title('Model Loss')
    plt.xlabel('Epoch')
    plt.ylabel('Loss')
    plt.legend()
    
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'training_history.png'))
    plt.show()
    
    print(f"Training completed! Files saved to: {output_dir}")
    print(f"Replace the contents of model_data.cpp with the generated file")

if __name__ == "__main__":
    # Configuration
    DATA_DIR = "path/to/your/dataset"  # Update this path
    OUTPUT_DIR = "model_output"
    
    print("Starting waste classification model training...")
    print(f"Input image size: {IMG_WIDTH}x{IMG_HEIGHT}x{IMG_CHANNELS}")
    print(f"Number of classes: {NUM_CLASSES}")
    print(f"Classes: {CLASS_NAMES}")
    
    # Uncomment to start training
    train_model(DATA_DIR, OUTPUT_DIR)
    
    print("Update DATA_DIR path and uncomment train_model() to start training")
