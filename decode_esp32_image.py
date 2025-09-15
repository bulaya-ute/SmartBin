#!/usr/bin/env python3
"""
ESP32-CAM Image Decoder
Simple script to decode Base64 image data from ESP32-CAM terminal output
"""

import base64
import io
import time
import re
from PIL import Image

def decode_image_from_input():
    """
    Decode Base64 image data from user input (copy-paste from terminal)
    """
    print("🔧 ESP32-CAM Image Decoder")
    print("=" * 50)
    print("Instructions:")
    print("1. Copy the complete image output from your ESP32 terminal")
    print("2. Paste it below and press Enter")
    print("3. Type 'END' on a new line and press Enter to finish")
    print("=" * 50)
    
    # Collect input lines
    input_lines = []
    print("\nPaste your ESP32 image data here:")
    
    while True:
        try:
            line = input()
            if line.strip().upper() == 'END':
                break
            input_lines.append(line)
        except EOFError:
            break
        except KeyboardInterrupt:
            print("\n❌ Operation cancelled by user")
            return
    
    if not input_lines:
        print("❌ No input data received")
        return
    
    # Parse the input data
    full_text = '\n'.join(input_lines)
    
    # Extract metadata
    metadata = {}
    
    # Find format
    format_match = re.search(r'FORMAT:\s*(\w+)', full_text)
    if format_match:
        metadata['format'] = format_match.group(1)
        print(f"📄 Format: {metadata['format']}")
    
    # Find size
    size_match = re.search(r'SIZE:\s*(\d+)\s*bytes', full_text)
    if size_match:
        metadata['size'] = int(size_match.group(1))
        print(f"📏 Size: {metadata['size']} bytes")
    
    # Find dimensions
    dim_match = re.search(r'DIMENSIONS:\s*(\d+)x(\d+)', full_text)
    if dim_match:
        metadata['width'] = int(dim_match.group(1))
        metadata['height'] = int(dim_match.group(2))
        print(f"📐 Dimensions: {metadata['width']}x{metadata['height']}")
    
    # Find timestamp
    timestamp_match = re.search(r'TIMESTAMP:\s*(\d+)', full_text)
    if timestamp_match:
        metadata['timestamp'] = int(timestamp_match.group(1))
        print(f"⏰ ESP32 Timestamp: {metadata['timestamp']} ms")
    
    # Extract Base64 data
    try:
        # Find the Base64 data section
        start_marker = "BASE64_DATA:"
        end_marker = "==IMAGE_END=="
        
        start_idx = full_text.find(start_marker)
        end_idx = full_text.find(end_marker)
        
        if start_idx == -1:
            print("❌ Could not find BASE64_DATA marker")
            return
        
        if end_idx == -1:
            print("❌ Could not find IMAGE_END marker")
            return
        
        # Extract Base64 portion
        base64_section = full_text[start_idx + len(start_marker):end_idx]
        
        # Clean the Base64 data (remove whitespace, newlines, progress messages)
        base64_data = ""
        for line in base64_section.split('\n'):
            line = line.strip()
            # Skip progress messages and empty lines
            if line and not line.startswith('[Camera]') and not 'Progress:' in line:
                # Remove any non-Base64 characters
                cleaned_line = re.sub(r'[^A-Za-z0-9+/=]', '', line)
                base64_data += cleaned_line
        
        if not base64_data:
            print("❌ No valid Base64 data found")
            return
        
        print(f"📊 Base64 data length: {len(base64_data)} characters")
        
        # Decode Base64 to bytes
        print("🔓 Decoding Base64 data...")
        try:
            image_bytes = base64.b64decode(base64_data)
            print(f"✅ Decoded {len(image_bytes)} bytes")
            
            # Verify size matches metadata
            if 'size' in metadata and len(image_bytes) != metadata['size']:
                print(f"⚠️  Warning: Decoded size ({len(image_bytes)}) doesn't match metadata ({metadata['size']})")
            
        except Exception as e:
            print(f"❌ Base64 decoding failed: {e}")
            return
        
        # Save the image
        timestamp = int(time.time())
        format_ext = metadata.get('format', 'JPEG').lower()
        if format_ext == 'jpeg':
            format_ext = 'jpg'
        
        filename = f"esp32_capture_{timestamp}.{format_ext}"
        
        try:
            with open(filename, 'wb') as f:
                f.write(image_bytes)
            print(f"💾 Image saved as: {filename}")
            
            # Try to open and display image info
            try:
                with Image.open(filename) as img:
                    print(f"🖼️  Image verification:")
                    print(f"   - PIL Format: {img.format}")
                    print(f"   - PIL Size: {img.size}")
                    print(f"   - PIL Mode: {img.mode}")
                    
                    # Check if dimensions match metadata
                    if 'width' in metadata and 'height' in metadata:
                        if img.size != (metadata['width'], metadata['height']):
                            print(f"⚠️  Warning: PIL size {img.size} doesn't match metadata ({metadata['width']}x{metadata['height']})")
                        else:
                            print("✅ Dimensions match metadata")
                    
                    # Display the image (optional)
                    try:
                        img.show()
                        print("🖼️  Image displayed in default viewer")
                    except:
                        print("ℹ️  Could not display image automatically")
                        
            except Exception as e:
                print(f"⚠️  Could not verify image with PIL: {e}")
                print("   (File might still be valid)")
            
            print(f"\n🎉 Successfully decoded ESP32-CAM image!")
            print(f"📁 File: {filename}")
            
        except Exception as e:
            print(f"❌ Failed to save image: {e}")
            return
            
    except Exception as e:
        print(f"❌ Error processing data: {e}")
        return

def main():
    """Main function"""
    decode_image_from_input()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
