# 📋 SmartBin Quick Setup & Operation Guide

## 🔧 Administrator Setup (Start of Day)

### 1. Power On System
```bash
# ESP32-CAM powers on automatically
# Blue LED indicates successful boot
```

### 2. Start GUI Application
```bash
cd /home/bulaya/StudioProjects/SmartBin
source .venv/bin/activate
python smartbin_gui.py
```

### 3. Initialize Connection
1. Enter administrator password when prompted
2. Verify ESP32 MAC: `EC:E3:34:15:F2:62`
3. Click "🔗 Connect"
4. Wait for "🟢 Connected" status

### 4. System Check
```
Send command: test-servos
Send command: status
```

### 5. Ready for Users
- System status: "🟢 Connected"
- Bins empty and positioned
- Coin dispenser loaded
- "Ready" indicator visible

---

## 👥 User Operation (Public Use)

### Simple Steps for Users:
1. **Drop item** in the bin opening
2. **Wait 10-15 seconds** for processing
3. **Collect coin** if item was recyclable
4. **Done!** ✅

### What Users See:
- **Recyclable items** → Left bin + Coin reward 🪙
- **Non-recyclable items** → Right bin + No coin

---

## 🎯 Classification Categories

| **Recyclable (Coin Reward)** | **Non-Recyclable (No Coin)** |
|------------------------------|-------------------------------|
| 🥤 Aluminium cans           | 💻 E-waste (electronics)     |
| 📦 Cardboard boxes          | 🍎 Organic waste (food)      |
| 🍾 Glass bottles            | 👕 Textiles (clothing)       |
| 📄 Paper documents          | 🪵 Wood items                |
| 🥤 Plastic bottles          |                               |

---

## 🚨 Troubleshooting Quick Reference

| **Problem** | **Admin Action** | **User Guidance** |
|-------------|------------------|-------------------|
| No connection | Restart GUI, check ESP32 | "System temporarily unavailable" |
| Item stuck | Power cycle, clear manually | "Please contact administrator" |
| No coin for recyclable | Check dispenser, refill coins | "Coin dispenser may be empty" |
| Wrong classification | Review confidence scores | "System learns from usage" |

---

## 📊 Daily Monitoring Checklist

- [ ] Connection stable (>95% uptime)
- [ ] Classification accuracy (>85% confidence)
- [ ] Coin dispenser level (refill at <3 coins)
- [ ] Bin levels (empty at 80% full)
- [ ] Error messages reviewed
- [ ] User feedback collected

---

## 🎛️ Quick Commands Reference

| **Command** | **Purpose** | **Expected Result** |
|-------------|-------------|---------------------|
| `status` | System health check | Shows connection, memory, motor positions |
| `test-servos` | Motor functionality | Servos move to test positions and return |
| `recyclable` | Manual recyclable processing | Coin + recyclable bin routing |
| `non-recyclable` | Manual non-recyclable processing | Non-recyclable bin routing only |

---

## 🔄 Daily Startup/Shutdown

### Morning Startup (5 minutes)
1. Power on ESP32 → Wait for boot
2. Start GUI → Enter password
3. Connect to ESP32 → Verify green status
4. Test servos → Confirm operation
5. Check supplies → Coins, bins empty

### Evening Shutdown (2 minutes)
1. Ensure no active processing
2. Disconnect GUI → Click disconnect
3. Close application → Safe exit
4. Power off ESP32 → Unplug safely
5. Secure coins → Store remaining coins

---

**🎉 System Ready for Smart Waste Sorting!**

*For detailed instructions, see full Admin and User Manuals*
