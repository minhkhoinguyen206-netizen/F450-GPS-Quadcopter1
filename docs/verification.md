# Verification plan

Every performance figure in this repository is a prediction. This document is the procedure that turns each one into a measurement, ordered by information gained per dollar spent.

The airframe currently carries no blackbox logging, no telemetry downlink and no current sensing, and the build had no thrust stand or wattmeter. That is the gap.

---

## Priority 0: already done, and it should have been done first

**Review the footage.** Six takeoff attempts were filmed on a phone at 30 fps and then not looked at frame by frame for months. Doing so resolved the axis of the divergence, which had been recorded as an impression, and replaced "roughly a second" with 0.25 s to 30° of bank. See [`fault-analysis.md`](fault-analysis.md#video-evidence).

Cost: zero. A phone at 30 fps resolves 33 ms, which is more than enough to time an event that takes 400 ms. For any repeatable mechanical failure, film it before instrumenting anything.

## Priority 1: free, and closes the biggest gaps

### 1. Weigh the vehicle

**Equipment:** a kitchen scale.

All-up weight is the single loosest input in [`calculations.md`](calculations.md). It propagates into thrust-to-weight, endurance, roll inertia and therefore into the fault model. The current figure of 1200 g is a sum of catalogue masses plus an estimate for wiring.

Weigh it twice: once with the battery, once without, so the pack's share is separated. Then update `MASS_BUDGET` in `analysis/performance_model.py` and re-run. Every table regenerates.

**What it decides:** whether thrust-to-weight is 1.93 or 1.54, which is the difference between a vehicle with adequate authority and one without.

### 2. Read the motor output protocol out of the CLI

**Equipment:** a USB cable and the INAV configurator.

```
get motor_pwm_protocol
get motor_pwm_rate
```

**What it decides:** whether [finding 1](../README.md#finding-1-the-motor-output-protocol-may-be-eating-the-entire-phase-margin) is a live defect or a documentation error. At 50 Hz the actuator contributes 79 degrees of phase lag at a 20 Hz crossover, which is more than the entire margin a stable loop has. At 400 Hz it contributes 16 degrees.

If the result is `STANDARD` at 50 Hz, change it. If the ESCs accept DSHOT600, use that: it removes the term from the budget entirely and removes ESC throttle calibration as a source of arm-to-arm asymmetry.

### 3. Continuity check on the ESC BEC wiring

**Equipment:** a multimeter.

With the battery disconnected, check whether more than one ESC's +5 V servo-lead conductor reaches the flight controller's 5 V rail. If several do, they are paralleled regulators and the highest-output one carries the entire load.

**Fix:** remove the red conductor from three of the four leads, or from all four given that the FC has its own regulators.

---

## Priority 2: under fifty dollars

### 4. Enable blackbox logging

**Equipment:** a microSD card, or the board's onboard flash if fitted.

This is the highest-value addition to the vehicle. It gives, per flight:

- Per-motor output, which shows asymmetry directly.
- Gyro and accelerometer traces, from which a vibration spectrum can be computed.
- PID term activity, which shows whether the controller is saturating.
- The position estimator's own output against raw GNSS.

**What it decides:** the next fault. The roll divergence documented in [`fault-analysis.md`](fault-analysis.md) took four hypotheses and several crashes; a per-motor vibration spectrum would have shown one arm carrying a peak the other three did not, in one flight.

Once logging exists, fly a hover and look for a peak near 120 Hz, which is rotor frequency at the hover point, on one arm and not the others. That is the signature of exactly the fault that occurred.

### 5. Thrust stand

**Equipment:** a kitchen scale, a length of timber, two clamps. Total cost is whatever the timber costs.

**Procedure:** clamp one arm so the motor thrusts downward onto the scale, or build a simple lever with a known ratio. Command throttle in 10 % steps from the INAV motor test page and record the scale reading at each step. Repeat for all four motors.

**What it gives:**

- Real thrust against throttle, which replaces the Staples correlation with data and validates the whole propulsion model.
- The actual throttle-to-thrust curve, which is not linear and which INAV assumes something about.
- **Arm-to-arm comparison**, which is the direct test that the tachometer could not perform. Four thrust curves that should overlay, and any that does not is a mechanical problem.

That last point is the answer to the lesson in the fault analysis. A tachometer measures the electrical half of the drivetrain, and it does so with the propellers off, which is the condition under which the fault does not exist. A scale under a spinning propeller measures the half that matters, under the load that reveals it.

### 6. Inline wattmeter

**Equipment:** a plug-in RC wattmeter, about fifteen dollars.

Fly a timed hover and record current, voltage and consumed capacity.

**What it decides:** the 13 to 16 minute endurance band collapses to one number, and the lumped drivetrain efficiency assumption of 72 % is replaced by a measurement. Also gives the actual full-throttle current, which is currently an estimate of 60 A sitting exactly at the XT60 rating.

---

## Priority 3: worth doing once the above are done

### 7. Throttle-to-rpm characterisation

**Equipment:** the optical tachometer and reflective tape already used in the fault investigation, shown in [`fault-analysis.md`](fault-analysis.md#the-test-that-produced-the-misleading-answer). The rig is reusable as it stands.

With propellers fitted and the airframe restrained, record rpm at 10 % throttle increments. The one existing data point, 11 300 rpm at 50 % throttle with no propellers, is difficult to reconcile with a 1200 KV motor on 11.1 V: it implies 9.42 V of back-EMF at half throttle, which suggests the throttle-to-duty mapping is far from linear or that the measurement conditions were not what was recorded.

Characterising the curve properly resolves it and gives the mapping the propulsion model currently has to assume.

### 8. Position-hold logging

**Equipment:** blackbox from item 4.

Log a five-minute hold and compute the standard deviation of the position estimate. This turns "roughly 1 to 2 m" into a distribution, and it separates GNSS noise from controller performance, which the current figure cannot.

Pair it with an anemometer reading if one is available, so the hold quality is attributable to a wind condition rather than to "15 to 20 mph" from a weather app.

### 9. Vibration spectrum by arm

**Equipment:** blackbox from item 4.

Hover, then compute an FFT of each gyro axis. Look for peaks at rotor frequency (about 120 Hz at hover) and blade-pass frequency (about 239 Hz). Compare across arms.

Beyond fault detection, this tells you where to place the gyro notch filters, which is currently left at defaults.

---

## Recording results

Add measurements to `docs/measurements.md` with date, instrument and conditions, and update the model constants in `analysis/` rather than editing the prose. The tables regenerate from the scripts.

Predictions that turn out wrong should stay in the repository next to the measurements. The gap between what was predicted and what was measured is the most informative thing a document like this can contain, and deleting it removes the only evidence that the model was ever tested.
