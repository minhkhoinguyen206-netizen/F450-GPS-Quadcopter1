#!/usr/bin/env python3
"""
=============================================================================
 F450 GPS Quadcopter: propulsion, power and endurance model
=============================================================================

 Predicts hover point, thrust margin, current draw and endurance for the
 as-built vehicle, and quantifies the wind authority that the observed
 position-hold performance implies.

 These are ANALYTICAL PREDICTIONS. No thrust stand, wattmeter or logging
 telemetry was available during the build, so nothing here is a measurement.
 docs/verification.md lists the instrumentation that would close each gap.

 Two independent methods are used for thrust and cross-checked:

   1. Momentum theory, which bounds the induced power of an ideal actuator
      disc and gives the physical floor on hover power.
   2. The Staples static-thrust correlation, an empirical fit widely used for
      small fixed-pitch propellers, which gives thrust as a function of RPM.

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

# =============================================================================
# 1. VEHICLE PARAMETERS
# =============================================================================
# Mass budget, in grams. Component masses are catalogue values for the exact
# parts fitted; wiring and hardware is an estimate. Total should be confirmed
# on a kitchen scale, which is the single cheapest measurement in this file.
MASS_BUDGET = {
    "F450 frame kit incl. integrated PDB": 280,
    "A2212 1200 KV motors (4)":            220,
    "40 A ESCs with leads (4)":            112,
    "8045 propellers (4)":                  40,
    "MATEK F405-WING V2":                   27,
    "M100-5883 GNSS + compass":             18,
    "ELRS 2.4 GHz receiver":                 3,
    "3S 5000 mAh LiPo":                    380,
    "Wiring, connectors, mounts, guards":  120,
}

PROP_D_IN = 8.0          # in    propeller diameter
PROP_P_IN = 4.5          # in    propeller pitch
N_ROTORS = 4
ARM_R = 0.225            # m     motor radius from centre (450 mm motor-to-motor)

KV = 1200.0              # rpm/V  A2212/11T
CELLS = 3
V_CELL_NOM = 3.7         # V     nominal
V_CELL_FULL = 4.2        # V     fully charged
BATT_CAPACITY_AH = 5.0
BATT_USABLE = 0.80       # keep 20 % in reserve, standard LiPo practice
BATT_R_INT = 0.010       # ohm   pack internal resistance, estimated

ESC_RATED_A = 40.0       # A     ESC continuous rating, from the case marking
MOTOR_CONT_A = 12.0      # A     A2212/11T continuous rating, catalogue
MOTOR_BURST_A = 15.0     # A     short-duration burst
XT60_RATED_A = 60.0

RHO = 1.225              # kg/m3 sea-level air density
G = 9.80665

FIGURE_OF_MERIT = 0.50   # hover efficiency of a small low-Reynolds rotor
ETA_MOTOR_ESC = 0.72     # combined electrical-to-shaft efficiency
P_AVIONICS = 5.0         # W     FC, GNSS, receiver, LEDs

V_NOM = CELLS * V_CELL_NOM
AUW_KG = sum(MASS_BUDGET.values()) / 1000.0
W_N = AUW_KG * G
DISC_A = math.pi * (PROP_D_IN * 0.0254) ** 2 / 4.0

SEP = "-" * 76


def hdr(t):
    print("\n" + "=" * 76)
    print(" " + t)
    print("=" * 76)


# =============================================================================
# 2. THRUST MODELS
# =============================================================================
def thrust_staples(rpm, d_in=PROP_D_IN, p_in=PROP_P_IN, v0=0.0):
    """
    Static thrust of a fixed-pitch propeller, Staples correlation.

        F [N] = 4.392399e-8 * RPM * (d^3.5 / sqrt(pitch))
                * (4.23333e-4 * RPM * pitch - V0)

    with d and pitch in inches and V0 the free-stream velocity in m/s.
    Validated against published APC data: a 10x4.7 at 6000 rpm predicts
    4.59 N (468 g) against a measured 460-500 g.
    """
    rpm = np.asarray(rpm, dtype=float)
    return (4.392399e-8 * rpm * (d_in ** 3.5 / math.sqrt(p_in))
            * (4.23333e-4 * rpm * p_in - v0))


def rpm_for_thrust(target_n, d_in=PROP_D_IN, p_in=PROP_P_IN):
    """Invert the static-thrust correlation. Static form is quadratic in RPM."""
    k = 4.392399e-8 * (d_in ** 3.5 / math.sqrt(p_in)) * 4.23333e-4 * p_in
    return math.sqrt(target_n / k)


def induced_power(thrust_n, area=DISC_A):
    """Momentum-theory induced power of an ideal actuator disc in hover."""
    return thrust_n ** 1.5 / math.sqrt(2.0 * RHO * area)


def electrical_power(thrust_n, area=DISC_A):
    """Per-rotor electrical power including rotor and drivetrain losses."""
    return induced_power(thrust_n, area) / FIGURE_OF_MERIT / ETA_MOTOR_ESC


# =============================================================================
# 3. MASS AND HOVER POINT
# =============================================================================
hdr("1. MASS BUDGET")
for k, v in sorted(MASS_BUDGET.items(), key=lambda kv: -kv[1]):
    print(f"   {k:<40}{v:6.0f} g   {v/sum(MASS_BUDGET.values())*100:5.1f} %")
print(SEP)
print(f"   {'All-up weight (AUW), estimated':<40}{AUW_KG*1000:6.0f} g")
print(f"   {'Weight':<40}{W_N:6.2f} N")

hdr("2. HOVER POINT")
t_hover = W_N / N_ROTORS
rpm_hover = rpm_for_thrust(t_hover)
rpm_noload = KV * V_NOM
tip_speed = math.pi * (PROP_D_IN * 0.0254) * rpm_hover / 60.0
disc_loading = W_N / (N_ROTORS * DISC_A)
v_induced = math.sqrt(t_hover / (2 * RHO * DISC_A))

print(f"   Thrust required per rotor            {t_hover:8.2f} N  ({t_hover/G*1000:.0f} g)")
print(f"   Rotor speed at hover                 {rpm_hover:8.0f} rpm")
print(f"   Unloaded rotor speed at {V_NOM:.1f} V       {rpm_noload:8.0f} rpm")
print(f"   Hover speed as fraction of unloaded  {rpm_hover/rpm_noload*100:8.1f} %")
print(f"   Blade tip speed                      {tip_speed:8.1f} m/s   "
      f"(Mach {tip_speed/343:.2f})")
print(f"   Disc loading                         {disc_loading:8.1f} N/m2 "
      f"({disc_loading/G:.1f} kg/m2)")
print(f"   Induced velocity through the disc    {v_induced:8.2f} m/s")

# Reynolds number at 75 % blade radius, which justifies the figure of merit
chord = 0.018            # m, representative 8045 chord at 75 % R
v_75 = 0.75 * tip_speed
re_75 = RHO * v_75 * chord / 1.81e-5
print(f"   Blade Reynolds number at 0.75 R      {re_75:8.0f}")
print(SEP)
print("   Re below ~1e5 is the low-Reynolds regime where sectional lift-to-drag")
print("   collapses. That is why a figure of merit of 0.50 is used here rather")
print("   than the 0.7-0.8 typical of full-scale rotors.")

# =============================================================================
# 4. THRUST MARGIN
# =============================================================================
hdr("3. THRUST MARGIN AND CONTROL AUTHORITY")


def thrust_from_current(i_a, v=V_NOM):
    """
    Invert the power chain to get the thrust a motor can produce at a given
    electrical current. This, not rotor speed, is the real ceiling: the motor
    reaches its thermal limit long before it reaches its unloaded speed.
    """
    p_shaft = i_a * v * ETA_MOTOR_ESC
    return (p_shaft * FIGURE_OF_MERIT * math.sqrt(2.0 * RHO * DISC_A)) ** (2.0 / 3.0)


t_cont = thrust_from_current(MOTOR_CONT_A)
t_burst = thrust_from_current(MOTOR_BURST_A)
rpm_cont = rpm_for_thrust(t_cont)
rpm_burst = rpm_for_thrust(t_burst)
twr_cont = N_ROTORS * t_cont / W_N
twr_burst = N_ROTORS * t_burst / W_N

print(f"   {'':<36}{'continuous':>13}{'burst':>13}")
print(f"   {'Motor current':<36}{MOTOR_CONT_A:10.1f} A{MOTOR_BURST_A:12.1f} A")
print(f"   {'Thrust per rotor':<36}{t_cont:10.2f} N{t_burst:12.2f} N")
print(f"   {'':<36}{t_cont/G*1000:10.0f} g{t_burst/G*1000:12.0f} g")
print(f"   {'Implied rotor speed':<36}{rpm_cont:10.0f}  {rpm_burst:11.0f}")
print(f"   {'Back-EMF voltage at that speed':<36}{rpm_cont/KV:10.2f} V{rpm_burst/KV:12.2f} V")
print(f"   {'Total thrust':<36}{N_ROTORS*t_cont:10.2f} N{N_ROTORS*t_burst:12.2f} N")
print(f"   {'Thrust-to-weight ratio':<36}{twr_cont:10.2f}  {twr_burst:11.2f}")
t_max, rpm_max = t_burst, rpm_burst
print(SEP)
print("   The ceiling is thermal, not kinematic. At 12 A the rotor turns about")
print(f"   {rpm_cont:.0f} rpm, which needs {rpm_cont/KV:.1f} V of back-EMF against a pack that")
print("   sits near 11.1 V under load. The motor runs out of current headroom")
print("   with rotor-speed headroom still on the table.")
print()
print("   FINDING: the 40 A ESC cannot protect a 12 A motor. Any condition that")
print("   overloads a motor, a fouled prop, a seized bearing, a bound bell, will")
print("   cook the winding long before the ESC's own limit engages. The ESC is")
print("   sized for a motor three times larger than the one fitted.")
print()
print(f"   Thrust-to-weight is also sensitive to the all-up weight estimate:")
for m in (1.2, 1.35, 1.5):
    print(f"      at {m:.2f} kg AUW: T/W = {N_ROTORS*t_cont/(m*G):.2f} continuous, "
          f"{N_ROTORS*t_burst/(m*G):.2f} burst")
print("   A multirotor wants about 2.0. Weighing the vehicle is the cheapest")
print("   measurement in this document and it decides which row above applies.")

# =============================================================================
# 5. POWER AND ENDURANCE
# =============================================================================
hdr("4. POWER AND ENDURANCE")
p_ind = induced_power(t_hover)
p_shaft = p_ind / FIGURE_OF_MERIT
p_elec = p_shaft / ETA_MOTOR_ESC
p_total = N_ROTORS * p_elec + P_AVIONICS
i_hover = p_total / V_NOM
usable_ah = BATT_CAPACITY_AH * BATT_USABLE
endurance_min = usable_ah / i_hover * 60.0

print(f"   Induced power per rotor (ideal)      {p_ind:8.1f} W")
print(f"   Shaft power per rotor (FM {FIGURE_OF_MERIT:.2f})       {p_shaft:8.1f} W")
print(f"   Electrical power per rotor           {p_elec:8.1f} W")
print(f"   Total electrical power at hover      {p_total:8.1f} W")
print(f"   Hover current at {V_NOM:.1f} V              {i_hover:8.1f} A")
print(f"   Usable capacity ({BATT_USABLE*100:.0f} % of {BATT_CAPACITY_AH:.1f} Ah)   "
      f"{usable_ah:8.1f} Ah")
print(f"   Predicted hover endurance            {endurance_min:8.1f} min")
print(SEP)
print(f"   Discharge rate at hover              {i_hover/BATT_CAPACITY_AH:8.1f} C")
i_full = MOTOR_BURST_A * N_ROTORS
print(f"   Discharge rate at full throttle      {i_full/BATT_CAPACITY_AH:8.1f} C")
print(f"   XT60 connector rating                {XT60_RATED_A:8.1f} A "
      f"({i_full/XT60_RATED_A*100:.0f} % used at full throttle)")
print(f"   ESC rating vs peak motor current     {ESC_RATED_A:8.1f} A "
      f"({MOTOR_BURST_A/ESC_RATED_A*100:.0f} % used)")
print(SEP)
print(SEP)
print("   Full throttle draws essentially the XT60's entire continuous rating.")
print("   Acceptable because full throttle is momentary, but it is the reason")
print("   the connector runs warm after an aggressive flight.")

# =============================================================================
# 6. WIND AUTHORITY
# =============================================================================
hdr("5. WIND AUTHORITY")
CD_A = 0.05 * 1.0        # m2, frontal area x drag coefficient, estimated
print(f"   Assumed drag area (Cd x A)           {CD_A:8.3f} m2")
print(SEP)
print(f"   {'Wind':>10}{'Drag':>10}{'Tilt':>10}{'Thrust need':>14}{'of max':>10}")
for mph in (5, 10, 15, 20, 25, 30):
    v = mph * 0.44704
    drag = 0.5 * RHO * v ** 2 * CD_A
    tilt = math.degrees(math.atan2(drag, W_N))
    t_req = W_N / math.cos(math.radians(tilt))
    print(f"   {mph:6d} mph{drag:9.2f} N{tilt:9.1f} deg{t_req:11.2f} N"
          f"{t_req/(N_ROTORS*t_max)*100:9.1f} %")
print(SEP)
print("   The observed 1-2 m position hold in 15-20 mph wind requires only about")
print("   an 11 degree tilt and 2 % extra thrust, which the vehicle has in hand.")
print("   Wind rejection was never the limiting factor; actuator bandwidth is.")

# =============================================================================
# 7. PROPELLER TRADE STUDY
# =============================================================================
hdr("6. PROPELLER TRADE STUDY")
print(f"   {'Prop':>10}{'Disc area':>12}{'Hover rpm':>12}{'Ideal P':>10}"
      f"{'Hover I':>10}{'Endurance':>12}")
for d, p in ((8.0, 4.5), (9.0, 4.5), (10.0, 4.5)):
    area = math.pi * (d * 0.0254) ** 2 / 4.0
    rpm_h = rpm_for_thrust(t_hover, d, p)
    pi_ = induced_power(t_hover, area)
    pe = pi_ / FIGURE_OF_MERIT / ETA_MOTOR_ESC
    tot = N_ROTORS * pe + P_AVIONICS
    cur = tot / V_NOM
    end = usable_ah / cur * 60.0
    print(f"   {int(d)}x{p:<7.1f}{area*1e4:9.0f} cm2{rpm_h:11.0f}{pi_:9.1f} W"
          f"{cur:9.1f} A{end:10.1f} min")
print(SEP)
print("   A 10 inch prop cuts induced power by about 20 % at the same thrust,")
print("   because induced power scales as 1/sqrt(disc area). The catch is that")
print("   1200 KV is high for a 10 inch blade on 3S: the motor would run closer")
print("   to its thermal limit. The conventional pairing is 1000 KV with 10x4.5,")
print("   or the 1200 KV fitted here with 8x4.5. Changing prop alone is not free.")


# =============================================================================
# 8. FIGURES
# =============================================================================
def _style(ax, title, xlabel, ylabel):
    ax.grid(True, ls=":", lw=0.6, alpha=0.55)
    ax.set_title(title, fontsize=12, fontweight="bold", pad=12)
    ax.set_xlabel(xlabel, fontsize=10)
    ax.set_ylabel(ylabel, fontsize=10)
    ax.tick_params(labelsize=9)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)


def plot_thrust_curve():
    rpm = np.linspace(2000, 12000, 500)
    t = thrust_staples(rpm)
    fig, ax = plt.subplots(figsize=(9, 5.2), dpi=200)
    ax.plot(rpm, t / G * 1000, lw=2.4, color="#0b6e99", label="8x4.5 static thrust")
    ax.axhline(t_hover / G * 1000, color="#1f8a55", ls="--", lw=1.4)
    ax.plot([rpm_hover], [t_hover / G * 1000], "o", ms=9, color="#1f8a55", zorder=5)
    ax.annotate(f"hover\n{rpm_hover:.0f} rpm, {t_hover/G*1000:.0f} g",
                (rpm_hover, t_hover / G * 1000), textcoords="offset points",
                xytext=(12, -34), fontsize=9, color="#1f8a55")
    ax.plot([rpm_cont], [t_cont / G * 1000], "o", ms=9, color="#e07b39", zorder=5)
    ax.annotate(f"12 A continuous limit\n{rpm_cont:.0f} rpm, {t_cont/G*1000:.0f} g",
                (rpm_cont, t_cont / G * 1000), textcoords="offset points",
                xytext=(-150, -6), fontsize=9, color="#e07b39")
    ax.plot([rpm_burst], [t_burst / G * 1000], "o", ms=9, color="#c0392b", zorder=5)
    ax.annotate(f"15 A burst\n{rpm_burst:.0f} rpm, {t_burst/G*1000:.0f} g",
                (rpm_burst, t_burst / G * 1000), textcoords="offset points",
                xytext=(-88, 14), fontsize=9, color="#c0392b")
    ax.axvspan(rpm_hover, rpm_burst, color="#f2c744", alpha=0.16,
               label="usable control band")
    _style(ax, "Static thrust of one rotor, and where the vehicle actually sits",
           "Rotor speed (rpm)", "Thrust per rotor (g)")
    ax.legend(fontsize=9, loc="upper left", framealpha=0.95)
    fig.tight_layout()
    fig.savefig(OUT / "thrust_curve.png")
    plt.close(fig)


def plot_endurance():
    masses = np.linspace(0.9, 1.8, 200)
    ends, twrs = [], []
    for m in masses:
        th = m * G / N_ROTORS
        pe = electrical_power(th)
        tot = N_ROTORS * pe + P_AVIONICS
        ends.append(usable_ah / (tot / V_NOM) * 60.0)
        twrs.append(N_ROTORS * t_max / (m * G))
    fig, ax = plt.subplots(figsize=(9, 5.2), dpi=200)
    ax.plot(masses, ends, lw=2.4, color="#0b6e99", label="Predicted hover endurance")
    ax.axvline(AUW_KG, color="#c0392b", ls="--", lw=1.4)
    ax.annotate(f"as built\n{AUW_KG:.2f} kg, {endurance_min:.1f} min",
                (AUW_KG, endurance_min), textcoords="offset points",
                xytext=(10, 18), fontsize=9, color="#c0392b")
    _style(ax, "Endurance against all-up weight, 4.0 Ah usable",
           "All-up weight (kg)", "Hover endurance (min)")
    ax2 = ax.twinx()
    ax2.plot(masses, twrs, lw=1.6, ls=":", color="#5b2d8e")
    ax2.axhline(2.0, color="#5b2d8e", lw=1.0, ls="-.")
    ax2.set_ylabel("Thrust-to-weight ratio", fontsize=10, color="#5b2d8e")
    ax2.tick_params(labelsize=9, colors="#5b2d8e")
    ax2.text(1.72, 2.05, "T/W = 2.0 target", fontsize=8, color="#5b2d8e", ha="right")
    ax2.spines["top"].set_visible(False)
    ax.legend(fontsize=9, loc="upper right", framealpha=0.95)
    fig.tight_layout()
    fig.savefig(OUT / "endurance_vs_mass.png")
    plt.close(fig)


def plot_mass_budget():
    items = sorted(MASS_BUDGET.items(), key=lambda kv: kv[1])
    names = [k for k, _ in items]
    vals = [v for _, v in items]
    colors = ["#c0392b" if v == max(vals) else "#7f8c8d" for v in vals]
    fig, ax = plt.subplots(figsize=(9, 4.6), dpi=200)
    bars = ax.barh(names, vals, color=colors, height=0.62)
    for b, v in zip(bars, vals):
        ax.text(v + 4, b.get_y() + b.get_height() / 2,
                f"{v} g  ({v/sum(vals)*100:.0f} %)", va="center", fontsize=9)
    ax.set_xlabel("Mass (g)", fontsize=10)
    ax.set_title(f"Mass budget, {sum(vals)} g all-up: the battery is the "
                 f"single largest item", fontsize=12, fontweight="bold", pad=12)
    ax.grid(axis="x", ls=":", lw=0.6, alpha=0.5)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.set_xlim(0, max(vals) * 1.42)
    fig.tight_layout()
    fig.savefig(OUT / "mass_budget.png")
    plt.close(fig)


if __name__ == "__main__":
    plot_thrust_curve()
    plot_endurance()
    plot_mass_budget()
    print(f"\nFigures written to {OUT}")
