#ifndef BLUETOOTH_H
#define BLUETOOTH_H

#include "BluetoothSerial.h"

// Bluetooth configuration
#define BT_DEVICE_NAME "SmartBin_ESP32"

extern BluetoothSerial SerialBT;

void initBluetooth();
void bluetoothPrint(const String& message);
void bluetoothPrintln(const String& message);
void bluetoothPrintf(const char* format, ...);

// Combined print functions (Serial + Bluetooth)
void dualPrint(const String& message);
void dualPrintln(const String& message);
void dualPrintf(const char* format, ...);

#endif
