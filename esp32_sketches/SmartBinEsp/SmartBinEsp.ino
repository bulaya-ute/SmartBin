#include "Camera.h"
#include "Classification.h" 
#include "LEDs.h"
#include "Servos.h"
#include "Ultrasonic.h"
#include "Logger.h"
#include "Communication.h"  // For centralized logging
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

// Create Bluetooth Serial object (used by Logger module)
BluetoothSerial SerialBT;

// Create Communication object for laptop protocol
Communication comm(&SerialBT);

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
  
  // Initialize Logger module first
  Serial.println("[Boot] Initializing Logger module...");
  bool loggerSuccess = initLogger(device_name);
  
  if (loggerSuccess) {
    LOG_BOOT("✅ Logger module initialized successfully");
  } else {
    LOG_BOOT("⚠️ Logger initialized with Serial only - Bluetooth unavailable");
  }
  
  // Print logger status
  printLoggerStatus();

  // TODO: Uncomment out servo init when ready
  // // Initialize modules one by one with debug messages
  // LOG_BOOT("Initializing Servos...");
  // yield(); // Prevent watchdog timeout
  // 
  // // Wrap in try-catch to handle potential crashes
  // try {
  //   initServos();
  //   delay(1000); // Give system time to breathe
  //   LOG_BOOT("✅ Servos initialized");
  // } catch (...) {
  //   LOG_BOOT("⚠️ Warning: Servo initialization failed");
  // }

  // TODO: Uncomment out LED init when ready
  // LOG_BOOT("Initializing LEDs...");
  // yield(); // Prevent watchdog timeout
  //
  // try {
  //   initLEDs();
  //   delay(100); // Give system time to breathe
  //   LOG_BOOT("✅ LEDs initialized");
  // } catch (...) {
  //   LOG_BOOT("⚠️ Warning: LED initialization failed");
  // }

  // Initialize ultrasonic sensor
  LOG_BOOT("Initializing Ultrasonic...");
  yield(); // Prevent watchdog timeout
  try {
    initUltrasonic();
    delay(100); // Give system time to breathe
    LOG_BOOT("✅ Ultrasonic initialized");
  } catch (...) {
    LOG_BOOT("⚠️ Warning: Ultrasonic initialization failed");
  }

  // Initialize camera
  LOG_BOOT("Initializing Camera...");
  yield(); // Prevent watchdog timeout
  try {
    if (initCamera()) {
      delay(100); // Give system time to breathe
      LOG_BOOT("✅ Camera initialized");
    } else {
      LOG_BOOT("⚠️ Warning: Camera initialization failed");
    }
  } catch (...) {
    LOG_BOOT("⚠️ Warning: Camera initialization crashed");
  }

  LOG_BOOT("Initializing Classification...");
  yield(); // Prevent watchdog timeout
  try {
    if (initClassification()) {
      delay(100); // Give system time to breathe
      LOG_BOOT("✅ Classification initialized");
    } else {
      LOG_BOOT("⚠️ Warning: Classification initialization failed");
    }
  } catch (...) {
    LOG_BOOT("⚠️ Warning: Classification initialization crashed");
  }

  // // Initialize all mechanisms to "home" position with error handling
  // LOG_BOOT("Moving to home position...");
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
  //   LOG_BOOT("✅ Bin lid opened");
  // } catch (...) {
  //   LOG_BOOT("⚠️ Warning: Bin lid operation failed");
  // }

  // Initialize Communication Protocol
  LOG_BOOT("Initializing laptop communication protocol...");
  yield(); // Prevent watchdog timeout
  
  try {
    comm.begin();
    LOG_BOOT("✅ Communication protocol initialized");
    
    // Wait for laptop connection - this is REQUIRED for sorting to work
    LOG_BOOT("⏳ Waiting for laptop connection (required for classification)...");
    if (comm.waitForLaptopConnection()) {
      LOG_BOOT("✅ Laptop connected successfully! Sorting will be enabled.");
    } else {
      LOG_BOOT("⚠️ Warning: Laptop connection timeout");
      LOG_BOOT("📋 SmartBin will wait for laptop connection before sorting");
      LOG_BOOT("💡 Make sure laptop script is running and sending MSG_LAPTOP_READY");
    }
    
  } catch (...) {
    LOG_BOOT("⚠️ Warning: Communication initialization failed");
  }

  LOG_SYSTEM("SmartBin Hardware Initialized");
  LOG_SYSTEM("Note: Sorting requires laptop connection");
  LOG_SYSTEM("Watchdog timer reset successfully avoided!");
}

void loop() {
  // Add watchdog reset to prevent hanging
  yield(); // Allow ESP32 to handle background tasks
  
  // Update communication system
  comm.update();
  
  // Check available memory periodically
  static unsigned long lastMemCheck = 0;
  if (millis() - lastMemCheck > 10000) { // Every 10 seconds
    size_t freeHeap = ESP.getFreeHeap();
    if (freeHeap < 50000) { // Less than 50KB free
      Serial.printf("[Warning] Low memory: %d bytes free\n", freeHeap);
    }
    lastMemCheck = millis();
  }
  
  // CRITICAL: Only run sorting logic when laptop is properly connected
  if (!comm.isLaptopConnected()) {
    // Log waiting status occasionally
    static unsigned long lastWaitingLog = 0;
    if (millis() - lastWaitingLog > 5000) { // Every 5 seconds
      LOG_SYSTEM("Waiting for laptop connection before starting sorting...");
      lastWaitingLog = millis();
    }
    return; // Don't run sorting logic without laptop
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
    // No delay needed - servo handles its own timing

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
    // No delay needed - servo handles its own timing

    // Step 6: Open release to drop item
    yield(); // Prevent watchdog timeout
    setRelease(true);
    delay(1000); // Keep this delay for gravity - item needs time to fall
    setRelease(false); // Close release

    // Step 7: Return compartment to zero
    yield(); // Prevent watchdog timeout
    moveToPosition(POSITION_ZERO);
    // No delay needed - servo handles its own timing

    // Step 8: Open lid for next item
    yield(); // Prevent watchdog timeout
    openBinLid();

    logMessage("[Cycle Complete] Sorted '" + detectedClass + "' into respective bin.");

    isProcessing = false;
  }
  
  // Small delay to prevent overwhelming the loop
  delay(100);
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
  // Check if laptop is connected for remote classification
  if (comm.isLaptopConnected()) {
    logMessage("[Classification] Using laptop-based classification");
    
    // Step 1: Capture image using Camera module
    logMessage("[Camera] Starting image capture...");
    
    CapturedImage image = captureImage();
    
    if (!image.isValid) {
      logMessage("[Camera] ERROR: Failed to capture image");
      return "unknown";
    }
    
    logMessage("[Camera] ✅ Image captured successfully");
    
    // Step 2: Send image to laptop for classification
    String classificationResult;
    bool success = comm.sendImageForClassification(
      image.imageData, 
      image.imageSize,
      image.frameBuffer->width,
      image.frameBuffer->height,
      classificationResult
    );
    
    // Release camera buffer
    releaseImage(image);
    
    if (success) {
      logMessage("[Classification] ✅ Laptop classification result: " + classificationResult);
      return classificationResult;
    } else {
      logMessage("[Classification] ❌ Laptop classification failed - falling back to local");
      // Fall through to local classification
    }
  }
  
  // Fallback: Local classification (original method)
  logMessage("[Classification] Using local ESP32 classification");
  
  // Step 1: Capture image using Camera module
  logMessage("[Camera] Starting image capture...");
  
  CapturedImage image = captureImage();
  
  if (!image.isValid) {
    logMessage("[Camera] ERROR: Failed to capture image");
    return "unknown";
  }
  
  logMessage("[Camera] ✅ Image captured successfully");
  
  // For debugging: still print image data when doing local classification
  logMessage("[Camera] Printing image data for verification...");
  printImageAsBase64(image);
  
  // Step 2: Classify image using local Classification module
  logMessage("[Classification] Starting local image classification...");
  
  ClassificationResult result = classifyImage(image);
  
  // Step 3: Clean up image memory
  releaseImage(image);
  
  // setLED1(false);
  
  if (!result.isValid) {
    logMessage("[Classification] ERROR: Classification failed - " + result.errorMessage);
    return "unknown";
  }
  
  // Step 4: Process classification results
  printClassificationDetails(result);
  
  String detectedClass = getTopClass(result);
  
  // Check confidence and handle low-confidence results
  if (!isConfidentResult(result)) {
    logMessage("[Classification] ⚠️ Low confidence result, routing to MISC bin");
    detectedClass = "misc";
  }
  
  // Step 5: Normalize class names to match bin positions
  if (detectedClass == "Plastic" || detectedClass == "Plastic Bottle") {
    detectedClass = "plastic";
  } else if (detectedClass == "Metal" || detectedClass == "Can") {
    detectedClass = "metal";
  } else if (detectedClass == "Paper" || detectedClass == "Cardboard") {
    detectedClass = "paper";
  } else if (detectedClass != "plastic" && detectedClass != "metal" && detectedClass != "paper") {
    detectedClass = "misc";
  }
  
  logMessage("[Classification] ✅ Final classification: " + detectedClass);
  
  return detectedClass;
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
  int currentPos = getCurrentSlidingPosition();
  int displacement = abs(position - currentPos);
  logMessage("[Motor] Moving from " + String(currentPos) + "° to " + String(position) + "° (displacement: " + String(displacement) + "°)");
  rotateSlidingMotor(position); // This will be implemented to move the sliding compartment
}

void setRelease(bool open) {
  int angle = open ? RELEASE_OPEN : RELEASE_CLOSED;
  int currentPos = getCurrentDroppingPosition();
  int displacement = abs(angle - currentPos);
  logMessage((open ? "[Release] Opening" : "[Release] Closing") + String(" from ") + String(currentPos) + "° to " + String(angle) + "° (displacement: " + String(displacement) + "°)");
  rotateDroppingMotor(angle); // Or actuate solenoid, etc.
}

void openBinLid() {
  const int LID_OPEN_ANGLE = 90; // Define this based on your lid mechanism
  int currentPos = getCurrentLidPosition();
  int displacement = abs(LID_OPEN_ANGLE - currentPos);
  logMessage("[Lid] Opening bin lid from " + String(currentPos) + "° to " + String(LID_OPEN_ANGLE) + "° (displacement: " + String(displacement) + "°)");
  rotateLid(LID_OPEN_ANGLE);
}

void closeBinLid() {
  const int LID_CLOSED_ANGLE = 0; // Define this based on your lid mechanism
  int currentPos = getCurrentLidPosition();
  int displacement = abs(LID_CLOSED_ANGLE - currentPos);
  logMessage("[Lid] Closing bin lid from " + String(currentPos) + "° to " + String(LID_CLOSED_ANGLE) + "° (displacement: " + String(displacement) + "°)");
  rotateLid(LID_CLOSED_ANGLE);
}