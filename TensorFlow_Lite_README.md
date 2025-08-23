# TensorFlow Lite Integration for ESP32 Waste Classification

This implementation provides complete control over the model training and deployment process using TensorFlow Lite for Microcontrollers.

## 🚀 **Benefits Over Edge Impulse**

- **Full Control**: Train custom architectures with your own datasets
- **No Limitations**: No restrictions on model complexity or data preprocessing
- **Rigorous Testing**: Test under different conditions and datasets
- **Cost Effective**: No subscription fees or cloud dependencies
- **Offline Training**: Train models locally with full access to training process

## 📋 **Requirements**

### ESP32 Side
- ESP32-CAM with PSRAM enabled
- Arduino IDE with ESP32 board package
- TensorFlowLite_ESP32 library

### Training Side (Python)
```bash
pip install -r requirements_training.txt
```

## 🔧 **Setup Instructions**

### 1. Install TensorFlow Lite Library for ESP32

In Arduino IDE:
1. Go to **Tools > Manage Libraries**
2. Search for "TensorFlowLite_ESP32"
3. Install the latest version by TensorFlow Authors

### 2. Prepare Your Dataset

Organize your dataset in this structure:
```
dataset/
├── train/
│   ├── metal/
│   ├── misc/
│   ├── paper/
│   └── plastic/
└── val/
    ├── metal/
    ├── misc/
    ├── paper/
    └── plastic/
```

### 3. Train Your Model

```bash
# Update the DATA_DIR path in train_model.py
python train_model.py
```

This will:
- Train a lightweight CNN optimized for ESP32
- Convert to TensorFlow Lite format
- Generate C++ header file with model data
- Create training visualizations

### 4. Deploy to ESP32

1. Replace `model_data.cpp` with the generated file
2. Upload the code to your ESP32-CAM
3. Monitor serial output for classification results

## 🏗️ **Model Architecture**

The default model is optimized for ESP32 constraints:

- **Input**: 48x48x3 RGB images
- **Architecture**: 3 Conv2D blocks with BatchNorm and Dropout
- **Output**: 4 classes (metal, misc, paper, plastic)
- **Size**: ~60KB (fits comfortably in ESP32 flash)
- **Inference Time**: ~200-500ms per image

## 📊 **Model Performance**

### Memory Usage
- **Model Size**: ~60KB
- **RAM Usage**: ~60KB tensor arena
- **Total Memory**: <200KB (leaves plenty for other operations)

### Processing Pipeline
1. **Image Capture**: ESP32-CAM captures 160x120 RGB565 image
2. **Preprocessing**: Resize to 48x48, convert RGB565→RGB, normalize
3. **Inference**: TensorFlow Lite runs CNN inference
4. **Post-processing**: Extract class probabilities and confidence

## 🎛️ **Configuration Options**

### Model Parameters (Classification.cpp)
```cpp
const int MODEL_INPUT_WIDTH = 48;     // Input width
const int MODEL_INPUT_HEIGHT = 48;    // Input height  
const int MODEL_INPUT_CHANNELS = 3;   // RGB channels
const int kTensorArenaSize = 60 * 1024; // Tensor arena size
```

### Camera Settings (Camera.cpp)
```cpp
.frame_size = FRAMESIZE_QQVGA,    // 160x120 for speed
.pixel_format = PIXFORMAT_RGB565, // Compatible format
.fb_location = CAMERA_FB_IN_PSRAM // Use PSRAM
```

### Confidence Thresholds (Classification.h)
```cpp
const float CONFIDENCE_THRESHOLD = 0.60f;  // 60% minimum
const float MINIMUM_CONFIDENCE = 0.30f;    // 30% absolute minimum
```

## 🔍 **Debugging and Monitoring**

### Serial Output
```
[Classification] Processing image with TensorFlow Lite...
[Classification] Image preprocessed successfully
[Classification] ✅ Inference completed in 245 ms
[Classification] Model output:
[Classification] metal: 15.2%
[Classification] misc: 8.7%
[Classification] paper: 71.3%
[Classification] plastic: 4.8%
[Classification] ✅ Top prediction: paper (71.3% confidence)
```

### Debug Functions
- `printModelInfo()`: Display model architecture details
- `printClassificationDetails()`: Show detailed classification results
- Memory monitoring in main loop

## 🚀 **Advanced Optimizations**

### Model Quantization
For even smaller models, enable quantization in training:
```python
converter.target_spec.supported_types = [tf.int8]
converter.inference_input_type = tf.int8
converter.inference_output_type = tf.int8
```

### Custom Architectures
Modify `create_model()` in `train_model.py` to experiment with:
- Different layer sizes
- Alternative architectures (MobileNet, EfficientNet)
- Transfer learning from pre-trained models

### Data Augmentation
Customize augmentation in `prepare_data()`:
- Lighting variations
- Background changes
- Perspective transforms
- Noise injection

## 🔧 **Troubleshooting**

### Common Issues

1. **Model too large**: Reduce `kTensorArenaSize` or simplify model
2. **Out of memory**: Enable PSRAM, reduce frame buffer count
3. **Slow inference**: Reduce input resolution or model complexity
4. **Poor accuracy**: Collect more training data, improve augmentation

### Performance Tips

1. **Use PSRAM**: Essential for larger models and frame buffers
2. **Optimize input size**: Balance between accuracy and speed
3. **Monitor memory**: Use heap monitoring in main loop
4. **Watchdog safety**: Add `yield()` calls during long operations

## 📈 **Next Steps**

1. **Collect Dataset**: Gather diverse images of waste items
2. **Train Model**: Use the provided training script
3. **Test Performance**: Validate accuracy and timing
4. **Deploy and Monitor**: Upload to ESP32 and monitor real-world performance
5. **Iterate**: Improve model based on real-world results

This implementation gives you complete control over your waste classification system!
