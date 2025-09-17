# SmartBin Modern GUI Application

## Overview

The SmartBin Modern GUI Application is a sophisticated CustomTkinter-based interface for monitoring and controlling the SmartBin PySerial Bluetooth protocol. It provides real-time visualization of communication, image preview, classification results with confidence scores, and manual command sending capabilities.

## Features

### 🖼️ Image Display
- **Real-time Image Preview**: Displays captured images from ESP32-CAM as they're received
- **Automatic Resizing**: Images are resized to fit the display area while maintaining aspect ratio
- **Image Metadata**: Shows image dimensions, format, and capture timestamp
- **Image Storage**: Keeps the original full-resolution image in memory

### 📊 Classification Results
- **Multi-class Confidence Display**: Shows confidence percentages for all waste categories
- **Visual Progress Bars**: Graphical representation of confidence levels
- **Ranking System**: Uses emojis (🥇🥈🥉📝) to show class rankings
- **Real-time Updates**: Classification results update immediately when received

### 💬 Communication Log
- **Color-coded Messages**: Different colors for sent, received, error, and info messages
- **Timestamps**: All messages include precise timestamps
- **Auto-scroll**: Optional automatic scrolling to latest messages
- **Message Filtering**: Clear distinction between protocol and debug messages
- **Scrollable History**: Full message history with scrollbar support

### 🔧 Control Interface
- **Connection Management**: Connect/disconnect to ESP32 with visual status indicators
- **MAC Address Input**: Configurable ESP32 MAC address
- **Manual Commands**: Send custom protocol commands
- **Quick Commands**: Pre-defined buttons for common operations
- **Real-time Status**: Connection status with colored indicators

## Technical Architecture

### 🏗️ Application Structure

```
SmartBinGUI (Main Application)
├── GUI Components (CustomTkinter)
│   ├── Image Display Frame
│   ├── Classification Results Frame
│   ├── Message Log Frame
│   └── Control Panel Frame
├── Protocol Integration
│   ├── GUIProtocol (Extended SmartBinPySerialProtocol)
│   ├── Message Queue (Thread-safe communication)
│   └── Threading Management
└── Event Handlers
    ├── GUI Updates
    ├── User Interactions
    └── Protocol Messages
```

### 🔄 Threading Model

1. **Main Thread**: GUI updates and user interactions
2. **Protocol Thread**: PySerial communication and protocol handling
3. **Message Queue**: Thread-safe communication between protocol and GUI

### 📡 Protocol Integration

The GUI extends the existing `SmartBinPySerialProtocol` class with GUI-specific functionality:

- **Message Interception**: All sent/received messages are captured and displayed
- **Image Processing**: Complete images are reconstructed and displayed
- **Classification Handling**: Results are parsed and visualized
- **Error Management**: Protocol errors are displayed in the GUI

## Requirements

### Software Dependencies

```python
# Core Dependencies
customtkinter>=5.2.0    # Modern UI framework
pillow>=10.0.0          # Image processing
pyserial>=3.5           # Serial communication
darkdetect>=0.8.0       # System theme detection (auto-installed with customtkinter)

# Standard Library (included with Python)
tkinter                 # Base GUI framework
threading               # Multi-threading support
queue                   # Thread-safe communication
json                    # Data serialization
datetime                # Timestamp handling
base64                  # Image data encoding
io                      # Byte stream handling
subprocess              # System command execution
```

### System Requirements

- **Operating System**: Linux (tested on Ubuntu), Windows, macOS
- **Python Version**: 3.8+ (recommended 3.10+)
- **Bluetooth**: System Bluetooth support with rfcomm capability
- **Memory**: Minimum 4GB RAM (for image processing)
- **Display**: Minimum 1024x768 resolution

### Hardware Requirements

- **ESP32-CAM**: Target device for communication
- **Bluetooth Adapter**: If not built into system
- **USB Cable**: For initial ESP32 programming (optional during GUI operation)

## Installation

### 1. Clone Repository

```bash
git clone <repository-url>
cd SmartBin
```

### 2. Create Virtual Environment

```bash
python3 -m venv .venv
source .venv/bin/activate  # Linux/macOS
# or
.venv\Scripts\activate     # Windows
```

### 3. Install Dependencies

```bash
pip install customtkinter pillow pyserial
```

### 4. System Setup (Linux)

```bash
# Install Bluetooth tools
sudo apt update
sudo apt install bluetooth bluez rfcomm

# Add user to dialout group (for serial access)
sudo usermod -a -G dialout $USER

# Logout and login again for group changes to take effect
```

## Usage

### 🚀 Starting the Application

```bash
# Activate virtual environment
source .venv/bin/activate

# Run the GUI application
python smartbin_gui.py
```

### 🔧 Configuration

1. **ESP32 MAC Address**: Enter your ESP32's Bluetooth MAC address in the input field
2. **Theme**: The application automatically detects your system theme (dark/light)
3. **Auto-scroll**: Toggle automatic scrolling in the message log

### 📱 Connecting to ESP32

1. Ensure ESP32 is powered on and Bluetooth is enabled
2. Enter the correct MAC address in the GUI
3. Click "🔗 Connect"
4. Wait for the connection status to show "🟢 Connected"
5. The ESP32 should appear in the message log

### 💬 Sending Commands

**Manual Commands:**
- Type command in the "Send Command" field
- Format: `CODE CONTENT` (e.g., `RTC00` or `IMG01 request`)
- Press Enter or click "📤 Send"

**Quick Commands:**
- **🤝 Connect**: Sends `RTC00` (initiate connection)
- **📷 Request Image**: Sends `IMG01` (request image capture)
- **🔄 Status**: Sends `STA01` (request status)

### 🖼️ Image Viewing

- Images automatically appear in the preview area when received
- Original aspect ratio is maintained
- Click on the image area to see full details
- Image metadata shows dimensions, format, and timestamp

### 📊 Classification Analysis

- Results appear automatically after image processing
- All classes are shown with confidence percentages
- Progress bars provide visual representation
- Classes are ranked from highest to lowest confidence

## Configuration Files

### Environment Variables

Create a `.env` file for default settings:

```bash
# ESP32 Configuration
ESP32_MAC_ADDRESS=EC:E3:34:15:F2:62
RFCOMM_DEVICE=/dev/rfcomm0
BAUDRATE=115200

# GUI Configuration
THEME=dark
AUTO_SCROLL=true
LOG_LEVEL=info
```

### GUI Themes

The application supports CustomTkinter's built-in themes:

```python
# Available appearance modes
ctk.set_appearance_mode("dark")    # Dark theme
ctk.set_appearance_mode("light")   # Light theme
ctk.set_appearance_mode("system")  # Follow system theme

# Available color themes
ctk.set_default_color_theme("blue")      # Blue accents
ctk.set_default_color_theme("green")     # Green accents
ctk.set_default_color_theme("dark-blue") # Dark blue accents
```

## Protocol Specification

### 📋 Message Format

All messages follow the 5-character protocol format:

```
CODE CONTENT
```

Where:
- `CODE`: 5-character command code
- `CONTENT`: Optional message content

### 🔄 Communication Flow

```
1. GUI → ESP32: RTC00 (Connection request)
2. ESP32 → GUI: RTC01 Laptop ready (Connection acknowledgment)
3. GUI → ESP32: RTC02 (Connection confirmed)
4. ESP32 → GUI: PA000 type:image,size:12345,parts:5 (Image metadata)
5. ESP32 → GUI: PA001 <base64_chunk_1> (Image part 1)
6. ESP32 → GUI: PA002 <base64_chunk_2> (Image part 2)
   ...
7. ESP32 → GUI: PX005 <base64_chunk_5> (Final image part)
8. GUI → ESP32: CLS01 plastic 0.89 (Classification result)
```

### 📡 Protocol Messages

| Code | Direction | Description | Content Format |
|------|-----------|-------------|----------------|
| RTC00 | GUI→ESP32 | Connection request | - |
| RTC01 | ESP32→GUI | Connection ready | "Laptop ready" |
| RTC02 | ESP32→GUI | Connection confirmed | - |
| PA000 | ESP32→GUI | Image metadata | "type:image,size:X,parts:N" |
| PA001-PA999 | ESP32→GUI | Image part | Base64 image chunk |
| PX001-PX999 | ESP32→GUI | Final image part | Base64 image chunk |
| CLS01 | GUI→ESP32 | Classification result | "class confidence" |
| ERR01-ERR99 | Either | Error message | Error description |

## Development

### 🔧 Extending the Application

#### Adding New Protocol Messages

1. **Extend the GUIProtocol class**:
```python
def _handle_protocol_message(self, code: str, content: str):
    if code == "NEW01":
        # Handle new message type
        self.gui.message_queue.put({
            'type': 'custom',
            'code': code,
            'content': content,
            'timestamp': datetime.now().strftime("%H:%M:%S")
        })
    
    super()._handle_protocol_message(code, content)
```

2. **Add GUI handler**:
```python
def _handle_gui_message(self, data: Dict[str, Any]):
    if data['type'] == 'custom':
        # Handle custom message type
        self._handle_custom_message(data)
    
    # ... existing handlers
```

#### Adding New GUI Components

1. **Create component in `_setup_gui()`**:
```python
def _create_custom_section(self):
    self.custom_frame = ctk.CTkFrame(self.root)
    self.custom_frame.grid(row=3, column=0, columnspan=2, sticky="ew")
    # Add widgets...
```

2. **Add update methods**:
```python
def _update_custom_display(self, data):
    # Update custom component with new data
    pass
```

#### Customizing Appearance

1. **Change color theme**:
```python
ctk.set_default_color_theme("green")  # or "dark-blue"
```

2. **Custom colors**:
```python
# In widget creation
widget = ctk.CTkButton(
    parent,
    fg_color="#FF5722",    # Custom background color
    text_color="#FFFFFF",  # Custom text color
    hover_color="#E64A19"  # Custom hover color
)
```

### 🧪 Testing

#### Unit Testing

```bash
# Run unit tests
python -m pytest tests/

# Run with coverage
python -m pytest --cov=smartbin_gui tests/
```

#### Integration Testing

```bash
# Test with mock ESP32
python tests/test_integration.py

# Test GUI components
python tests/test_gui.py
```

### 🐛 Debugging

#### Enable Debug Logging

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# In smartbin_gui.py
DEBUG = True
```

#### Common Issues

1. **Connection Failed**:
   - Check ESP32 MAC address
   - Verify Bluetooth pairing
   - Ensure rfcomm tools are installed

2. **Image Not Displaying**:
   - Check PIL installation
   - Verify image format support
   - Check memory availability

3. **GUI Freezing**:
   - Ensure protocol runs in separate thread
   - Check for blocking operations in main thread
   - Verify message queue processing

## Performance Optimization

### 🚀 Memory Management

- **Image Caching**: Large images are automatically resized for display
- **Message Limiting**: Log messages are limited to prevent memory overflow
- **Garbage Collection**: Unused image data is automatically cleaned up

### ⚡ Performance Tips

1. **Reduce Log Verbosity**: Disable debug messages for better performance
2. **Image Size Limits**: Consider resizing images on ESP32 before transmission
3. **Message Batching**: Group multiple small messages when possible
4. **Thread Optimization**: Avoid blocking operations in the main GUI thread

## Security Considerations

### 🔒 Bluetooth Security

- **Pairing**: Ensure proper Bluetooth pairing before connection
- **MAC Address Validation**: Verify ESP32 MAC address before connecting
- **Connection Timeout**: Implement timeouts to prevent hanging connections

### 🛡️ Data Security

- **Input Validation**: All user inputs are validated before processing
- **Error Handling**: Comprehensive error handling prevents crashes
- **Memory Safety**: Proper cleanup prevents memory leaks

## Troubleshooting

### Common Problems and Solutions

#### 1. "Failed to bind RFCOMM"

**Problem**: Cannot establish Bluetooth connection
**Solution**:
```bash
# Check Bluetooth status
sudo systemctl status bluetooth

# Restart Bluetooth service
sudo systemctl restart bluetooth

# Check paired devices
bluetoothctl devices

# Pair ESP32 if needed
bluetoothctl pair EC:E3:34:15:F2:62
```

#### 2. "Permission denied: /dev/rfcomm0"

**Problem**: User lacks permission to access serial device
**Solution**:
```bash
# Add user to dialout group
sudo usermod -a -G dialout $USER

# Logout and login again
# Or change permissions temporarily
sudo chmod 666 /dev/rfcomm0
```

#### 3. GUI Not Responding

**Problem**: GUI freezes during operation
**Solution**:
- Check that protocol runs in separate thread
- Ensure message queue is being processed
- Restart application and check console for errors

#### 4. Images Not Displaying

**Problem**: Images received but not shown
**Solution**:
```bash
# Check PIL installation
pip install --upgrade pillow

# Check image format support
python -c "from PIL import Image; print(Image.EXTENSION)"

# Verify image data integrity in logs
```

## Future Enhancements

### 🔮 Planned Features

1. **Data Logging**: Save communication logs to files
2. **Image Gallery**: Browse previously captured images
3. **Statistics Dashboard**: Show connection and classification statistics
4. **Configuration Manager**: GUI-based settings management
5. **Plugin System**: Support for custom extensions
6. **Multiple Device Support**: Connect to multiple ESP32 devices
7. **Real-time Graphs**: Plot classification confidence over time
8. **Export Functions**: Export images and data in various formats

### 🎨 UI/UX Improvements

1. **Customizable Layout**: Resizable and movable panels
2. **Keyboard Shortcuts**: Hotkeys for common operations
3. **Notification System**: Toast notifications for events
4. **Fullscreen Image Viewer**: Detailed image inspection
5. **Theme Editor**: Custom color scheme creation
6. **Accessibility**: Screen reader support and high contrast modes

## License

This project is licensed under the MIT License. See LICENSE file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## Support

For issues and questions:
- Create an issue on the GitHub repository
- Check the troubleshooting section above
- Review the protocol specification for communication issues

## Changelog

### Version 1.0.0 (Initial Release)
- Modern CustomTkinter-based GUI
- Real-time Bluetooth communication
- Image preview and classification display
- Multi-threaded architecture
- Comprehensive message logging
- Manual command sending
- Connection management
- Error handling and recovery

---

*Built with ❤️ using CustomTkinter and Python*
