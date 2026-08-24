# Calculations

Every figure quoted in the README is derived here. Three scripts reproduce all of it:

```bash
python3 analysis/performance_model.py   # mass, hover, thrust margin, power, wind, props
python3 analysis/fault_dynamics.py      # roll divergence and actuator bandwidth
python3 analysis/link_budget.py         # ELRS 2.4 GHz control link
```

**Status of these numbers.** The airframe carries no blackbox logging, no telemetry downlink and no current sensing, and the build had no access to a thrust stand or a wattmeter. Nothing below is a measurement. Everything is either a catalogue parameter, a value read from a part, or a calculation from first principles with the assumption stated. [`verification.md`](verification.md) says what each one would cost to confirm.

---

## 1. Mass budget

Component masses are catalogue figures for the exact parts fitted; wiring and hardware is an estimate.

| Item | Mass | Share |
|---|---|---|
| 3S 5000 mAh LiPo | 380 g | 32 % |
| F450 frame kit including PDB | 280 g | 23 % |
| A2212 1200 KV motors, 4 off | 220 g | 18 % |
| Wiring, connectors, mounts, guards | 120 g | 10 % |
| 40 A ESCs with leads, 4 off | 112 g | 9 % |
| 8 x 4.5 propellers, 4 off | 40 g | 3 % |
| MATEK F405-WING V2 | 27 g | 2 % |
| M100-5883 GNSS and compass | 18 g | 2 % |
| ELRS receiver | 3 g | 0 % |
| **All-up weight** | **1200 g** | |

All-up weight of 1.200 kg gives a weight of 11.77 N.

**This is the loosest input in the document and it propagates everywhere:** into thrust-to-weight, into endurance, into the roll inertia used in the fault model. Weighing the vehicle takes five seconds and would remove it. Until then, results that depend strongly on it are quoted across a 1.2 to 1.5 kg band.

---

## 2. Hover point

Two independent methods, cross-checked.

**Momentum theory** treats the rotor as an ideal actuator disc and gives the physical floor on induced power:

```
P_induced = T^1.5 / sqrt(2 · ρ · A)
```

**The Staples static-thrust correlation** is an empirical fit for small fixed-pitch propellers, giving thrust from rotor speed:

```
F [N] = 4.392399e-8 · RPM · (d^3.5 / sqrt(pitch)) · (4.23333e-4 · RPM · pitch − V0)
```

with d and pitch in inches. It was validated before use against published APC data: a 10 x 4.7 at 6000 rpm predicts 4.59 N (468 g) against a measured 460 to 500 g.

For the 8 x 4.5 fitted, disc area is 324 cm² and hover requires 11.77 / 4 = 2.94 N per rotor:

| Quantity | Value |
|---|---|
| Thrust per rotor at hover | 2.94 N (300 g) |
| Rotor speed at hover | 7177 rpm |
| Unloaded rotor speed at 11.1 V | 13 320 rpm |
| Hover as a fraction of unloaded speed | 54 % |
| Blade tip speed | 76.4 m/s (Mach 0.22) |
| Disc loading | 90.7 N/m² (9.3 kg/m²) |
| Induced velocity through the disc | 6.09 m/s |
| Blade Reynolds number at 0.75 R | 69 800 |

**On the figure of merit.** A Reynolds number of 70 000 at the representative blade section is deep in the low-Reynolds regime, where sectional lift-to-drag collapses and profile drag becomes a large share of total power. This is why the model uses a figure of merit of 0.50 rather than the 0.7 to 0.8 typical of full-scale rotors. It is not pessimism; it is the efficiency penalty that every small multirotor pays and cannot design around at this scale.

---

## 3. Thrust margin

The real ceiling is not rotor speed. It is motor current, because the motor reaches its thermal limit long before it reaches its unloaded speed. Inverting the power chain:

```
P_shaft = I · V · η_drivetrain
T_max   = ( P_shaft · FM · sqrt(2 ρ A) )^(2/3)
```

| | Continuous (12 A) | Burst (15 A) |
|---|---|---|
| Thrust per rotor | 5.67 N (579 g) | 6.58 N (671 g) |
| Implied rotor speed | 9967 rpm | 10 736 rpm |
| Back-EMF at that speed | 8.31 V | 8.95 V |
| Total thrust | 22.70 N | 26.34 N |
| Thrust-to-weight ratio | 1.93 | 2.24 |

At 12 A the rotor needs 8.31 V of back-EMF against a pack sitting near 11.1 V under load. Roughly a quarter of the available voltage is never used: the motor runs out of current headroom with rotor-speed headroom still available.

**Sensitivity to the all-up weight estimate:**

| AUW | T/W continuous | T/W burst |
|---|---|---|
| 1.20 kg | 1.93 | 2.24 |
| 1.35 kg | 1.71 | 1.99 |
| 1.50 kg | 1.54 | 1.79 |

A multirotor wants about 2.0. Which row applies is decided by a kitchen scale.

**Finding: the 40 A ESC cannot protect a 12 A motor.** Any condition that overloads a motor, a fouled propeller, a dragging bearing, a bound bell, will take the winding to its thermal limit while the ESC reports 30 % of its own rating. The protective device exists, is correctly rated for itself, and protects nothing downstream. The 40 A parts also carry about 30 g that a correctly sized 20 A ESC would not, on a vehicle where thrust-to-weight is the binding constraint.

---

## 4. Power and endurance

```
P_induced = 2.94^1.5 / sqrt(2 × 1.225 × 0.0324) = 17.9 W  per rotor
P_shaft   = 17.9 / 0.50                          = 35.8 W
P_elec    = 35.8 / 0.72                          = 49.7 W
P_total   = 4 × 49.7 + 5 (avionics)              = 204 W
I_hover   = 204 / 11.1                           = 18.4 A
```

With 80 % of a 5000 mAh pack usable, which is standard LiPo practice:

```
endurance = 4.0 Ah / 18.4 A = 0.218 h = 13.1 min
```

**On the efficiency assumption.** The lumped 72 % drivetrain figure is the loosest number in this section. A detailed motor model using the back-EMF constant and winding resistance suggests something closer to 86 %:

```
Ke = 60 / (2π × 1200)              = 0.00796 V·s/rad
τ  = P_shaft / ω = 35.8 / 751.5    = 0.0476 N·m
I  = τ / Kt = 0.0476 / 0.00796     = 5.98 A  (motor phase current)
V  = Ke·ω + I·R = 5.98 + 0.6       = 6.58 V
copper loss = I²R = 5.98² × 0.1    = 3.58 W  against 35.8 W of shaft power
```

That gives hover current near 15 A and endurance near 16 minutes. **The honest answer is a 13 to 16 minute band**, which brackets the 12 to 18 minutes that F450 builds on this pack typically report. Resolving it into one number needs an inline wattmeter and costs about fifteen dollars.

**Current and rate checks:**

| Quantity | Value | Comment |
|---|---|---|
| Hover discharge rate | 3.7 C | Comfortable for any pack of this class |
| Full-throttle discharge rate | 12 C | Still comfortable |
| Full-throttle current | 60 A | **Exactly the XT60 continuous rating** |
| Motor at hover | 6 A of a 12 A rating | 50 %, which is where a multirotor should sit |

Full throttle drawing the connector's entire continuous rating is acceptable because full throttle on a hovering platform is momentary, and it is the reason the connector is noticeably warm after an aggressive flight.

---

## 5. Wind authority

A quadcopter generates horizontal force by tilting. Required tilt follows from drag against weight:

```
F_drag = 0.5 · ρ · v² · Cd·A          (Cd·A estimated at 0.05 m²)
tilt   = atan(F_drag / W)
T_req  = W / cos(tilt)
```

| Wind | Drag | Tilt | Thrust required | Share of maximum |
|---|---|---|---|---|
| 5 mph | 0.15 N | 0.7° | 11.77 N | 39 % |
| 10 mph | 0.61 N | 3.0° | 11.78 N | 39 % |
| 15 mph | 1.38 N | 6.7° | 11.85 N | 39 % |
| 20 mph | 2.45 N | 11.8° | 12.02 N | 40 % |
| 25 mph | 3.83 N | 18.0° | 12.37 N | 41 % |
| 30 mph | 5.51 N | 25.1° | 12.99 N | 43 % |

Holding position in the 15 to 20 mph wind the flight tests were conducted in requires 11 degrees of tilt and 2 % extra thrust. **Wind was never the limiting factor.** How tightly the vehicle holds a point is set by the bandwidth of its attitude loop, which is section 7.

---

## 6. Propeller trade study

Induced power scales as 1/sqrt(disc area), so a larger disc moving more air more slowly is always more efficient at the same thrust:

| Propeller | Disc area | Hover rpm | Ideal power | Hover current | Endurance |
|---|---|---|---|---|---|
| 8 x 4.5 | 324 cm² | 7177 rpm | 17.9 W | 18.4 A | 13.1 min |
| 9 x 4.5 | 410 cm² | 5840 rpm | 15.9 W | 16.4 A | 14.7 min |
| 10 x 4.5 | 507 cm² | 4857 rpm | 14.3 W | 14.8 A | 16.2 min |

A 10 inch blade would buy about 20 % more endurance. The catch is that 1200 KV is high for a 10 inch blade on 3S: the larger disc demands more torque at lower speed, current rises, and the motor sits closer to the thermal ceiling identified in section 3. The conventional pairings are 1000 KV with 10 x 4.5, or the 1200 KV fitted here with 8 x 4.5. **Changing the propeller alone is not free**, and doing it without changing the motor would trade a thrust-margin problem for a thermal one.

---

## 7. Actuator bandwidth

A control loop is only as fast as the actuator it drives. A zero-order hold at rate *f* contributes an average latency of 1/(2*f*), and latency becomes phase lag in proportion to frequency: φ = 360 · f_signal · τ degrees.

Evaluated at a 20 Hz rate-loop crossover, representative for a 450 mm airframe:

| Protocol | Update rate | ZOH plus ESC latency | Phase cost at 20 Hz |
|---|---|---|---|
| Standard PWM | 50 Hz | 11.00 ms | **79.2°** |
| Standard PWM | 400 Hz | 2.25 ms | 16.2° |
| ONESHOT125 | 2 kHz | 0.55 ms | 4.0° |
| DSHOT600 | 4 kHz | 0.23 ms | 1.6° |
| DSHOT600 | 8 kHz | 0.16 ms | 1.2° |

**Where the rest of the budget goes:**

| Contributor | Phase lag at 20 Hz |
|---|---|
| Gyro low-pass, first order at 90 Hz | 12.5° |
| PID discretisation at 1 kHz | 3.6° |
| Motor protocol at 50 Hz | 79.2° |
| Motor protocol at 400 Hz | 16.2° |

| Configuration | Total lag | Budget |
|---|---|---|
| 50 Hz PWM | 95.3° | 45° |
| 400 Hz PWM | 32.3° | 45° |

**Finding: at 50 Hz the actuator alone exceeds the entire phase margin a stable loop has to spend**, before the PID gains are considered. The symptom would be a vehicle that feels sluggish and starts oscillating as soon as the gains are raised enough to feel responsive.

50 Hz is a servo rate. It is the correct default for the fixed-wing role this board is named for, and the wrong one for a multirotor. The original system description called the motor drive 50 Hz PWM, which may have been loose wording rather than the configuration in use, so this is an action rather than a confirmed defect: **read `motor_pwm_protocol` and `motor_pwm_rate` out of the CLI dump.** If the ESCs accept DSHOT600, moving to it removes this term from the budget entirely and also removes ESC throttle calibration as a source of arm-to-arm asymmetry, which is directly relevant to the fault in section 8.

---

## 8. Roll divergence from a single-arm thrust deficit

Full narrative in [`fault-analysis.md`](fault-analysis.md). The arithmetic:

**Roll inertia,** built up from the mass budget rather than guessed:

| Contribution | Value | Share |
|---|---|---|
| Arm-tip masses, 93 g each at a 159 mm moment arm | 0.00942 kg·m² | 82 % |
| Frame arms, rods about the centre projected at 45° | 0.00101 kg·m² | 9 % |
| Core, battery dominant, 45 mm radius of gyration | 0.00099 kg·m² | 9 % |
| **Total** | **0.01142 kg·m²** | |

In X configuration each motor sits 225 mm from the centre, giving a roll moment arm of 225 · sin45° = 159 mm.

**Divergence.** A thrust deficit of fraction δ on one arm produces an uncorrected angular acceleration α = δ·T·r / I:

| Deficit | Thrust lost | Moment | Angular acceleration | Time to 30° | Time to 90° |
|---|---|---|---|---|---|
| 5 % | 0.15 N | 0.0234 N·m | 117 °/s² | 0.71 s | 1.24 s |
| 10 % | 0.29 N | 0.0468 N·m | 235 °/s² | 0.51 s | 0.87 s |
| 15 % | 0.44 N | 0.0702 N·m | 352 °/s² | 0.41 s | 0.72 s |
| 20 % | 0.59 N | 0.0936 N·m | 470 °/s² | 0.36 s | 0.62 s |
| 30 % | 0.88 N | 0.1404 N·m | 705 °/s² | 0.29 s | 0.51 s |

**Validated against video.** Six takeoff attempts were filmed. Stepping through them at 30 fps gives 0.25 s to 30° of bank and about 0.4 s to 90°, faster than any row above. Inverting the relation, since time to a given angle scales as one over the square root of the deficit, gives 40 to 50 % at hover thrust. Correcting for a takeoff attempt commanding roughly 1.3 times hover thrust, a **30 % deficit reproduces the measurement to within a hundredth of a second**. The failure sat at or beyond the severe end of this table, and the axis was unambiguously roll: a separate clip shows the airframe holding heading for seven seconds at partial throttle, which rules out a yaw torque imbalance.

**Why the tachometer missed it.** Unloaded rotor speed is set by applied voltage and the back-EMF constant and is almost independent of anything downstream of the shaft. Thrust is set by what the propeller disc does with that rotation. A no-load tachometer measures the electrical half of the chain and is blind to the mechanical half. The measured 11 300 rpm implies 9.42 V of back-EMF, which is a statement about the motor's electrical behaviour and says nothing about whether the bell was rigidly coupled to it.

**Why the integrator did not absorb it.** A constant thrust deficit on one arm is exactly what an integral term exists for, and it would have been trimmed out within a second or two of hover. That it was not means the deficit grew with commanded thrust, which is what a bell that tilts further as aerodynamic load increases does. The failure was a loss of control effectiveness rather than a fixed disturbance, and no amount of integral gain recovers from that.

**The signature that would have found it.** A wobbling bell forces the airframe at rotor frequency: 7177 rpm is 119.6 Hz, with a 239 Hz blade-pass component. That lands just above INAV's default 90 Hz gyro low-pass corner, attenuated but not removed, and feeds into the accelerometer that anchors the attitude estimate. A per-motor vibration spectrum from blackbox logging would have shown one arm carrying a peak the other three did not.

---

## 9. Control link budget

Standard one-way budget:

```
P_rx   = P_tx + G_tx + G_rx − FSPL(d, f) − L_blockage
margin = P_rx − S_rx
FSPL(dB) = 20·log10(d_km) + 20·log10(f_MHz) + 32.44
```

| Parameter | Value |
|---|---|
| Carrier | 2440 MHz |
| Transmit power | 150 mW (21.8 dBm) |
| Antenna gain, each end | 2.0 dBi |
| Packet rate | 150 Hz |
| Receiver sensitivity at that rate | −108 dBm |
| Required fade margin | 10 dB |

**Margin against distance:**

| Antenna scenario | 100 m | 250 m | 500 m | 1 km | 2 km |
|---|---|---|---|---|---|
| Mast, clear line of sight (V1) | 54 dB | 46 dB | 40 dB | 34 dB | 28 dB |
| Underside, favourable attitude (V2) | 48 dB | 40 dB | 34 dB | 28 dB | 22 dB |
| Underside, airframe in the path (V2) | 39 dB | 31 dB | 25 dB | 19 dB | 13 dB |
| Underside, deep null (V2, worst) | 29 dB | 21 dB | 15 dB | 9 dB | 3 dB |

**Range at a 10 dB fade margin:**

| Scenario | Range | Relative to V1 |
|---|---|---|
| Mast, clear line of sight (V1) | 15.1 km | 100 % |
| Underside, favourable attitude (V2) | 7.6 km | 50 % |
| Underside, airframe in the path (V2) | 2.7 km | 18 % |
| Underside, deep null (V2, worst) | 849 m | 6 % |

The antenna relocation costs between half and 94 % of theoretical range depending on vehicle attitude, and it does not matter: every flight in this project has been line-of-sight inside a few hundred metres, where even the worst-case null holds 29 dB of margin. **The relocation spends margin the vehicle was never using**, which is what makes it a good trade rather than merely a convenient one.

**Packet rate as the pilot's lever:**

| Rate | Sensitivity | Range with 15 dB blockage | Control latency |
|---|---|---|---|
| 50 Hz | −112 dBm | 4253 m | 20.0 ms |
| 150 Hz | −108 dBm | 2683 m | 6.7 ms |
| 250 Hz | −105 dBm | 1900 m | 4.0 ms |
| 500 Hz | −102 dBm | 1345 m | 2.0 ms |

Dropping from 500 Hz to 50 Hz buys 10 dB, roughly a factor of three in range, and costs 18 ms of stick-to-motor latency. For a line-of-sight GPS platform that is a trade worth making. For a racing quad it is not. 150 Hz is the sensible middle and is what is flown.

**Caveat.** Free-space path loss is optimistic near the ground, where reflection nulls and Fresnel-zone obstruction dominate below roughly 10 m altitude, and this budget does not model them. The comparison between the two antenna positions still holds, because both suffer those effects equally.

---

## 10. GNSS position accuracy

Absolute horizontal accuracy from dilution of precision:

```
σ_horizontal ≈ HDOP × UERE
```

With the observed HDOP of 1.8 and a user-equivalent range error of 3 to 5 m for single-frequency GNSS, absolute 1σ error is 5.4 to 9.0 m. The observed position hold is 1 to 2 m, which is far tighter.

There is no contradiction, and understanding why matters. **Position hold is a relative problem, not an absolute one.** The GNSS error budget is dominated by ionospheric delay, satellite clock and ephemeris terms, all of which drift slowly and are common-mode over the minutes a hold lasts. The estimator only has to reject short-term noise, which is a much smaller quantity, typically well under a metre. INAV additionally fuses the barometer and accelerometer into the position estimate, which smooths further.

Quoting a hold figure as though it were absolute accuracy is a common error in hobbyist write-ups. The 1 to 2 m figure here is relative, over a few minutes, and is not a claim about where the vehicle thinks it is on the Earth.
