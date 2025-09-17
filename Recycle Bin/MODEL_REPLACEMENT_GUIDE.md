# 🔄 Model Replacement Guide for ESP32 TensorFlow Lite

This guide explains how to replace the dummy model with a well-trained model for your ESP32 waste classification system.

## 📋 **TL;DR - Quick Model Replacement**

**It's just ONE file replacement!**

1. Train your new model (using `train_model.py`)
2. Replace `esp32_sketches/SmartBinEsp/model_data.cpp` with the newly generated file
3. Upload to ESP32 - Done! ✅

## 🔍 **Understanding Model Compatibility**

### **What Makes Models Compatible?**

✅ **Compatible (Just replace the file):**
- Same input dimensions (48×48×3)
- Same number of output classes (4)
- Same class order (metal, misc, paper, plastic)
- Different weights and biases (this is expected!)
- Different training accuracy
- Different model size (within ESP32 memory limits)

❌ **Incompatible (Requires code changes):**
- Different input dimensions (e.g., 64×64 instead of 48×48)
- Different number of classes (e.g., 5 classes instead of 4)
- Different class names or order
- Model too large for ESP32 memory

## 📁 **File Structure Overview**

```
esp32_sketches/SmartBinEsp/
├── model_data.cpp          ← REPLACE THIS FILE
├── Classification.h        ← Configuration (rarely needs changes)
├── Classification.cpp      ← Logic (rarely needs changes)
├── Camera.h/.cpp          ← Hardware (no changes needed)
├── SmartBinEsp.ino        ← Main code (no changes needed)
└── other files...
```

## 🔧 **Step-by-Step Replacement Process**

### **Step 1: Train Your New Model**

```bash
# Update your dataset path in train_model.py
python train_model.py
```

This generates:
- `model_output/waste_classifier.h5` (Keras model)
- `model_output/waste_classifier.tflite` (TensorFlow Lite model)
- `model_output/model_data.cpp` ← **This is what you need!**

### **Step 2: Replace the Model File**

```bash
# Copy new model to ESP32 project
cp model_output/model_data.cpp esp32_sketches/SmartBinEsp/model_data.cpp
```

### **Step 3: Verify Compatibility** (Optional but Recommended)

Check that the generated `model_data.cpp` has:

```cpp
const unsigned char waste_classification_model[] = {
    0x18, 0x00, 0x00, 0x00, 0x54, 0x46, 0x4c, 0x33, // TFLite header
    // ... thousands of hex bytes ...
};

const int waste_classification_model_len = XXXXX; // Some number
```

### **Step 4: Upload to ESP32**

1. Open Arduino IDE
2. Open your SmartBinEsp project
3. Compile (should work if model is compatible)
4. Upload to ESP32
5. Monitor serial output

## 🔧 **Configuration Changes (If Needed)**

### **If Your Model Has Different Dimensions**

Edit `Classification.h` and `Classification.cpp`:

```cpp
// In Classification.h and Classification.cpp
const int MODEL_INPUT_WIDTH = 48;    // Change if different
const int MODEL_INPUT_HEIGHT = 48;   // Change if different  
const int MODEL_INPUT_CHANNELS = 3;  // Usually stays 3 for RGB
const int MODEL_OUTPUT_CLASSES = 4;  // Change if different number of classes
```

### **If Your Model Has Different Classes**

Edit `Classification.cpp`:

```cpp
// Update class names to match your training
const char* class_names[MODEL_OUTPUT_CLASSES] = {"metal", "misc", "paper", "plastic"};
```

### **If Your Model Is Too Large**

Edit `Classification.cpp`:

```cpp
// Increase tensor arena size (but watch ESP32 memory limits)
const int kTensorArenaSize = 80 * 1024; // Increase from 60KB to 80KB
```

## 📊 **Testing Your New Model**

### **Serial Monitor Output**

Look for these messages to confirm the model loaded correctly:

```
[Classification] ✅ Model loaded successfully
[Classification] ✅ Tensors allocated successfully
[Classification] Model input: 48x48x3
[Classification] Model output classes: 4
[Classification] ✅ TensorFlow Lite initialized successfully
```

### **Classification Results**

During inference, you should see:

```
[Classification] Model output:
[Classification] metal: 15.2%
[Classification] misc: 8.7%
[Classification] paper: 71.3%
[Classification] plastic: 4.8%
[Classification] ✅ Top prediction: paper (71.3% confidence)
```

## 🚨 **Troubleshooting**

### **"Model version not supported"**
- Your TensorFlow Lite version is incompatible
- Regenerate the model with the same TensorFlow version

### **"Failed to allocate tensors"**
- Model is too large for ESP32 memory
- Increase `kTensorArenaSize` or reduce model complexity

### **Random/Poor Classifications**
- Model not properly trained
- Wrong input preprocessing
- Incorrect class mapping

### **Compilation Errors**
- Check that `model_data.cpp` syntax is correct
- Ensure no missing commas or brackets in the byte array

## 🎯 **Model Training Tips for ESP32 Compatibility**

### **Keep Models Small**
```python
# In your training script, use smaller architectures
layers.Conv2D(16, (3, 3))  # Instead of 64 filters
layers.Dense(64)           # Instead of 256 units
```

### **Use Quantization for Smaller Models**
```python
# In convert_to_tflite() function
converter.target_spec.supported_types = [tf.int8]  # Quantized
converter.inference_input_type = tf.int8
converter.inference_output_type = tf.int8
```

### **Test Model Size Before Deployment**
```python
# Check model size after conversion
tflite_model = converter.convert()
print(f"Model size: {len(tflite_model)} bytes")  # Should be < 200KB
```

## 📈 **Iterative Model Development**

1. **Start with Dummy Model**: Test compilation and basic functionality
2. **Train on Small Dataset**: Verify real data pipeline works
3. **Expand Dataset**: Add more samples and variations
4. **Optimize Architecture**: Balance accuracy vs. speed/memory
5. **Deploy and Monitor**: Test in real-world conditions
6. **Iterate**: Improve based on performance data

## 🔄 **Quick Reference - Model Replacement Checklist**

- [ ] New model trained successfully
- [ ] `model_data.cpp` file generated
- [ ] File copied to ESP32 project directory
- [ ] Code compiles without errors
- [ ] ESP32 boots and initializes model
- [ ] Classification produces reasonable results
- [ ] Performance meets requirements (speed/accuracy)

**Remember**: As long as your model architecture matches (input/output dimensions and classes), you only need to replace the `model_data.cpp` file!
