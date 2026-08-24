// i2c_scanner.ino
//
// Scans the I2C bus and reports every device that acknowledges at any address
// from 1 to 126.
//
// Written to settle a specific question: INAV detected the GNSS receiver on
// the M100-5883 module but reported no magnetometer. The choice was between
// replacing the module and finding out what was actually on the bus. This
// sketch answers the second question in about thirty seconds.
//
// The scan returned a single device at 0x0D, which is the QMC5883L. The
// legacy HMC5883L that the "5883" in the part name suggests lives at 0x1E.
// Setting the magnetometer type explicitly in INAV fixed detection on the
// next reboot.
//
// Wiring:  Arduino SDA/SCL tied to the same physical bus lines as the module,
//          grounds common.

#include <Wire.h>

void setup() {
  Wire.begin();
  Serial.begin(115200);
  while (!Serial) {}
  Serial.println("I2C scanner starting...");
}

void loop() {
  byte error, address;
  int count = 0;

  Serial.println("Scanning...");

  for (address = 1; address < 127; address++) {
    Wire.beginTransmission(address);
    error = Wire.endTransmission();

    if (error == 0) {
      Serial.print("Found I2C device at 0x");
      if (address < 16) Serial.print("0");
      Serial.println(address, HEX);
      count++;
    }
  }

  if (count == 0) {
    Serial.println("No I2C devices found.");
  } else {
    Serial.print("Scan done, ");
    Serial.print(count);
    Serial.println(" device(s).");
  }

  delay(2000);
}
