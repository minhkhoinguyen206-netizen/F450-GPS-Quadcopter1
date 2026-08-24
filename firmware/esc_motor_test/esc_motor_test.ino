// esc_motor_test.ino
//
// Drives one ESC from an analog potentiometer so that each ESC and motor pair
// can be validated on the bench before the flight controller is integrated.
//
// The arming sequence is written out explicitly rather than relied upon: an
// ESC that is not armed and an ESC that is armed but receiving minimum
// throttle look identical, and telling them apart later costs more time than
// being explicit here.
//
// Wiring:  B10K potentiometer wiper -> A0
//          ESC signal wire          -> D9
//          ESC and Arduino grounds tied together
//
// Do not fit a propeller for this test.

#include <Servo.h>

Servo esc;
const int POT_PIN = A0;
const int ESC_PIN = 9;

const int PWM_MIN_US = 1000;   // ESC minimum throttle pulse
const int PWM_MAX_US = 2000;   // ESC maximum throttle pulse
const int ARM_HOLD_MS = 2000;  // hold minimum throttle to enter armed state

void setup() {
  Serial.begin(9600);
  esc.attach(ESC_PIN, PWM_MIN_US, PWM_MAX_US);

  esc.writeMicroseconds(PWM_MIN_US);
  delay(ARM_HOLD_MS);
  Serial.println("ESC armed. Rotate potentiometer to drive motor.");
}

void loop() {
  int rawADC = analogRead(POT_PIN);                              // 0..1023
  int pwm_us = map(rawADC, 0, 1023, PWM_MIN_US, PWM_MAX_US);
  esc.writeMicroseconds(pwm_us);

  Serial.print("ADC=");
  Serial.print(rawADC);
  Serial.print("  PWM=");
  Serial.print(pwm_us);
  Serial.println(" us");

  delay(20);                                                     // 50 Hz update
}
