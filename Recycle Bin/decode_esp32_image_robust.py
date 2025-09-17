#!/usr/bin/env python3
"""
Robust ESP32-CAM Image Decoder
Handles chunked Base64 data and various formatting issues
"""

import base64
import io
import time
import re
from PIL import Image

def fix_base64_padding(b64_string):
    """Fix Base64 padding issues"""
    # Remove any whitespace
    b64_string = re.sub(r'\s+', '', b64_string)
    
    # Add padding if needed
    missing_padding = len(b64_string) % 4
    if missing_padding:
        b64_string += '=' * (4 - missing_padding)
    
    return b64_string

def extract_clean_base64(text):
    """Extract and clean Base64 data from ESP32 output"""
    # Find the Base64 data section
    start_marker = "BASE64_DATA:"
    end_marker = "==IMAGE_END=="
    
    start_idx = text.find(start_marker)
    end_idx = text.find(end_marker)
    
    if start_idx == -1 or end_idx == -1:
        # Try alternative markers
        lines = text.split('\n')
        base64_lines = []
        in_base64_section = False
        
        for line in lines:
            line = line.strip()
            
            # Check for start of Base64 data
            if 'BASE64_DATA' in line or line.startswith('/9j/') or line.startswith('iVBOR'):
                in_base64_section = True
                if not line.startswith('BASE64_DATA'):
                    base64_lines.append(line)
                continue
                
            # Check for end markers
            if '==IMAGE_END==' in line or 'IMAGE DATA OUTPUT COMPLETE' in line:
                in_base64_section = False
                break
                
            # Collect Base64 lines
            if in_base64_section:
                # Skip progress messages and log lines
                if not any(skip in line for skip in ['Progress:', '[Camera]', '[IMG_B64]', 'ERROR:', 'Total bytes']):
                    # Check if line looks like Base64
                    if re.match(r'^[A-Za-z0-9+/=]+$', line) and len(line) > 10:
                        base64_lines.append(line)
        
        return ''.join(base64_lines)
    
    # Extract from markers
    base64_section = text[start_idx + len(start_marker):end_idx]
    
    # Clean the data
    base64_lines = []
    for line in base64_section.split('\n'):
        line = line.strip()
        if line and not any(skip in line for skip in ['Progress:', '[Camera]', '[IMG_B64]', 'Starting transmission']):
            # Remove any non-Base64 characters
            cleaned_line = re.sub(r'[^A-Za-z0-9+/=]', '', line)
            if cleaned_line:
                base64_lines.append(cleaned_line)
    
    return ''.join(base64_lines)

def decode_image_robust():
    """Robust decoder that handles various issues"""
    print("🔧 Robust ESP32-CAM Image Decoder")
    print("=" * 50)
    print("This decoder handles:")
    print("- Base64 padding issues")
    print("- Chunked transmission problems")
    print("- Mixed output formats")
    print("- Progress messages in data")
    print("=" * 50)
    
    # Get input
    print("\nPaste your ESP32 image data here:")
    print("(Type 'END' on a new line when finished)")
    
    input_lines = []
    while True:
        try:
            line = input()
            if line.strip().upper() == 'END':
                break
            input_lines.append(line)
        except EOFError:
            break
        except KeyboardInterrupt:
            print("\n❌ Operation cancelled")
            return
    
    if not input_lines:
        print("❌ No input received")
        return
    
    full_text = '\n'.join(input_lines)
    
    # Extract metadata
    metadata = {}
    
    # Try multiple format patterns
    format_patterns = [
        r'FORMAT:\s*(\w+)',
        r'format[:\s]*(\w+)',
        r'Image format[:\s]*(\w+)'
    ]
    
    for pattern in format_patterns:
        match = re.search(pattern, full_text, re.IGNORECASE)
        if match:
            metadata['format'] = match.group(1).upper()
            break
    
    # Size patterns
    size_patterns = [
        r'SIZE:\s*(\d+)\s*bytes',
        r'size[:\s]*(\d+)',
        r'Total bytes[:\s]*(\d+)'
    ]
    
    for pattern in size_patterns:
        match = re.search(pattern, full_text, re.IGNORECASE)
        if match:
            metadata['size'] = int(match.group(1))
            break
    
    # Dimensions
    dim_match = re.search(r'DIMENSIONS:\s*(\d+)x(\d+)', full_text, re.IGNORECASE)
    if dim_match:
        metadata['width'] = int(dim_match.group(1))
        metadata['height'] = int(dim_match.group(2))
    
    print("\n📊 Extracted metadata:")
    for key, value in metadata.items():
        print(f"   {key}: {value}")
    
    # Extract Base64 data
    print("\n🔍 Extracting Base64 data...")
    base64_data = extract_clean_base64(full_text)
    
    if not base64_data:
        print("❌ No Base64 data found")
        print("\n💡 Debug info:")
        print(f"Input length: {len(full_text)} characters")
        print("Looking for patterns...")
        if 'BASE64_DATA' in full_text:
            print("✅ Found BASE64_DATA marker")
        if '==IMAGE_END==' in full_text:
            print("✅ Found IMAGE_END marker")
        return
    
    print(f"📏 Base64 data length: {len(base64_data)} characters")
    
    # Fix padding
    original_length = len(base64_data)
    base64_data = fix_base64_padding(base64_data)
    
    if len(base64_data) != original_length:
        print(f"🔧 Fixed padding (added {len(base64_data) - original_length} chars)")
    
    # Try to decode
    print("🔓 Attempting to decode...")
    
    try:
        image_bytes = base64.b64decode(base64_data, validate=True)
        print(f"✅ Successfully decoded {len(image_bytes)} bytes")
        
        # Verify size if available
        if 'size' in metadata:
            if len(image_bytes) == metadata['size']:
                print("✅ Size matches metadata")
            else:
                print(f"⚠️  Size mismatch: decoded {len(image_bytes)} vs metadata {metadata['size']}")
        
    except Exception as e:
        print(f"❌ Base64 decoding failed: {e}")
        print("\n🔧 Troubleshooting:")
        print("1. Check if you copied the complete output")
        print("2. Make sure there are no extra characters")
        print("3. Verify the ESP32 completed transmission")
        
        # Try partial decode for debugging
        print(f"\n🔍 Debug info:")
        print(f"   Base64 string starts with: {base64_data[:50]}...")
        print(f"   Base64 string ends with: ...{base64_data[-50:]}")
        
        return
    
    # Save the image
    timestamp = int(time.time())
    format_ext = metadata.get('format', 'JPEG').lower()
    if format_ext == 'jpeg':
        format_ext = 'jpg'
    
    filename = f"esp32_robust_{timestamp}.{format_ext}"
    
    try:
        with open(filename, 'wb') as f:
            f.write(image_bytes)
        print(f"💾 Image saved as: {filename}")
        
        # Verify with PIL
        try:
            with Image.open(filename) as img:
                print(f"\n🖼️  Image verification:")
                print(f"   Format: {img.format}")
                print(f"   Size: {img.size}")
                print(f"   Mode: {img.mode}")
                
                # Check dimensions
                if 'width' in metadata and 'height' in metadata:
                    expected = (metadata['width'], metadata['height'])
                    if img.size == expected:
                        print("✅ Dimensions match metadata")
                    else:
                        print(f"⚠️  Dimension mismatch: {img.size} vs {expected}")
                
                # Try to display
                try:
                    img.show()
                    print("🖼️  Image opened in viewer")
                except:
                    print("ℹ️  Could not auto-open image")
                    
        except Exception as e:
            print(f"⚠️  PIL verification failed: {e}")
            print("   (Image file might still be valid)")
        
        print(f"\n🎉 Image successfully decoded and saved!")
        print(f"📁 File: {filename}")
        
    except Exception as e:
        print(f"❌ Failed to save image: {e}")

def main():
    """Main function"""
    decode_image_robust()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
