#ifndef LOGGER_H
#define LOGGER_H

#include <Arduino.h>

// Logger initialization and control functions
bool initLogger(const String& btDeviceName = "SmartBin_ESP32");
void deinitLogger();

// Core logging functions
void logMessage(const String& message);
void logMessageNoNewline(const String& message);
void logLongMessage(const String& message, const String& prefix = "");  // For chunking long messages

// Logger status and control
bool isLoggerInitialized();
bool isBluetoothLoggingEnabled();
bool isSerialLoggingEnabled();
void setBluetoothLogging(bool enabled);
void setSerialLogging(bool enabled);
String getDeviceName();

// Logger information and statistics
void printLoggerStatus();
void printLoggerStats();
void resetLoggerStats();

// Helper macros for different log levels
#define LOG_INFO(msg) logMessage(String("[INFO] ") + msg)
#define LOG_WARNING(msg) logMessage(String("[WARNING] ") + msg)
#define LOG_ERROR(msg) logMessage(String("[ERROR] ") + msg)
#define LOG_DEBUG(msg) logMessage(String("[DEBUG] ") + msg)

// Module-specific logging macros
#define LOG_CAMERA(msg) logMessage(String("[Camera] ") + msg)
#define LOG_CLASSIFICATION(msg) logMessage(String("[Classification] ") + msg)
#define LOG_ULTRASONIC(msg) logMessage(String("[Ultrasonic] ") + msg)
#define LOG_SERVOS(msg) logMessage(String("[Servos] ") + msg)
#define LOG_LEDS(msg) logMessage(String("[LEDs] ") + msg)
#define LOG_CLASSIFIER(msg) logMessage(String("[SmartBinClassifier] ") + msg)
#define LOG_BOOT(msg) logMessage(String("[Boot] ") + msg)
#define LOG_SYSTEM(msg) logMessage(String("[System] ") + msg)

#endif // LOGGER_H
