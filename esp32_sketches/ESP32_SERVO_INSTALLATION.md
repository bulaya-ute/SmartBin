# ESP32 Servo Library Installation Guide

## The Problem
The standard Arduino `Servo` library is not compatible with ESP32 and will cause compilation errors:
```
error: #error "This library only supports boards with an AVR, SAM, SAMD, NRF52, STM32F4, Renesas or XMC processor."
```

## Solution: Install ESP32Servo Library

### Method 1: Arduino IDE Library Manager
1. Open Arduino IDE
2. Go to **Tools** → **Manage Libraries...**
3. Search for "ESP32Servo"
4. Find "ESP32Servo" by Kevin Harrington
5. Click **Install**

### Method 2: Arduino IDE Manual Installation
1. Download from: https://github.com/jkb-git/ESP32Servo
2. Extract to Arduino libraries folder:
   - Windows: `Documents/Arduino/libraries/`
   - Linux: `~/Arduino/libraries/`
   - macOS: `~/Documents/Arduino/libraries/`

### Method 3: PlatformIO
Add to `platformio.ini`:
```ini
lib_deps = 
    madhephaestus/ESP32Servo@^0.13.0
```

## Code Changes Made
- Replaced `#include <Servo.h>` with `#include <ESP32Servo.h>`
- Added ESP32PWM timer allocation in setup()
- Added proper servo initialization with frequency and pulse width settings

## ESP32Servo Features
- Compatible with ESP32 architecture
- Supports standard servo control (0-180 degrees)
- Configurable PWM frequency and pulse width
- Multiple servo support with timer allocation

## Usage
```cpp
#include <ESP32Servo.h>

Servo myServo;

void setup() {
  ESP32PWM::allocateTimer(0);
  myServo.setPeriodHertz(50);    // standard 50 hz servo
  myServo.attach(servoPin, 1000, 2000); // Min/Max pulse width in microseconds
}

void loop() {
  myServo.write(90); // Move to 90 degrees
}
```

## Verification
After installing ESP32Servo library, the SmartBin ESP32 code should compile successfully without servo-related errors.
