# 👨‍💼 SmartBin Administrator Manual

## 🚀 System Startup (5 minutes)

### Step 1: Power On ESP32
- Connect power to ESP32-CAM
- Wait for blue LED flash (boot complete)
- ESP32 initializes: Camera, servos, Bluetooth ("SmartBin_ESP32")

### Step 2: Start GUI Application
```bash
cd /home/bulaya/StudioProjects/SmartBin
source .venv/bin/activate
python smartbin_gui.py
```

### Step 3: Connect to System
1. **Enter administrator password** when prompted
2. **Verify ESP32 MAC**: `EC:E3:34:15:F2:62` (default)
3. **Click "🔗 Connect"** button
4. **Wait for "🟢 Connected"** status

### Step 4: System Check
- Send command: `test-servos` (motors should move and return)
- Send command: `status` (check system health)
- **Ready!** System is operational for users

---

## 🖥️ GUI Interface

### Main Sections:
- **Image Preview** (left): Shows captured waste images
- **Classification Results** (center): 9-class AI analysis with confidence scores
- **Bin Status** (right): Real-time counts for recyclable/non-recyclable items
- **Message Log** (middle): Communication between laptop and ESP32
- **Controls** (bottom): Connection status and manual commands

### Key Commands:
| Command | Purpose |
|---------|---------|
| `status` | System health check |
| `test-servos` | Test motor movement |
| `recyclable` | Manual recyclable processing |
| `non-recyclable` | Manual non-recyclable processing |

---

## 📊 Daily Monitoring

### Check These Indicators:
- **Connection**: Should show "🟢 Connected"
- **Classification Confidence**: Target >85%
- **Coin Level**: Refill when <3 coins remaining
- **Bin Levels**: Empty when reaching capacity
- **Error Messages**: Address any red error messages

### Maintenance Tasks:
- **Morning**: Check coin dispenser, empty bins if needed
- **Throughout day**: Monitor connection stability
- **Evening**: Review classification accuracy, check for errors

---

## 🔧 Troubleshooting

| Problem | Quick Fix |
|---------|-----------|
| "🔴 Connection Failed" | Check ESP32 power, verify MAC address, try reconnect |
| Low classification confidence | Clean camera lens, ensure good lighting |
| Servos not responding | Send `test-servos`, check power connections |
| Coin dispenser empty | Refill coin dispenser, test with `recyclable` |
| GUI freezing | Close and restart application |

---

## 🛑 System Shutdown

### End of Day:
1. **Ensure no processing** - Wait for any active sorting to complete
2. **Disconnect**: Click "🔌 Disconnect" in GUI
3. **Close GUI**: Close application window
4. **Power off ESP32**: Unplug power safely
5. **Secure coins**: Store remaining coins safely

---

## 📋 Quick Reference

### Classification Categories:
**Recyclable (Coin Reward):** Aluminium, Carton, Glass, Paper & Cardboard, Plastic  
**Non-Recyclable (No Coin):** E-Waste, Organic Waste, Textile, Wood

### Default Settings:
- **ESP32 MAC**: `EC:E3:34:15:F2:62`
- **Model Path**: `runs/smartbin_9class/weights/best.pt`
- **Coin Capacity**: 10 coins
- **Motor Speed**: 44ms/degree (~4 seconds for 90°)

### Emergency: Force shutdown if unresponsive
1. Ctrl+C to close GUI
2. Unplug ESP32 immediately
3. Check for mechanical obstructions
4. Review logs before restarting

---

*Quick setup: Power → GUI → Connect → Test → Ready!*
*For detailed troubleshooting, see BUG_FIXES_SUMMARY.md*
