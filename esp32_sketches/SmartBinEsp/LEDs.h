#ifndef LEDS_H
#define LEDS_H

extern int LED1_PIN;
extern int LED2_PIN;
extern int LED3_PIN;

void initLEDs();
void setLED1(bool state);
void setLED2(bool state);
void setLED3(bool state);

#endif
