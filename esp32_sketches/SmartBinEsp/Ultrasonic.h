#ifndef ULTRASONIC_H
#define ULTRASONIC_H

extern int ULTRASONIC_TRIG_PIN;
extern int ULTRASONIC_ECHO_PIN;

void initUltrasonic();
float readUltrasonicDistance();

#endif
