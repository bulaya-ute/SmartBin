# 💻 SmartBin Code Snippets Reference

## 📋 Table of Contents
1. [ESP32 Motor Control](#esp32-motor-control)
2. [ESP32 Classification Logic](#esp32-classification-logic)
3. [ESP32 Bluetooth Commands](#esp32-bluetooth-commands)
4. [GUI Classification Processing](#gui-classification-processing)
5. [GUI Binary Mapping](#gui-binary-mapping)
6. [GUI Bin Visualization](#gui-bin-visualization)
7. [Configuration Constants](#configuration-constants)

---

## 🔧 ESP32 Motor Control

### Servo Initialization
```cpp
void initServos() {
  Serial.println("[Servo] Initializing servo motors...");
  
  yield(); // Prevent watchdog timeout
  coinServo.attach(COIN_DISPENSER_PIN);
  Serial.println("[Servo] Coin dispenser attached to GPIO " + String(COIN_DISPENSER_PIN));
  delay(10);
  
  yield(); // Prevent watchdog timeout
  slidingServo.attach(SLIDING_MOTOR_PIN);
  Serial.println("[Servo] Sliding motor attached to GPIO " + String(SLIDING_MOTOR_PIN));
  delay(10);
  
  // Move to home positions
  Serial.println("[Servo] Moving to home positions: Coin=" + String(currentCoinPosition) + "°, Sliding=" + String(currentSlidingPosition) + "°");
  coinServo.write(currentCoinPosition);        // Coin dispenser home: 0°
  slidingServo.write(currentSlidingPosition);  // Sliding motor home: 90°
  
  delay(500);
  Serial.println("[Servo] Initialization complete!");
}
```

### Smooth Motor Movement (5-degree increments)
```cpp
void rotateCoinDispenser(int angle) {
  angle = constrain(angle, 0, 180);
  
  if (abs(angle - currentCoinPosition) == 0) {
    Serial.println("[Servo] CoinDispenser: Already at target position");
    return;
  }
  
  int direction = (angle > currentCoinPosition) ? 1 : -1;
  int currentPos = currentCoinPosition;
  
  while (currentPos != angle) {
    // Move in 5-degree increments
    int step = min(5, abs(angle - currentPos));
    currentPos += direction * step;
    
    coinServo.write(currentPos);
    
    // Proportional delay: 44ms per degree = ~4 seconds for 90°
    int stepDelay = (step < 5) ? 
                   (MOVEMENT_SPEED_MS_PER_DEGREE * step) : 
                   (MOVEMENT_SPEED_MS_PER_DEGREE * 5);
    
    // Watchdog-safe delay
    unsigned long startTime = millis();
    while (millis() - startTime < stepDelay) {
      yield();
      delay(10);
    }
  }
  
  currentCoinPosition = angle;
}
```

---

## 🤖 ESP32 Classification Logic

### Binary Classification Processing
```cpp
// Map 9-class classification to binary for motors
bool isRecyclable = false;
if (detectedClass == "aluminium" || detectedClass == "carton" || 
    detectedClass == "glass" || detectedClass == "paper_and_cardboard" || 
    detectedClass == "plastic") {
  isRecyclable = true;
}

if (isRecyclable) {
  // Recyclable: Dispense coin, then route to recyclable bin
  logMessage("[Sorting] Recyclable material detected (" + detectedClass + ") - dispensing coin and routing to recyclable bin");
  
  // First: Dispense coin
  rotateCoinDispenser(COIN_DISPENSE);  // Move to dispense position (0°)
  delay(1000);
  rotateCoinDispenser(COIN_HOME);      // Return to home (90°)
  delay(500);
  
  // Then: Route to recyclable bin
  rotateSlidingMotor(SLIDING_RECYCLABLE);   // Move to recyclable position (30°)
  delay(3000);  // Hold for 3 seconds to allow waste to fall
  rotateSlidingMotor(SLIDING_HOME);         // Return to home position (90°)
}
else {
  // Non-recyclable: Route to non-recyclable bin (no coin)
  logMessage("[Sorting] Non-recyclable material detected (" + detectedClass + ") - routing to non-recyclable bin");
  rotateSlidingMotor(SLIDING_NON_RECYCLABLE);  // Move to non-recyclable position (150°)
  delay(3000);
  rotateSlidingMotor(SLIDING_HOME);            // Return to home position (90°)
}
```

### Fallback for Unknown Classifications
```cpp
if (detectedClass == "unknown") {
  logMessage("[Error] Classification failed or ambiguous. Routing to non-recyclable.");
  detectedClass = "organic_waste"; // Default to a valid 9-class category
}

// Handle low confidence results
if (!isConfidentResult(result)) {
  logMessage("[Classification] ⚠️ Low confidence result, routing to non-recyclable bin");
  detectedClass = "organic_waste"; // Default to a valid 9-class category
}
```

---

## 📡 ESP32 Bluetooth Commands

### Command Processing
```cpp
// Handle Bluetooth commands (for manual control and testing)
if (SerialBT.available()) {
  String command = SerialBT.readStringUntil('\n');
  command.trim();
  command.toLowerCase();
  
  if (command == "recyclable") {
    SerialBT.println("[Command] Processing recyclable waste manually");
    rotateCoinDispenser(COIN_DISPENSE);       // Dispense coin (0°)
    delay(1000);
    rotateCoinDispenser(COIN_HOME);           // Return to home (90°)
    delay(500);
    rotateSlidingMotor(SLIDING_RECYCLABLE);   // Move to recyclable position (30°)
    delay(3000);
    rotateSlidingMotor(SLIDING_HOME);         // Return to home (90°)
    SerialBT.println("[Command] Recyclable processing complete");
  }
  else if (command == "non-recyclable") {
    SerialBT.println("[Command] Processing non-recyclable waste manually");
    rotateSlidingMotor(SLIDING_NON_RECYCLABLE);  // Move to non-recyclable position (150°)
    delay(3000);
    rotateSlidingMotor(SLIDING_HOME);            // Return to home (90°)
    SerialBT.println("[Command] Non-recyclable processing complete");
  }
  else if (command == "test-servos") {
    SerialBT.println("[Command] Testing servo motors");
    // Test movements and return to home
  }
  else if (command == "status") {
    SerialBT.println("[Status] SmartBin System Status:");
    SerialBT.println("- Laptop Connected: " + String(comm.isLaptopConnected() ? "Yes" : "No"));
    SerialBT.println("- Processing: " + String(isProcessing ? "Yes" : "No"));
    SerialBT.println("- Free Memory: " + String(ESP.getFreeHeap()) + " bytes");
  }
}
```

---

## 🖥️ GUI Classification Processing

### YOLO Backend Integration
```python
def _classify_with_yolo_backend(self, image: Image.Image) -> Dict[str, Any]:
    """Classify image using the YOLO backend script"""
    try:
        import subprocess
        import tempfile
        import os
        
        # Save image to temporary file
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp_file:
            image.save(tmp_file.name, 'JPEG')
            tmp_path = tmp_file.name
        
        try:
            # Call the YOLO backend script
            venv_python = ".venv/bin/python"
            cmd = [
                venv_python, "yolo_classification_backend.py",
                "--model", "runs/smartbin_9class/weights/best.pt",
                "--image", tmp_path,
                "--json"
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                import json
                classification_data = json.loads(result.stdout)
                return classification_data
            else:
                return {"success": False, "error": f"Backend script error: {result.stderr}"}
        
        finally:
            os.unlink(tmp_path)  # Clean up temp file
    
    except Exception as e:
        return {"success": False, "error": f"YOLO backend integration error: {e}"}
```

---

## 🔄 GUI Binary Mapping

### 9-Class to Binary Conversion
```python
# Map 9-class classification to binary for ESP32
recyclable_classes = {
    'aluminium', 'carton', 'glass', 
    'paper_and_cardboard', 'plastic'
}

# Determine if item is recyclable
if classification.lower() in recyclable_classes:
    binary_result = "recyclable"
else:
    binary_result = "non-recyclable"

# Send binary classification result to ESP32
esp32_command = f"{binary_result} {confidence:.2f}"
if self._send_message("CLS01", esp32_command):
    self.gui.message_queue.put({
        'type': 'info',
        'message': f"✅ Sent to ESP32: {esp32_command} (from {classification})",
        'timestamp': datetime.now().strftime("%H:%M:%S")
    })
```

### Bin Count Updates
```python
def _update_bin_count(self, classified_item: str):
    """Update bin count when an item is classified (9-class system)"""
    if classified_item in self.bin_counts:
        self.bin_counts[classified_item] += 1
        
        # Update visual display
        count_label = getattr(self, f"{classified_item}_count_label", None)
        if count_label:
            count_label.configure(text=f"{self.bin_counts[classified_item]}")
        
        # Check if recyclable for coin dispensing
        recyclable_classes = {
            'aluminium', 'carton', 'glass', 
            'paper_and_cardboard', 'plastic'
        }
        
        if classified_item.lower() in recyclable_classes:
            if self.coin_count > 0:
                self.coin_count -= 1
                self.coin_progress.set(self.coin_count / self.coin_capacity)
                self.coin_count_label.configure(text=f"{self.coin_count}/{self.coin_capacity} coins")
                coin_msg = f" | Coin dispensed! Remaining: {self.coin_count}"
            else:
                coin_msg = " | No coins left to dispense!"
        else:
            coin_msg = " | Non-recyclable (no coin)"
```

---

## 📊 GUI Bin Visualization

### 9-Class Bin Display
```python
def _create_bin_visualizations(self):
    """Create the bin and coin visualizations for 9-class system"""
    # Recyclable bin info
    recyclable_info = {
        "aluminium": {"emoji": "🥤", "color": "#C0C0C0"},
        "carton": {"emoji": "📦", "color": "#8D6E63"},
        "glass": {"emoji": "🍾", "color": "#4CAF50"}, 
        "paper_and_cardboard": {"emoji": "📄", "color": "#FF9800"},
        "plastic": {"emoji": "🥤", "color": "#2196F3"}
    }
    
    # Non-recyclable bin info
    non_recyclable_info = {
        "ewaste": {"emoji": "💻", "color": "#9C27B0"},
        "organic_waste": {"emoji": "🍎", "color": "#795548"},
        "textile": {"emoji": "👕", "color": "#E91E63"},
        "wood": {"emoji": "🪵", "color": "#6D4C41"}
    }
    
    # Create recyclable section
    for i, (waste_type, info) in enumerate(recyclable_info.items()):
        item_frame = ctk.CTkFrame(recyclable_grid, width=80, height=60)
        item_frame.grid(row=row, column=col, padx=2, pady=2, sticky="ew")
        
        # Item emoji and label
        item_label = ctk.CTkLabel(
            item_frame,
            text=f"{info['emoji']}\n{waste_type.replace('_', ' ').title()[:8]}",
            font=ctk.CTkFont(size=10, weight="bold")
        )
        item_label.pack(pady=2)
        
        # Count label
        count_label = ctk.CTkLabel(
            item_frame,
            text=f"{self.bin_counts[waste_type]}",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=info['color']
        )
        count_label.pack(pady=2)
        
        # Store reference for updates
        setattr(self, f"{waste_type}_count_label", count_label)
```

### Classification Results Display
```python
def _update_classification_display(self, result: str, confidence: float, all_classes: Dict[str, float], timestamp: str):
    """Update the classification results display"""
    # Clear existing widgets
    for widget in self.classification_results.winfo_children():
        widget.destroy()
    
    # Sort classes by confidence
    sorted_classes = sorted(all_classes.items(), key=lambda x: x[1], reverse=True)
    
    # Create display for each class
    for i, (class_name, conf) in enumerate(sorted_classes):
        class_frame = ctk.CTkFrame(self.classification_results)
        class_frame.pack(fill="x", padx=5, pady=2)
        
        # Emoji for ranking
        emoji = ["🥇", "🥈", "🥉", "📝"][i] if i < 4 else "📝"
        
        # Class name and confidence
        class_label = ctk.CTkLabel(
            class_frame,
            text=f"{emoji} {class_name}: {conf*100:.1f}%",
            font=ctk.CTkFont(size=14, weight="bold" if i == 0 else "normal")
        )
        class_label.pack(side="left", padx=10, pady=5)
        
        # Progress bar for confidence
        progress = ctk.CTkProgressBar(class_frame, width=150, height=10)
        progress.pack(side="right", padx=10, pady=5)
        progress.set(conf)
```

---

## ⚙️ Configuration Constants

### ESP32 Motor Constants
```cpp
// Pin assignments
int COIN_DISPENSER_PIN = 13;  // GPIO 13
int SLIDING_MOTOR_PIN  = 4;   // GPIO 4

// Motor positions
const int SLIDING_HOME = 90;           // Home position (center)
const int SLIDING_RECYCLABLE = 30;     // Recyclable bin position
const int SLIDING_NON_RECYCLABLE = 150; // Non-recyclable bin position
const int COIN_HOME = 90;              // Coin dispenser home position
const int COIN_DISPENSE = 0;           // Coin dispense position

// Movement speed (44ms per degree = ~4 seconds for 90°)
const int MOVEMENT_SPEED_MS_PER_DEGREE = 44;

// Current position tracking
int currentCoinPosition = 0;      // Home position: 0 degrees
int currentSlidingPosition = 90;  // Home position: 90 degrees
```

### GUI Configuration
```python
# 9-class waste categories
self.bin_counts = {
    # Recyclable materials
    "aluminium": 0,
    "carton": 0,
    "glass": 0,
    "paper_and_cardboard": 0,
    "plastic": 0,
    # Non-recyclable materials  
    "ewaste": 0,
    "organic_waste": 0,
    "textile": 0,
    "wood": 0
}

# Binary classification mapping
recyclable_classes = {
    'aluminium', 'carton', 'glass', 
    'paper_and_cardboard', 'plastic'
}

# Model path
model_path = "runs/smartbin_9class/weights/best.pt"

# Connection settings
esp32_mac = "EC:E3:34:15:F2:62"
rfcomm_device = "/dev/rfcomm0"
baudrate = 115200
```

### Communication Protocol
```python
# Protocol commands
commands = {
    "status": "System health check",
    "test-servos": "Test motor movements", 
    "recyclable": "Manual recyclable processing",
    "non-recyclable": "Manual non-recyclable processing"
}

# Message types
message_types = {
    "sent": {"color": "#4CAF50", "prefix": "➡️ SENT"},
    "received": {"color": "#2196F3", "prefix": "⬅️ RECV"},
    "error": {"color": "#F44336", "prefix": "❌ ERROR"},
    "info": {"color": "#FFC107", "prefix": "ℹ️ INFO"}
}
```

---

## 🔧 Quick Reference Commands

### ESP32 Bluetooth Commands
```bash
status          # System health check
test-servos     # Test motor movements
recyclable      # Manual recyclable processing
non-recyclable  # Manual non-recyclable processing
```

### GUI Startup
```bash
cd /home/bulaya/StudioProjects/SmartBin
source .venv/bin/activate
python smartbin_gui.py
```

### Classification Flow
```
Item Detection → Image Capture → 9-Class YOLO → GUI Display → Binary Mapping → ESP32 Action
```

---

*This reference contains the core code snippets for SmartBin operation and maintenance.*
