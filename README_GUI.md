# 🤖 SmartBin Modern GUI Application

A sophisticated CustomTkinter-based interface for the SmartBin PySerial Bluetooth protocol with real-time communication monitoring, image preview, and classification results visualization.

## 🚀 Quick Start

### 1. Install Dependencies
```bash
# Activate virtual environment
source .venv/bin/activate

# Install required packages (already done)
pip install customtkinter pillow pyserial

# Install system tkinter (if needed)
sudo apt install python3-tk
```

### 2. Run the Application
```bash
python smartbin_gui.py
```

## 🎯 Features

### 🖼️ **Image Display**
- Real-time preview of captured images from ESP32-CAM
- Automatic image resizing with aspect ratio preservation
- Image metadata display (dimensions, format, timestamp)

### 📊 **Classification Results**
- **Multi-class confidence visualization** with progress bars
- **Ranking system** with emojis (🥇🥈🥉📝)
- **Real-time updates** as classifications are processed
- **Detailed confidence percentages** for all waste categories

### 💬 **Communication Log**
- **Color-coded messages**: Sent (green), Received (blue), Errors (red), Info (amber)
- **Timestamps** for all communications
- **Auto-scroll** option for latest messages
- **Scrollable history** with search capability

### 🔧 **Control Interface**
- **Connection management** with visual status indicators
- **Configurable ESP32 MAC address**
- **Manual command sending** with protocol validation
- **Quick command buttons** for common operations

## 🎨 Modern UI Design

- **Dark/Light theme** automatic detection
- **Responsive layout** that adapts to window size
- **Smooth animations** and hover effects
- **Professional appearance** with CustomTkinter styling
- **Intuitive controls** with clear visual feedback

## 📡 Protocol Support

Full support for the SmartBin 5-character Bluetooth protocol:
- **Connection management** (RTC00, RTC01, RTC02)
- **Image transmission** (PA000, PA001-PA999, PX001-PX999)
- **Classification results** (CLS01)
- **Error handling** (ERR01-ERR99)

## 🔧 Usage

1. **Start the application**: `python smartbin_gui.py`
2. **Enter ESP32 MAC address**: Default is `EC:E3:34:15:F2:62`
3. **Click Connect**: Establishes Bluetooth connection
4. **Monitor communications**: View real-time message exchange
5. **See image previews**: Captured images appear automatically
6. **View classifications**: All confidence scores displayed with rankings

## 📋 Quick Commands

- **🤝 Connect**: Send `RTC00` to initiate connection
- **📷 Request Image**: Send `IMG01` to request image capture
- **🔄 Status**: Send `STA01` to request device status

## 🛠️ Technical Details

- **Framework**: CustomTkinter with modern design
- **Threading**: Non-blocking communication with ESP32
- **Protocol**: PySerial-based Bluetooth communication
- **Image Processing**: PIL for image display and manipulation
- **Message Queue**: Thread-safe communication between protocol and GUI

## 📚 Documentation

For complete documentation, architecture details, and development guide, see:
- **[SmartBin_GUI_Documentation.md](SmartBin_GUI_Documentation.md)** - Complete technical documentation

## 🔧 Dependencies

- `customtkinter>=5.2.0` - Modern UI framework
- `pillow>=10.0.0` - Image processing
- `pyserial>=3.5` - Serial communication
- `python3-tk` - System tkinter package

## 🎯 Key Benefits

✅ **Real-time monitoring** of all ESP32 communications  
✅ **Visual classification results** with confidence levels  
✅ **Modern, professional interface** with dark/light themes  
✅ **Non-blocking operation** with multithreading  
✅ **Complete protocol support** for SmartBin system  
✅ **Easy debugging** with comprehensive message logging  
✅ **Image visualization** for captured waste items  
✅ **Manual control** for testing and development  

## 🏗️ Architecture

```
SmartBin GUI Application
├── Modern CustomTkinter Interface
│   ├── Image Preview Panel
│   ├── Classification Results Panel
│   ├── Communication Log Panel
│   └── Control Panel
├── Protocol Integration
│   ├── Extended PySerial Protocol
│   ├── Thread-safe Message Queue
│   └── Real-time Event Processing
└── Advanced Features
    ├── Multi-class Confidence Display
    ├── Message Color Coding
    ├── Auto-scroll Logging
    └── Connection Management
```

Perfect for development, testing, and monitoring your SmartBin waste classification system!

---

*Built with ❤️ using CustomTkinter and Python*
