#include "Servos.h"
#include "LEDs.h"
#include "Ultrasonic.h"
#include "CameraInference.h"
#include "BluetoothSerial.h"


String device_name = "SmartBin_ESP32";

// Check if Bluetooth is available
#if !defined(CONFIG_BT_ENABLED) || !defined(CONFIG_BLUEDROID_ENABLED)
#error Bluetooth is not enabled! Please run `make menuconfig` to and enable it
#endif

// Check Serial Port Profile
#if !defined(CONFIG_BT_SPP_ENABLED)
#error Serial Port Profile for Bluetooth is not available or not enabled. It is only available for the ESP32 chip.
#endif

// Create Bluetooth Serial object
BluetoothSerial SerialBT;

// Bluetooth status flag
bool bluetoothEnabled = false;

// Timing & state
unsigned long lastTrigger = 0;
const unsigned long triggerInterval = 10000; // 10 sec minimum between detections
bool isProcessing = false; // Prevent re-trigger during processing

// Bin positions (servo angles or stepper steps)
const int POSITION_ZERO = 90;     // Default waiting position
const int POSITION_PLASTIC = 0;
const int POSITION_METAL = 60;
const int POSITION_PAPER = 120;
const int POSITION_MISC = 180;

// Release mechanism angle (example: 0 = closed, 90 = open)
const int RELEASE_OPEN = 90;
const int RELEASE_CLOSED = 0;

// Distance threshold for object detection (in cm)
const float DETECTION_THRESHOLD = 10.0f;

void setup() {
  Serial.begin(115200);
  delay(1000); // Give serial time to initialize
  
  Serial.println("[Boot] Starting SmartBin initialization...");
  
  // Initialize Bluetooth Serial
  Serial.println("[Boot] Initializing Bluetooth...");
  
  // Add error handling for Bluetooth initialization
  if (!SerialBT.begin(device_name)) {
    Serial.println("[Boot] ERROR: Bluetooth initialization failed");
    bluetoothEnabled = false;
    // Continue without Bluetooth
  } else {
    Serial.printf("[Boot] Bluetooth Serial Started - Device Name: \"%s\"\n", device_name.c_str());
    bluetoothEnabled = true;
  }

  // TODO: Uncomment out servo init when ready
  // // Initialize modules one by one with debug messages
  // logMessage("[Boot] Initializing Servos...");
  // yield(); // Prevent watchdog timeout
  // 
  // // Wrap in try-catch to handle potential crashes
  // try {
  //   initServos();
  //   delay(1000); // Give system time to breathe
  //   logMessage("[Boot] ✅ Servos initialized");
  // } catch (...) {
  //   logMessage("[Boot] ⚠️ Warning: Servo initialization failed");
  // }

  // TODO: Uncomment out LED init when ready
  // logMessage("[Boot] Initializing LEDs...");
  // yield(); // Prevent watchdog timeout
  //
  // try {
  //   initLEDs();
  //   delay(100); // Give system time to breathe
  //   logMessage("[Boot] ✅ LEDs initialized");
  // } catch (...) {
  //   logMessage("[Boot] ⚠️ Warning: LED initialization failed");
  // }

  // TODO: Uncomment out ultrasonic init when ready
  logMessage("[Boot] Initializing Ultrasonic...");
  yield(); // Prevent watchdog timeout
  
  try {
    initUltrasonic();
    delay(100); // Give system time to breathe
    logMessage("[Boot] ✅ Ultrasonic initialized");
  } catch (...) {
    logMessage("[Boot] ⚠️ Warning: Ultrasonic initialization failed");
  }

  // logMessage("[Boot] Initializing Camera...");
  // yield(); // Prevent watchdog timeout
  
  // try {
  //   initCamera();
  //   delay(100); // Give system time to breathe
  //   logMessage("[Boot] ✅ Camera initialized");
  // } catch (...) {
  //   logMessage("[Boot] ⚠️ Warning: Camera initialization failed");
  // }

  // // Initialize all mechanisms to "home" position with error handling
  // logMessage("[Boot] Moving to home position...");
  // yield(); // Prevent watchdog timeout
  
  // try {
  //   moveToPosition(POSITION_ZERO);
  //   delay(100); // Give system time to breathe
  //   logMessage("[Boot] ✅ Moved to home position");
  // } catch (...) {
  //   logMessage("[Boot] ⚠️ Warning: Move to home position failed");
  // }

  // logMessage("[Boot] Setting release mechanism...");
  // yield(); // Prevent watchdog timeout
  
  // try {
  //   setRelease(false); // Closed
  //   delay(100); // Give system time to breathe
  //   logMessage("[Boot] ✅ Release mechanism set");
  // } catch (...) {
  //   logMessage("[Boot] ⚠️ Warning: Release mechanism failed");
  // }

  // logMessage("[Boot] Opening bin lid...");
  // yield(); // Prevent watchdog timeout
  
  // try {
  //   openBinLid();
  //   delay(100); // Give system time to breathe
  //   logMessage("[Boot] ✅ Bin lid opened");
  // } catch (...) {
  //   logMessage("[Boot] ⚠️ Warning: Bin lid operation failed");
  // }

  logMessage("[System] SmartBin Ready and Initialized");
  logMessage("[System] Watchdog timer reset successfully avoided!");
}

void loop() {
  // Add watchdog reset to prevent hanging
  yield(); // Allow ESP32 to handle background tasks
  
  // Check available memory periodically
  static unsigned long lastMemCheck = 0;
  if (millis() - lastMemCheck > 10000) { // Every 10 seconds
    size_t freeHeap = ESP.getFreeHeap();
    if (freeHeap < 50000) { // Less than 50KB free
      Serial.printf("[Warning] Low memory: %d bytes free\n", freeHeap);
    }
    lastMemCheck = millis();
  }
  
  if (isProcessing) return; // Don't interrupt ongoing cycle

  unsigned long currentMillis = millis();

  // Check if enough time has passed since last trigger
  if (currentMillis - lastTrigger < triggerInterval) {
    return;
  }

  // Step 1: Wait for item
  if (isItemDetected()) {
    lastTrigger = currentMillis;
    isProcessing = true;

    logMessage("[Detection] Item detected! Starting sorting cycle...");

    // Step 2: Close bin lid
    yield(); // Prevent watchdog timeout
    closeBinLid();
    delay(500); // Allow lid to close

    // Step 3: Capture image
    yield(); // Prevent watchdog timeout
    String detectedClass = captureAndClassify();

    if (detectedClass == "unknown") {
      logMessage("[Error] Classification failed or ambiguous. Routing to MISC.");
      detectedClass = "misc";
    }

    // Step 4: Map class to position
    yield(); // Prevent watchdog timeout
    int targetPosition = getTargetPosition(detectedClass);

    // Step 5: Slide compartment to correct bin
    yield(); // Prevent watchdog timeout
    moveToPosition(targetPosition);
    delay(500); // Stabilize

    // Step 6: Open release to drop item
    yield(); // Prevent watchdog timeout
    setRelease(true);
    delay(1000); // Allow item to drop (adjust based on gravity/mechanics)
    setRelease(false); // Close release

    // Step 7: Return compartment to zero
    yield(); // Prevent watchdog timeout
    moveToPosition(POSITION_ZERO);
    delay(500);

    // Step 8: Open lid for next item
    yield(); // Prevent watchdog timeout
    openBinLid();

    logMessage("[Cycle Complete] Sorted '" + detectedClass + "' into respective bin.");

    isProcessing = false;
  }
  
  // Small delay to prevent overwhelming the loop
  delay(100);
}

// === Logging Function ===
void logMessage(String message) {
  // Always send to Serial
  Serial.println(message);
  
  // Only send to Bluetooth if it's enabled and has a connected client
  if (bluetoothEnabled && SerialBT.available() && SerialBT.hasClient()) {
    try {
      SerialBT.println(message);
    } catch (...) {
      // Ignore Bluetooth errors to prevent crashes
      Serial.println("[Warning] Bluetooth send failed");
    }
  }
}

// === High-Level Helper Functions ===

bool isItemDetected() {
  float distance = readUltrasonicDistance(); // From Ultrasonic.h
  
  // Only log occasionally to avoid spam
  static unsigned long lastLog = 0;
  if (millis() - lastLog > 2000) { // Log every 2 seconds
    // Handle invalid readings from ultrasonic sensor
    if (distance <= 0 || distance > 400) {
      logMessage("[Ultrasonic] Invalid reading: " + String(distance) + " cm (sensor may be disconnected)");
    } else {
      String msg = "[Ultrasonic] Distance: " + String(distance) + " cm";
      logMessage(msg);
    }
    lastLog = millis();
  }

  // Return false if invalid reading (prevents false triggers)
  if (distance <= 0 || distance > 400) {
    return false;
  }

  return distance < DETECTION_THRESHOLD;
}

String captureAndClassify() {
  // Optional: Flash LED before capture
  setLED1(true);
  delay(100);

  String className = runInference(); // From CameraInference.h
  setLED1(false);

  logMessage("[AI] Detected class: " + className);

  // Normalize or map possible model outputs
  if (className == "Plastic" || className == "Plastic Bottle") {
    return "plastic";
  } else if (className == "Metal" || className == "Can") {
    return "metal";
  } else if (className == "Paper" || className == "Cardboard") {
    return "paper";
  } else {
    return "misc";
  }
}

int getTargetPosition(String className) {
  if (className == "plastic") return POSITION_PLASTIC;
  if (className == "metal") return POSITION_METAL;
  if (className == "paper") return POSITION_PAPER;
  return POSITION_MISC; // default
}

// === Servo/Actuator Control (to be implemented in Servos.h/.cpp) ===
// These are just wrappers — actual servo control goes in Servos.cpp

void moveToPosition(int position) {
  logMessage("[Motor] Moving to position: " + String(position));
  rotateSlidingMotor(position); // This will be implemented to move the sliding compartment
}

void setRelease(bool open) {
  int angle = open ? RELEASE_OPEN : RELEASE_CLOSED;
  logMessage(open ? "[Release] Opening..." : "[Release] Closing...");
  rotateDroppingMotor(angle); // Or actuate solenoid, etc.
}

void openBinLid() {
  logMessage("[Lid] Opening bin lid...");
  // Example: rotateLidServo(LID_OPEN_ANGLE);
}

void closeBinLid() {
  logMessage("[Lid] Closing bin lid...");
  // Example: rotateLidServo(LID_CLOSED_ANGLE);
}