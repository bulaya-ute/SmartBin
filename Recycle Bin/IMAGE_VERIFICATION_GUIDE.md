# ESP32-CAM Image Verification Guide

## How to Use

### 1. ESP32 Side
When your ESP32-CAM captures an image (e.g., when ultrasonic sensor triggers), it will automatically print the image data to the serial terminal in this format:

```
[Camera] === IMAGE DATA OUTPUT ===
==IMAGE_START==
FORMAT: JPEG
SIZE: 85432 bytes
DIMENSIONS: 1600x1200
TIMESTAMP: 12345678
BASE64_DATA:
/9j/4AAQSkZJRgABAQEAYABgAAD/2wBDAAEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEB...
[Base64 data continues...]
==IMAGE_END==
[Camera] === IMAGE DATA OUTPUT COMPLETE ===
```

### 2. Python Script Usage

1. **Run the decoder script:**
   ```bash
   python decode_esp32_image.py
   ```

2. **Copy the complete output:**
   - Copy everything from `==IMAGE_START==` to `==IMAGE_END==` (including these markers)
   - Include all the Base64 data lines

3. **Paste into the script:**
   - Paste the copied data when prompted
   - Type `END` on a new line and press Enter

4. **Result:**
   - Script will decode and save the image as `esp32_capture_[timestamp].jpg`
   - Image will be automatically displayed (if possible)
   - Verification information will be shown

### 3. What You Can Verify

- **Image Quality:** Check if the image is clear and well-focused
- **Flash Effect:** Verify that the flash is illuminating the subject properly
- **Resolution:** Confirm the actual resolution matches expectations
- **Capture Timing:** See how long capture takes
- **JPEG Compression:** Check file size and quality

### 4. Example Output

```
🔧 ESP32-CAM Image Decoder
==================================================
Instructions:
1. Copy the complete image output from your ESP32 terminal
2. Paste it below and press Enter
3. Type 'END' on a new line and press Enter to finish
==================================================

Paste your ESP32 image data here:
[User pastes data here]
END

📄 Format: JPEG
📏 Size: 85432 bytes
📐 Dimensions: 1600x1200
⏰ ESP32 Timestamp: 12345678 ms
📊 Base64 data length: 113909 characters
🔓 Decoding Base64 data...
✅ Decoded 85432 bytes
💾 Image saved as: esp32_capture_1726123456.jpg
🖼️  Image verification:
   - PIL Format: JPEG
   - PIL Size: (1600, 1200)
   - PIL Mode: RGB
✅ Dimensions match metadata
🖼️  Image displayed in default viewer

🎉 Successfully decoded ESP32-CAM image!
📁 File: esp32_capture_1726123456.jpg
```

### 5. Troubleshooting

**If image appears corrupted:**
- Check if all Base64 data was copied
- Ensure no extra characters were added during copy-paste
- Verify the `==IMAGE_START==` and `==IMAGE_END==` markers are present

**If image is too dark:**
- Flash might not be working properly
- Try adjusting camera sensor settings

**If image is blurry:**
- Camera might need focus adjustment
- Check if camera module is properly seated

**If no Base64 data:**
- Ensure ESP32 has enough memory for encoding
- Check if capture actually succeeded

### 6. Requirements

**Python dependencies:**
```bash
pip install Pillow
```

The script uses only standard Python libraries plus Pillow for image handling.
