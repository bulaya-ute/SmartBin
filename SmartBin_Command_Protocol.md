# SmartBin ESP32 Command Protocol Specification

## 🎯 **Core Design Philosophy**
- **Linux-style syntax**: Familiar command structure with flags and options
- **Bidirectional communication**: Commands from GUI to ESP32, responses back
- **State persistence**: ESP32 maintains its own state, GUI can override
- **Error handling**: Clear success/error responses with descriptive messages

---

## 📋 **Proposed Command Categories**

### 🔧 **Hardware Control Commands**

#### **Lid Operations**
```bash
lid open                    # Open the main lid
lid close                   # Close the main lid
lid status                  # Get current lid position (open/closed/moving)
lid auto                    # Enable automatic lid control
lid manual                  # Disable automatic lid control
```

#### **Coin Dispenser**
```bash
coin dispense               # Dispense one coin
coin dispense --count 3     # Dispense specific number of coins
coin status                 # Get remaining coin count and mechanism status
coin refill --count 50      # Set coin count (manual override)
coin test                   # Test dispenser mechanism without dispensing
```

#### **Camera & Flash Control**
```bash
capture                     # Take photo with current settings
capture --flash             # Take photo with flash enabled
capture --no-flash          # Take photo with flash disabled
capture --preview           # Take low-res preview image
flash on                    # Turn flash on continuously
flash off                   # Turn flash off
flash test --duration 100   # Test flash for specified ms
```

#### **Bin Compartments**
```bash
bin open --id 0             # Open specific bin compartment
bin close --id 1            # Close specific bin compartment  
bin status                  # Get status of all bin compartments
bin reset --id 2            # Reset bin compartment sensors
```

---

### ⚙️ **Configuration Commands**

#### **Flash Settings**
```bash
config flash precap --duration 50    # Flash duration before capture (ms)
config flash postcap --duration 40   # Flash duration after capture (ms)
config flash intensity --level 80    # Flash intensity (0-100%)
config flash save                     # Save flash settings to EEPROM
```

#### **Sensor Configuration**
```bash
config sensor ultrasonic --threshold 10     # Distance threshold for detection (cm)
config sensor weight --calibration 1.25     # Weight sensor calibration factor
config sensor weight --zero                 # Zero/tare weight sensors
config sensor save                          # Save sensor config to EEPROM
```

#### **Timing Settings**
```bash
config timing capture --delay 500           # Delay before auto-capture (ms)
config timing lid --speed 50                # Lid movement speed (0-100%)
config timing timeout --duration 30         # Operation timeout (seconds)
config timing save                          # Save timing config to EEPROM
```

#### **Network Configuration**
```bash
config bt --name "SmartBin_001"            # Set Bluetooth device name
config bt --pin 1234                       # Set Bluetooth pairing PIN
config wifi --ssid "NetworkName"           # Set WiFi network (future use)
config wifi --password "password"          # Set WiFi password
config save                                # Save all configuration
```

---

### 📊 **Data & Status Commands**

#### **Bin Status & Quantities**
```bash
bin get --id 0 --quantity              # Get quantity in specific bin
bin get --all --quantity               # Get quantities in all bins
bin set --id 1 --quantity 5            # Manually set bin quantity
bin get --id 2 --weight                # Get weight of bin contents
bin get --all --status                 # Get comprehensive bin status
bin clear --id 3                       # Reset bin to empty
bin clear --all                        # Reset all bins to empty
```

#### **System Information**
```bash
status system                          # Get comprehensive system status
status uptime                          # Get system uptime
status battery                         # Get battery level (if applicable)
status memory                          # Get memory usage stats
status sensors                         # Get all sensor readings
status network                         # Get Bluetooth/WiFi status
```

#### **Statistics & History**
```bash
stats daily                            # Get today's sorting statistics
stats weekly                           # Get weekly statistics
stats total                            # Get lifetime statistics
stats reset                            # Reset statistics counters
log recent --lines 20                  # Get recent activity log
log errors                             # Get error log entries
log clear                              # Clear logs
```

---

### 🔄 **System Control Commands**

#### **Connection Management**
```bash
bt disconnect                          # Disconnect Bluetooth
bt reconnect                           # Reconnect Bluetooth
bt scan                                # Scan for nearby devices
bt status                              # Get Bluetooth connection info
```

#### **System Operations**
```bash
system restart                         # Restart ESP32
system shutdown                        # Enter deep sleep mode
system factory-reset                   # Reset to factory defaults
system backup                          # Backup configuration
system restore                         # Restore from backup
system test --all                      # Run comprehensive system test
```

#### **Diagnostic Commands**
```bash
test motor --id servo1                 # Test specific motor
test sensor --id ultrasonic            # Test specific sensor
test led --pattern blink               # Test LED with pattern
test speaker --tone 440 --duration 1000 # Test speaker
diag memory                            # Memory diagnostic
diag sensors                           # Sensor diagnostic
```

---

## 🌟 **Advanced Command Features**

### **Command Chaining**
```bash
lid open && capture --flash && lid close    # Chain multiple commands
```

### **Conditional Execution**
```bash
bin status --id 0 | if full then coin dispense    # Conditional logic
```

### **Scheduled Commands**
```bash
schedule daily 00:00 "stats reset"          # Daily scheduled task
schedule interval 3600 "status system"      # Hourly status check
```

### **Batch Operations**
```bash
batch bin clear --all && config timing save && system restart
```

---

## 📝 **Command Response Format**

### **Success Response**
```json
{
  "status": "success",
  "command": "bin get --id 0 --quantity",
  "data": {
    "bin_id": 0,
    "quantity": 7,
    "weight": 150.5,
    "last_updated": "2025-09-18T14:30:00Z"
  },
  "timestamp": "2025-09-18T14:30:15Z"
}
```

### **Error Response**
```json
{
  "status": "error",
  "command": "coin dispense --count 10",
  "error": {
    "code": "INSUFFICIENT_COINS",
    "message": "Only 3 coins remaining, cannot dispense 10",
    "details": "Current coin count: 3"
  },
  "timestamp": "2025-09-18T14:30:15Z"
}
```

---

## 🛠️ **Implementation Recommendations**

### **Command Parser Structure**
1. **Tokenization**: Split command into verb, noun, flags, and arguments
2. **Validation**: Check syntax and parameter ranges
3. **Execution**: Route to appropriate handler function
4. **Response**: Format and send JSON response

### **State Management**
1. **Persistent Storage**: Use EEPROM for configuration
2. **Runtime State**: RAM for current operational data
3. **Backup System**: Periodic state backups
4. **Recovery**: Graceful recovery from power loss

### **Security Considerations**
1. **Command Authentication**: Optional PIN protection for critical commands
2. **Rate Limiting**: Prevent command flooding
3. **Access Levels**: Different permission levels for different commands
4. **Audit Log**: Track all executed commands

---

## 🎯 **Priority Implementation Order**

### **Phase 1: Core Commands**
1. `capture`, `lid open/close`, `bin status`
2. `coin dispense`, `bt disconnect`
3. Basic `config` commands for flash and timing

### **Phase 2: Enhanced Control**
1. All `bin` quantity and weight commands
2. Complete `config` system with persistence
3. `status` and `stats` commands

### **Phase 3: Advanced Features**
1. Diagnostic and test commands
2. Scheduling and batch operations
3. Advanced network features

---

## 💡 **Additional Useful Commands**

### **Maintenance Commands**
```bash
clean cycle                             # Run cleaning cycle for sensors
calibrate sensors                       # Auto-calibrate all sensors
update firmware --file path/to/fw.bin  # Update firmware
backup export --format json            # Export configuration
```

### **User Experience Commands**
```bash
led pattern --name "rainbow"            # Fun LED patterns
sound play --tone success               # Audio feedback
demo mode --duration 300                # Demo mode for presentations
tutorial start                          # Interactive tutorial mode
```

### **Developer Commands**
```bash
debug enable                            # Enable debug output
debug memory                            # Show memory allocation
debug timing                            # Show timing measurements
profile start                          # Start performance profiling
```

---

This command structure provides:
- ✅ **Familiar syntax** like Linux commands
- ✅ **Comprehensive control** over all hardware
- ✅ **Flexible configuration** with persistence
- ✅ **Rich data access** for monitoring
- ✅ **Professional error handling**
- ✅ **Extensible design** for future features

The ESP32 can maintain its own state while allowing GUI override, and the JSON response format ensures reliable communication parsing.
