# INAV configuration notes

Firmware: **INAV 9.0.1**, target `MATEKF405SE` on a MATEK F405-WING V2.

---

## Ports

| Port | Function | Protocol | Baud |
|---|---|---|---|
| USB | Configurator, MSP | MSP | n/a |
| UART1 | Serial RX | CRSF (ExpressLRS) | 115200 |
| UART3 | GPS | UBLOX (M10) | 115200 |
| I2C | Magnetometer | QMC5883L at `0x0D` | 400 kHz |

---

## Sensors

| Sensor | Part | Bus | Note |
|---|---|---|---|
| Accelerometer and gyro | ICM42605 | SPI, onboard | |
| Barometer | SPL06 | I2C, onboard | |
| Magnetometer | QMC5883L | I2C, external | **Must be set explicitly.** Auto-detection fails; see below |
| GNSS | u-blox M10 | UART3 | GPS + Galileo + BeiDou concurrent |

### The magnetometer trap

The M100-5883 carries a **QMC5883L at `0x0D`**, not the legacy **HMC5883L at `0x1E`** that the "5883" in the part name implies. They share a number and nothing else.

INAV's auto-detection does not resolve this reliably. Set the magnetometer type explicitly to `QMC5883` in the Configuration tab and reboot. An I2C bus scan confirming a single device at `0x0D` is what identified this; the sketch is in [`firmware/i2c_scanner/`](../firmware/i2c_scanner/) and the full analysis is in [`docs/i2c-debug.md`](../docs/i2c-debug.md).

> **Open item.** The scan was run with the Arduino `Wire` default of 100 kHz, while the flight controller runs the bus at 400 kHz. Presence at 100 kHz was proven; integrity at 400 kHz was assumed. Re-run with `Wire.setClock(400000)` before adding anything else to this bus.

### Compass calibration

Rotate the airframe through 360 degrees on each of three axes while INAV logs per-axis minima and maxima to compute the hard-iron offset. Run it three times and cross-reference the final heading against a handheld compass before accepting.

Calibration quality is the largest single variable in GPS-mode stability. A poor calibration makes the vehicle fight its own heading estimate during position hold and drift in slow circles, which looks like a tuning problem and is not one.

---

## Mixer and outputs

- Mixer: **Quadcopter X**
- Motors on the first four PWM outputs
- Motor directions: 2 CW and 2 CCW per the X-config diagram, verified visually and on the motor test page

> **Open item.** `motor_pwm_protocol` and `motor_pwm_rate` have not been recorded here and need to be read out of the CLI. If the output is standard PWM at 50 Hz, the actuator contributes 79 degrees of phase lag at a 20 Hz rate-loop crossover, which is more than the whole phase margin a stable loop has to spend. See [`docs/calculations.md §7`](../docs/calculations.md#7-actuator-bandwidth). This is roadmap item 1.

---

## Battery profile

- 3S LiPo, 5000 mAh
- Voltage divider calibrated against a multimeter to within 0.05 V, so the low-voltage warning is trustworthy
- No current sensor fitted, so consumed-capacity estimates are voltage-based only

---

## Flight modes in use

| Mode | Aux | Status |
|---|---|---|
| Angle | Aux 1 | Enabled |
| Altitude hold | Aux 2 | Enabled |
| GPS position hold | Aux 2 | Enabled |
| Return to home | Aux 3 | Enabled |
| Waypoint mission | n/a | **Not enabled.** See [`docs/regulatory.md`](../docs/regulatory.md) |

---

## PID tuning

Defaults retained. Tuning was deferred until a stable hover existed to tune against, and has not been revisited since.

This is deliberate but not ideal. Retuning is only worth doing after the motor output protocol question is resolved, because changing the actuator update rate changes the phase budget the gains are being tuned inside. Tuning first and then changing the protocol would mean tuning twice.

---

## CLI dump

`cli_dump.txt` in this directory holds the full `dump all` output for a complete restore. Regenerate it after any configuration change:

```
# in the INAV CLI
dump all
```

then copy the console output to the file.
