import tensorflow as tf
from tensorflow.keras import layers, models
import numpy as np
import pathlib

# ------------------------------
# Parameters
# ------------------------------
IMG_SIZE = (48, 48)   # Small for ESP32
NUM_CLASSES = 4
BATCH_SIZE = 32
EPOCHS = 20

# ------------------------------
# Load your dataset
# ------------------------------
# Expect folder structure like:
# dataset/
#   paper/
#   metal/
#   glass/
#   misc/
data_dir = pathlib.Path("dataset")

train_ds = tf.keras.utils.image_dataset_from_directory(
    data_dir,
    validation_split=0.2,
    subset="training",
    seed=42,
    image_size=IMG_SIZE,
    color_mode="grayscale",
    batch_size=BATCH_SIZE
)

val_ds = tf.keras.utils.image_dataset_from_directory(
    data_dir,
    validation_split=0.2,
    subset="validation",
    seed=42,
    image_size=IMG_SIZE,
    color_mode="grayscale",
    batch_size=BATCH_SIZE
)

# Normalize to 0-1
def normalize_img(image, label):
    return tf.cast(image, tf.float32) / 255.0, label

train_ds = train_ds.map(normalize_img)
val_ds = val_ds.map(normalize_img)

# ------------------------------
# Model definition (tiny CNN)
# ------------------------------
model = models.Sequential([
    layers.Conv2D(8, (3, 3), activation="relu", input_shape=(IMG_SIZE[0], IMG_SIZE[1], 1)),
    layers.MaxPooling2D((2, 2)),
    layers.Conv2D(16, (3, 3), activation="relu"),
    layers.MaxPooling2D((2, 2)),
    layers.Flatten(),
    layers.Dense(32, activation="relu"),
    layers.Dense(NUM_CLASSES, activation="softmax")
])

model.compile(optimizer="adam",
              loss="sparse_categorical_crossentropy",
              metrics=["accuracy"])

model.summary()

# ------------------------------
# Training
# ------------------------------
model.fit(train_ds, validation_data=val_ds, epochs=EPOCHS)

# ------------------------------
# Save normal Keras model
# ------------------------------
model.save("waste_classifier.h5")

# ------------------------------
# Convert to TFLite (quantized)
# ------------------------------
converter = tf.lite.TFLiteConverter.from_keras_model(model)
converter.optimizations = [tf.lite.Optimize.DEFAULT]  # Post-training quantization
tflite_model = converter.convert()

# Save .tflite model
with open("waste_classifier.tflite", "wb") as f:
    f.write(tflite_model)

print("TFLite model size:", len(tflite_model), "bytes")
