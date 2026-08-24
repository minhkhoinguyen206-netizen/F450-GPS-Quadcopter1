#!/usr/bin/env python3
"""
=============================================================================
 F450 GPS Quadcopter: roll divergence model and actuator bandwidth budget
=============================================================================

 Two questions this file answers with numbers rather than narrative.

 PART A. The vehicle tipped onto one side within about a second of applying
 throttle, repeatably, with no fault flag from the flight controller. How
 large a thrust deficit on one arm does that timescale imply, and why did a
 no-load tachometer reading of 11,300 rpm on all four motors fail to reveal
 it?

 PART B. How much phase margin does the motor output protocol cost? A control
 loop can only be as fast as the actuator it drives, and a fixed-wing-oriented
 default of 50 Hz standard PWM is a very different machine from DSHOT600.

 Everything here is a model. Nothing was instrumented in flight: the vehicle
 has no blackbox logging fitted, which is itself one of the findings.

 Author : Nguyen Minh Khoi
 License: MIT
=============================================================================
"""

import math
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pathlib import Path

OUT = Path(__file__).resolve().parent / "figures"
OUT.mkdir(parents=True, exist_ok=True)

G = 9.80665
SEP = "-" * 76


def hdr(t):
    print("\n" + "=" * 76)
    print(" " + t)
    print("=" * 76)


# =============================================================================
# PART A. ROLL DIVERGENCE FROM A SINGLE-ARM THRUST DEFICIT
# =============================================================================
AUW = 1.20               # kg, from performance_model.py mass budget
ARM_R = 0.225            # m, motor radius (450 mm motor-to-motor)
ROLL_ARM = ARM_R * math.sin(math.radians(45))   # X configuration

# Roll inertia, built up from the mass budget rather than guessed as a lump.
M_ARM_TIP = (220 + 40 + 112) / 4 / 1000.0       # motor + prop + ESC, per arm
M_FRAME_ARM = 0.030                              # one frame arm
M_CORE = (380 + 27 + 18 + 3 + 60) / 1000.0       # battery, FC, GNSS, RX, plate
R_GYR_CORE = 0.045                               # m, core radius of gyration

I_tips = 4 * M_ARM_TIP * ROLL_ARM ** 2
I_arms = 4 * M_FRAME_ARM * ARM_R ** 2 / 6.0      # rod about end, projected 45 deg
I_core = M_CORE * R_GYR_CORE ** 2
I_ROLL = I_tips + I_arms + I_core

T_HOVER = AUW * G / 4.0


def divergence(deficit_frac, i_roll=I_ROLL):
    """Uncorrected angular acceleration and time to a given bank angle."""
    dT = deficit_frac * T_HOVER
    moment = dT * ROLL_ARM
    alpha = moment / i_roll
    return moment, alpha


def time_to_angle(alpha, deg):
    return math.sqrt(2 * math.radians(deg) / alpha) if alpha > 0 else float("inf")


hdr("A1. ROLL INERTIA")
print(f"   Motor + prop + ESC per arm           {M_ARM_TIP*1000:8.0f} g")
print(f"   Roll moment arm (X config)           {ROLL_ARM*1000:8.0f} mm")
print(SEP)
print(f"   Arm tip masses                       {I_tips:8.5f} kg m2   "
      f"{I_tips/I_ROLL*100:4.0f} %")
print(f"   Frame arms                           {I_arms:8.5f} kg m2   "
      f"{I_arms/I_ROLL*100:4.0f} %")
print(f"   Core (battery dominates)             {I_core:8.5f} kg m2   "
      f"{I_core/I_ROLL*100:4.0f} %")
print(f"   Roll inertia, total                  {I_ROLL:8.5f} kg m2")

hdr("A2. HOW FAST DOES IT FALL OVER")
print(f"   Hover thrust per rotor               {T_HOVER:8.2f} N")
print(SEP)
print(f"   {'Deficit':>10}{'Thrust lost':>14}{'Moment':>12}{'Ang. accel':>14}"
      f"{'t to 30 deg':>14}")
for d in (0.05, 0.10, 0.15, 0.20, 0.30):
    m, a = divergence(d)
    print(f"   {d*100:8.0f} %{d*T_HOVER:11.2f} N{m:11.4f} Nm"
          f"{math.degrees(a):11.0f} d/s2{time_to_angle(a, 30):11.2f} s")
print(SEP)
print("   The observed failure was a tip-over in roughly one second. A deficit")
print("   anywhere between 10 % and 30 % on one arm reproduces that, uncorrected.")

hdr("A3. WHY THE TACHOMETER SAID EVERYTHING WAS FINE")
KV = 1200.0
V_PACK = 11.1
rpm_measured = 11300.0
print(f"   Measured, all four motors, no props  {rpm_measured:8.0f} rpm")
print(f"   Back-EMF that speed implies          {rpm_measured/KV:8.2f} V")
print(SEP)
print("   Unloaded rotor speed is set by applied voltage and the back-EMF")
print("   constant. It is almost independent of anything downstream of the")
print("   shaft. Thrust is set by what the propeller disc does with that")
print("   rotation: whether it stays perpendicular to the shaft, whether it")
print("   stays in one plane, whether the bell is rigidly coupled.")
print()
print("   A no-load tachometer therefore measures the electrical half of the")
print("   chain and is blind to the mechanical half. Motor 2 passed the test")
print("   it was given. The test was the wrong test.")
print()
print("   A constant thrust deficit would also have been trimmed out by the")
print("   roll integrator within a second or two of hover. That it was not")
print("   says the deficit grew with commanded thrust, which is what a bell")
print("   that tilts further as aerodynamic load increases would do. The fault")
print("   was a loss of control effectiveness, not a fixed disturbance, and no")
print("   amount of integral gain recovers from that.")

hdr("A4. THE SIGNATURE THAT WOULD HAVE FOUND IT IN MINUTES")
rpm_hover = 7177.0
f_rotor = rpm_hover / 60.0
print(f"   Rotor frequency at hover             {f_rotor:8.1f} Hz")
print(f"   Blade-pass frequency (2 blades)      {2*f_rotor:8.1f} Hz")
print(f"   INAV default gyro low-pass           {90:8.0f} Hz")
print(SEP)
print("   A wobbling bell forces the airframe at rotor frequency. At hover that")
print(f"   lands at about {f_rotor:.0f} Hz, just above the default gyro filter corner,")
print("   where it is attenuated but not removed, and it feeds straight into")
print("   the accelerometer that anchors the attitude estimate.")
print()
print("   With blackbox logging enabled, a per-motor vibration spectrum would")
print("   have shown one arm carrying a peak the other three did not. That is a")
print("   five-minute diagnosis instead of a four-hypothesis elimination. Fitting")
print("   logging is the highest-value change on the roadmap.")


# =============================================================================
# PART B. ACTUATOR BANDWIDTH AND PHASE BUDGET
# =============================================================================
PROTOCOLS = {
    "Standard PWM, 50 Hz":   (50.0,   1.0),
    "Standard PWM, 400 Hz":  (400.0,  1.0),
    "ONESHOT125, 2 kHz":     (2000.0, 0.3),
    "DSHOT600, 4 kHz":       (4000.0, 0.1),
    "DSHOT600, 8 kHz":       (8000.0, 0.1),
}
F_CROSSOVER = 20.0       # Hz, representative rate-loop crossover for this size


def latency_ms(rate_hz, esc_ms):
    """Zero-order-hold delay plus ESC interpretation delay."""
    return 1000.0 / (2.0 * rate_hz) + esc_ms


def phase_deg(tau_ms, f_hz=F_CROSSOVER):
    return 360.0 * f_hz * tau_ms / 1000.0


hdr("B1. ACTUATOR LATENCY AND PHASE COST")
print(f"   Evaluated at a {F_CROSSOVER:.0f} Hz rate-loop crossover, typical for a")
print("   450 mm airframe. A healthy loop wants about 45 degrees of phase margin")
print("   in total, shared between the actuator, the gyro filters and the PID.")
print(SEP)
print(f"   {'Protocol':<24}{'Update':>10}{'ZOH+ESC':>12}{'Phase cost':>14}")
for name, (rate, esc) in PROTOCOLS.items():
    tau = latency_ms(rate, esc)
    print(f"   {name:<24}{rate:8.0f} Hz{tau:9.2f} ms{phase_deg(tau):11.1f} deg")
print(SEP)
tau50 = latency_ms(*PROTOCOLS["Standard PWM, 50 Hz"])
tau400 = latency_ms(*PROTOCOLS["Standard PWM, 400 Hz"])
print(f"   FINDING: at 50 Hz the actuator alone eats {phase_deg(tau50):.0f} degrees of phase,")
print("   more than the entire margin a stable loop has to spend. 50 Hz is a")
print("   servo rate, inherited from the fixed-wing heritage of this board's")
print(f"   naming, and it is not a multirotor rate. At 400 Hz the cost falls to")
print(f"   {phase_deg(tau400):.0f} degrees, which is affordable. DSHOT makes it negligible.")
print()
print("   ACTION: confirm motor_pwm_protocol and motor_pwm_rate in the CLI dump.")
print("   If the ESCs accept it, DSHOT600 removes this term from the budget")
print("   entirely and also removes ESC calibration as a source of asymmetry")
print("   between arms, which is directly relevant to the fault in Part A.")

hdr("B2. WHERE THE REST OF THE PHASE BUDGET GOES")
GYRO_LPF_HZ = 90.0
PID_RATE_HZ = 1000.0
phase_gyro = math.degrees(math.atan2(F_CROSSOVER, GYRO_LPF_HZ))
phase_pid = phase_deg(1000.0 / (2 * PID_RATE_HZ))
rows = [
    ("Gyro low-pass, first order at 90 Hz", phase_gyro),
    ("PID loop discretisation at 1 kHz", phase_pid),
    ("Motor protocol at 50 Hz", phase_deg(tau50)),
    ("Motor protocol at 400 Hz", phase_deg(tau400)),
]
for n, v in rows:
    print(f"   {n:<44}{v:8.1f} deg")
print(SEP)
total50 = phase_gyro + phase_pid + phase_deg(tau50)
total400 = phase_gyro + phase_pid + phase_deg(tau400)
print(f"   Total lag with 50 Hz PWM             {total50:8.1f} deg")
print(f"   Total lag with 400 Hz PWM            {total400:8.1f} deg")
print(f"   Budget available                     {45.0:8.1f} deg")
print(SEP)
print("   The 50 Hz configuration is over budget before the PID gains are even")
print("   considered, which would show up as a vehicle that feels sluggish and")
print("   oscillates when the gains are raised far enough to feel responsive.")


# =============================================================================
# FIGURES
# =============================================================================
def _style(ax, title, xlabel, ylabel):
    ax.grid(True, ls=":", lw=0.6, alpha=0.55)
    ax.set_title(title, fontsize=12, fontweight="bold", pad=12)
    ax.set_xlabel(xlabel, fontsize=10)
    ax.set_ylabel(ylabel, fontsize=10)
    ax.tick_params(labelsize=9)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)


def plot_divergence():
    t = np.linspace(0, 1.2, 400)
    fig, ax = plt.subplots(figsize=(9, 5.2), dpi=200)
    for d, col in zip((0.05, 0.10, 0.20, 0.30),
                      ("#1f8a55", "#0b6e99", "#e07b39", "#c0392b")):
        _, a = divergence(d)
        ax.plot(t, np.degrees(0.5 * a * t ** 2), lw=2.2, color=col,
                label=f"{d*100:.0f} % thrust deficit on one arm")
    ax.axhline(30, color="#555", ls="--", lw=1.2)
    ax.text(0.02, 32, "30 degrees: recovery is unlikely below this altitude",
            fontsize=8.5, color="#555")
    ax.axhline(90, color="#555", ls="-.", lw=1.0)
    ax.text(0.02, 92, "90 degrees: on its side", fontsize=8.5, color="#555")
    _style(ax, "Uncorrected roll divergence, one arm down on thrust",
           "Time from throttle-up (s)", "Bank angle (degrees)")
    ax.set_ylim(0, 130)
    ax.set_xlim(0, 1.2)
    ax.legend(fontsize=9, loc="lower right", framealpha=0.95)
    fig.tight_layout()
    fig.savefig(OUT / "roll_divergence.png")
    plt.close(fig)


def plot_phase_budget():
    names = list(PROTOCOLS.keys())[::-1]
    vals = [phase_deg(latency_ms(*PROTOCOLS[n])) for n in names]
    colors = ["#c0392b" if v > 45 else "#e07b39" if v > 20 else "#1f8a55"
              for v in vals]
    fig, ax = plt.subplots(figsize=(9, 4.4), dpi=200)
    bars = ax.barh(names, vals, color=colors, height=0.6)
    ax.axvline(45, color="#c0392b", ls="--", lw=1.5)
    ax.text(46, -0.42, "45 deg: the whole phase margin", color="#c0392b",
            fontsize=9, fontweight="bold")
    for b, v in zip(bars, vals):
        ax.text(v + 1.2, b.get_y() + b.get_height() / 2, f"{v:.1f} deg",
                va="center", fontsize=9)
    ax.set_xlabel(f"Phase lag contributed at a {F_CROSSOVER:.0f} Hz crossover (degrees)",
                  fontsize=10)
    ax.set_title("What the motor output protocol costs the attitude loop",
                 fontsize=12, fontweight="bold", pad=12)
    ax.grid(axis="x", ls=":", lw=0.6, alpha=0.5)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.set_xlim(0, 95)
    fig.tight_layout()
    fig.savefig(OUT / "phase_budget.png")
    plt.close(fig)


if __name__ == "__main__":
    plot_divergence()
    plot_phase_budget()
    print(f"\nFigures written to {OUT}")
