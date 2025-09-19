# Motor Priority Pin Configuration

## Overview
Prioritizing motor functionality over flash LED to ensure reliable servo operation.

## New Pin Assignments

### Servo Motors
- **Coin Dispenser**: GPIO 13 (changed from GPIO 14)
- **Sliding Motor**: GPIO 4 (changed from GPIO 15, **former flash LED pin**)

### Ultrasonic Sensor
- **Trigger**: GPIO 2 (unchanged)
- **Echo**: GPIO 14 (changed from GPIO 13)

### Camera
- **Flash LED**: **DISABLED** (GPIO 4 now used for sliding motor)
- All camera data pins remain unchanged

## Trade-offs Made

### ✅ Benefits
- Motors should work reliably without camera DMA conflicts
- GPIO 14 and 15 (problematic pins) no longer used for servos
- Ultrasonic sensor gets the GPIO 14 echo pin as requested

### ⚠️ Compromises
- **Flash LED functionality lost** - images may be darker in low light
- Camera still functional but without illumination assistance

## Hardware Wiring Updates Required

1. **Coin Dispenser Servo**: 
   - Move signal wire from GPIO 14 → **GPIO 13**

2. **Sliding Motor Servo**: 
   - Move signal wire from GPIO 15 → **GPIO 4**

3. **Ultrasonic Echo**: 
   - Move echo wire from GPIO 13 → **GPIO 14**

4. **Flash LED**: 
   - Disconnect (GPIO 4 now used for servo)

## Expected Behavior

### During Startup
```
[Servo] Coin dispenser attached to GPIO 13
[Servo] Sliding motor attached to GPIO 4
[Camera] Flash LED disabled (GPIO 4 used for servo)
```

### During Operation
- Motors should operate without camera crashes
- Camera captures will work but without flash illumination
- Image quality may be reduced in low-light conditions
- Ultrasonic sensor should work normally with new echo pin

## Testing Checklist

- [ ] Motors initialize properly on GPIO 13 and 4
- [ ] Camera captures images without crashing
- [ ] Ultrasonic sensor reads distance correctly
- [ ] No GPIO conflicts during simultaneous operations
- [ ] Classification system works with new motor pins

## Fallback Plan

If image quality becomes problematic without flash:
- Consider external LED illumination
- Adjust camera sensor settings for low-light performance
- Use alternative servo pins if GPIO 4 proves necessary for flash
