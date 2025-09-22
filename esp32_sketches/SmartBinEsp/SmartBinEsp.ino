#include "Camera.h"
#include "Classification.h" 
#include "Servos.h"
#include "Ultrasonic.h"
#include "Logger.h"
#include "Bluetooth.h"         // Includes BluetoothSerial and SerialBT extern declaration
#include "Communication.h"     // For centralized logging

String device_name = "SmartBin_ESP32";

// Check if Bluetooth is available
#if !defined(CONFIG_BT_ENABLED) || !defined(CONFIG_BLUEDROID_ENABLED)
#error Bluetooth is not enabled! Please run `make menuconfig` to and enable it
#endif

// Check Serial Port Profile
#if !defined(CONFIG_BT_SPP_ENABLED)
#error Serial Port Profile for Bluetooth is not available or not enabled. It is only available for the ESP32 chip.
#endif

// SerialBT is already defined in Bluetooth.cpp and declared as extern in Bluetooth.h

// Create Communication object for laptop protocol
Communication comm(&SerialBT);

// Timing & state
unsigned long lastTrigger = 0;
const unsigned long triggerInterval = 10000; // 10 sec minimum between detections
bool isProcessing = false; // Prevent re-trigger during processing

// Old position constants - no longer used with new two-motor system
/*
// Bin positions (servo angles or stepper steps)
const int POSITION_ZERO = 90;     // Default waiting position
const int POSITION_PLASTIC = 0;
const int POSITION_METAL = 60;
const int POSITION_PAPER = 120;
const int POSITION_MISC = 180;

// Release mechanism angle (example: 0 = closed, 90 = open)
const int RELEASE_OPEN = 90;
const int RELEASE_CLOSED = 0;
*/

// New two-motor system constants
const int SLIDING_HOME = 90;           // Sliding motor home position
const int SLIDING_RECYCLABLE = 30;     // Recyclable bin position (reduced angle)
const int SLIDING_NON_RECYCLABLE = 150; // Non-recyclable bin position (reduced angle)

const int COIN_HOME = 90;             // Coin dispenser home position (changed from 0)
const int COIN_DISPENSE = 0;          // Coin dispense position (changed from 100)

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

  // Initialize servos for two-motor system
  LOG_BOOT("Initializing Servos...");
  yield(); // Prevent watchdog timeout
  
  // Wrap in try-catch to handle potential crashes
  try {
    initServos();
    delay(1000); // Give system time to breathe
    LOG_BOOT("✅ Servos initialized");
    
    // Test servo movement to ensure they're working
    LOG_BOOT("Testing servo movement...");
    
    // Check if servos are properly attached before testing
    Serial.println("[Servo Debug] Checking servo attachment status...");
    
    // Test coin dispenser
    logMessage("[Servo Test] Testing coin dispenser movement");
    logMessage("[Debug] About to move coin dispenser to 45°");
    rotateCoinDispenser(45);  // Move to middle position
    delay(1000);
    logMessage("[Debug] About to move coin dispenser to 90° (home)");
    rotateCoinDispenser(90);   // Return to home
    delay(500);
    
    // Test sliding motor
    logMessage("[Servo Test] Testing sliding motor movement");
    Serial.println("[Debug] About to move sliding motor to 60°");
    rotateSlidingMotor(60);   // Move to test position
    delay(1000);
    logMessage("[Debug] About to move sliding motor to 90° (home)");
    rotateSlidingMotor(90);   // Return to home
    delay(500);
    
    LOG_BOOT("✅ Servo movement test completed");
    
  } catch (...) {
    LOG_BOOT("⚠️ Warning: Servo initialization failed");
  }

  // LED and buzzer functionality removed for stability
  LOG_BOOT("LED and buzzer functionality disabled");

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
      // Test coin dispenser
      rotateCoinDispenser(45);  // Test position
      delay(1000);
      rotateCoinDispenser(COIN_HOME);  // Return home
      delay(500);
      // Test sliding motor
      rotateSlidingMotor(60);   // Test position
      delay(1000);
      rotateSlidingMotor(SLIDING_HOME);  // Return home
      SerialBT.println("[Command] Servo test complete");
    }
    else if (command == "status") {
      SerialBT.println("[Status] SmartBin System Status:");
      SerialBT.println("- Laptop Connected: " + String(comm.isLaptopConnected() ? "Yes" : "No"));
      SerialBT.println("- Processing: " + String(isProcessing ? "Yes" : "No"));
      SerialBT.println("- Free Memory: " + String(ESP.getFreeHeap()) + " bytes");
      SerialBT.println("- Motor Positions: Sliding=" + String(SLIDING_HOME) + "°, Coin=" + String(COIN_HOME) + "°");
    }
    else if (command != "") {
      SerialBT.println("[Error] Unknown command: " + command);
      SerialBT.println("Available commands: recyclable, non-recyclable, test-servos, status");
    }
  }
  
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

    // System processing state (LED functionality disabled)
    // setSystemState(SYSTEM_BUSY);

    logMessage("[Detection] Item detected! Starting sorting cycle...");

    // Step 2: Capture image (bin lid motor removed)
    yield(); // Prevent watchdog timeout
    String detectedClass = captureAndClassify();

    if (detectedClass == "unknown") {
      logMessage("[Error] Classification failed or ambiguous. Routing to non-recyclable.");
      detectedClass = "organic_waste"; // Default to a valid 9-class category
    }

    // Extract class name from result (remove confidence score if present)
    int spaceIndex = detectedClass.indexOf(' ');
    if (spaceIndex > 0) {
      String originalResult = detectedClass;
      detectedClass = detectedClass.substring(0, spaceIndex);
      logMessage("[Processing] Extracted class '" + detectedClass + "' from result '" + originalResult + "'");
    }

    // Step 3: Map detailed classification to binary for motors
    yield(); // Prevent watchdog timeout
    
    // Map 9-class classification to binary recyclable/non-recyclable
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
      delay(1000);  // Hold dispense position
      rotateCoinDispenser(COIN_HOME);      // Return to home (90°)
      delay(500);   // Brief pause
      
      // Then: Route to recyclable bin
      rotateSlidingMotor(SLIDING_RECYCLABLE);   // Move to recyclable position (30°)
      delay(3000);  // Hold for 3 seconds to allow waste to fall
      rotateSlidingMotor(SLIDING_HOME);         // Return to home position (90°)
    }
    else {
      // Non-recyclable: Route to non-recyclable bin (no coin)
      logMessage("[Sorting] Non-recyclable material detected (" + detectedClass + ") - routing to non-recyclable bin");
      rotateSlidingMotor(SLIDING_NON_RECYCLABLE);  // Move to non-recyclable position (150°)
      delay(3000);  // Hold for 3 seconds to allow waste to fall
      rotateSlidingMotor(SLIDING_HOME);            // Return to home position (90°)
    }

    logMessage("[Cycle Complete] Sorted '" + detectedClass + "' - motors returned to home.");

    // Return system to ready state (LED functionality disabled)
    // setSystemState(SYSTEM_READY);

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
    logMessage("[Classification] ⚠️ Low confidence result, routing to non-recyclable bin");
    detectedClass = "organic_waste"; // Default to a valid 9-class category
  }
  
  // Step 5: Normalize class names to match bin positions
  if (detectedClass == "Plastic" || detectedClass == "Plastic Bottle") {
    detectedClass = "plastic";
  } else if (detectedClass == "Metal" || detectedClass == "Can") {
    detectedClass = "metal";
  } else if (detectedClass == "Paper" || detectedClass == "Cardboard") {
    detectedClass = "paper";
  } else if (detectedClass != "plastic" && detectedClass != "metal" && detectedClass != "paper") {
    // For unrecognized classifications, default to organic_waste (non-recyclable)
    logMessage("[Classification] ⚠️ Unrecognized class, defaulting to organic_waste");
    detectedClass = "organic_waste";
  }
  
  logMessage("[Classification] ✅ Final classification: " + detectedClass);
  
  return detectedClass;
}

// Old position-based functions removed - now using direct motor control
/*
int getTargetPosition(String className) {
  if (className == "plastic") return POSITION_PLASTIC;
  if (className == "metal") return POSITION_METAL;
  if (className == "paper") return POSITION_PAPER;
  return POSITION_MISC; // default
}
*/

// === Two-Motor Control System ===
// Direct motor control - no wrapper functions needed anymore

// Old servo wrapper functions removed - using direct calls now
/*
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
*/

// Bin lid functions removed - hardware no longer present