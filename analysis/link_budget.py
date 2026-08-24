#!/usr/bin/env python3
"""
=============================================================================
 F450 GPS Quadcopter: ELRS 2.4 GHz control link budget
=============================================================================

 The V2 revision moved both receiver antennas from a vertical mast above the
 flight controller to the underside of the frame, because the mast was the
 first thing to break in every crash. The original write-up called the
 resulting RF penalty "measurable but tolerable" and left it there. This file
 replaces that assertion with a number.

 Method is a standard one-way link budget:

     P_rx = P_tx + G_tx + G_rx - FSPL(d, f) - L_blockage
     margin = P_rx - S_rx

 where FSPL is free-space path loss and S_rx is the receiver sensitivity at
 the configured packet rate. ExpressLRS sensitivity is rate-dependent, which
 is the lever the pilot actually controls, so several rates are tabulated.

 This is a prediction, not a range test. Real links are limited by ground
 reflection nulls, antenna pattern shape and Fresnel zone clearance long
 before free-space loss becomes the constraint. The budget is still the right
 tool for the question asked here, which is comparative: how much margin does
 the relocation spend, and is there enough left.

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
# LINK PARAMETERS
# =============================================================================
F_MHZ = 2440.0
P_TX_MW = 150.0
P_TX_DBM = 10 * math.log10(P_TX_MW)

G_TX_DBI = 2.0           # handheld transmitter dipole
G_RX_DBI = 2.0           # receiver dipole, boresight

# ExpressLRS receiver sensitivity by packet rate. Lower rates spend more time
# per symbol and buy sensitivity; the cost is control latency.
SENSITIVITY_DBM = {
    "50 Hz":  -112.0,
    "150 Hz": -108.0,
    "250 Hz": -105.0,
    "500 Hz": -102.0,
}
RATE_USED = "150 Hz"

# Blockage scenarios. The airframe, battery and carbon arms sit between the
# antenna and the operator for a large part of the sphere once the antennas
# are under the frame.
BLOCKAGE_DB = {
    "Mast, clear line of sight (V1)":       0.0,
    "Underside, favourable attitude (V2)":  6.0,
    "Underside, airframe in the path (V2)": 15.0,
    "Underside, deep null (V2, worst)":     25.0,
}

MARGIN_REQUIRED_DB = 10.0   # conventional fade margin for a control link
SEP = "-" * 76


def hdr(t):
    print("\n" + "=" * 76)
    print(" " + t)
    print("=" * 76)


def fspl_db(d_m, f_mhz=F_MHZ):
    """Free-space path loss. Guard the singularity at zero range."""
    d_km = np.maximum(np.asarray(d_m, dtype=float), 1.0) / 1000.0
    return 20 * np.log10(d_km) + 20 * np.log10(f_mhz) + 32.44


def margin_db(d_m, blockage=0.0, rate=RATE_USED):
    return (P_TX_DBM + G_TX_DBI + G_RX_DBI - fspl_db(d_m) - blockage
            - SENSITIVITY_DBM[rate])


def range_at_margin(blockage=0.0, rate=RATE_USED, margin=MARGIN_REQUIRED_DB):
    """Distance at which the link falls to the required fade margin."""
    budget = (P_TX_DBM + G_TX_DBI + G_RX_DBI - blockage
              - SENSITIVITY_DBM[rate] - margin)
    d_km = 10 ** ((budget - 20 * math.log10(F_MHZ) - 32.44) / 20.0)
    return d_km * 1000.0


hdr("1. LINK PARAMETERS")
print(f"   Carrier frequency                    {F_MHZ:8.0f} MHz")
print(f"   Transmit power                       {P_TX_MW:8.0f} mW  ({P_TX_DBM:.1f} dBm)")
print(f"   Antenna gain, each end               {G_TX_DBI:8.1f} dBi")
print(f"   Packet rate in use                   {RATE_USED:>10}")
print(f"   Receiver sensitivity at that rate    {SENSITIVITY_DBM[RATE_USED]:8.1f} dBm")
print(f"   Required fade margin                 {MARGIN_REQUIRED_DB:8.1f} dB")

hdr("2. MARGIN AGAINST DISTANCE")
dists = [100, 250, 500, 1000, 2000]
print(f"   {'Scenario':<38}" + "".join(f"{d:>7} m" for d in dists))
print(SEP)
for name, b in BLOCKAGE_DB.items():
    row = "".join(f"{margin_db(d, b):6.0f} dB" for d in dists)
    print(f"   {name:<38}{row}")
print(SEP)
print("   Values are margin above the demodulation threshold. Positive means the")
print("   link closes; anything under about 10 dB is where packet loss and")
print("   failsafe events start appearing in practice.")

hdr("3. USABLE RANGE AT A 10 dB FADE MARGIN")
base = range_at_margin(BLOCKAGE_DB["Mast, clear line of sight (V1)"])
print(f"   {'Scenario':<38}{'Range':>10}{'vs V1':>10}")
print(SEP)
for name, b in BLOCKAGE_DB.items():
    r = range_at_margin(b)
    print(f"   {name:<38}{r:8.0f} m{r/base*100:8.0f} %")
print(SEP)
worst = range_at_margin(BLOCKAGE_DB["Underside, deep null (V2, worst)"])
print(f"   FINDING: even the worst-case underside null leaves {worst:.0f} m of usable")
print("   range at a 10 dB margin. Every flight in this project has been")
print("   line-of-sight inside a few hundred metres, so the relocation spends")
print("   margin the vehicle was never using. That is what makes it a good")
print("   trade rather than merely a convenient one.")
print()
print("   The honest caveat: free-space loss is optimistic near the ground.")
print("   Ground-reflection nulls and Fresnel obstruction dominate below about")
print("   10 m altitude, and this budget does not model them. The comparison")
print("   between the two antenna positions still holds, because both suffer")
print("   those effects equally.")

hdr("4. PACKET RATE AS THE PILOT'S LEVER")
print(f"   {'Rate':>8}{'Sensitivity':>14}{'Range, 15 dB blocked':>24}"
      f"{'Control latency':>18}")
print(SEP)
for rate, s in SENSITIVITY_DBM.items():
    r = range_at_margin(15.0, rate)
    latency = 1000.0 / float(rate.split()[0])
    print(f"   {rate:>8}{s:11.0f} dBm{r:20.0f} m{latency:15.1f} ms")
print(SEP)
print("   Dropping from 500 Hz to 50 Hz buys 10 dB, which is a factor of about")
print("   three in range, and costs 18 ms of stick-to-motor latency. For a")
print("   line-of-sight GPS platform that is a trade worth making; for a racing")
print("   quad it is not. 150 Hz is the sensible middle and is what is flown.")


# =============================================================================
# FIGURE
# =============================================================================
def plot_margin():
    d = np.logspace(1.5, 4.0, 500)
    fig, ax = plt.subplots(figsize=(9.2, 5.2), dpi=200)
    for (name, b), col in zip(BLOCKAGE_DB.items(),
                              ("#1f8a55", "#0b6e99", "#e07b39", "#c0392b")):
        ax.plot(d, margin_db(d, b), lw=2.2, color=col, label=name)
    ax.axhline(MARGIN_REQUIRED_DB, color="#333", ls="--", lw=1.4)
    ax.text(40, MARGIN_REQUIRED_DB + 1.8, "10 dB fade margin",
            fontsize=8.5, color="#333", ha="left")
    ax.axhline(0, color="#333", lw=1.0)
    ax.text(40, 1.8, "link threshold", fontsize=8.5, color="#333", ha="left")
    ax.axvspan(50, 400, color="#f2c744", alpha=0.16,
               label="range actually flown in this project")
    ax.set_xscale("log")
    ax.grid(True, which="both", ls=":", lw=0.6, alpha=0.55)
    ax.set_title("ELRS 2.4 GHz link margin, and what the antenna move costs",
                 fontsize=12, fontweight="bold", pad=12)
    ax.set_xlabel("Slant range (m)", fontsize=10)
    ax.set_ylabel("Margin above sensitivity (dB)", fontsize=10)
    ax.tick_params(labelsize=9)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.set_ylim(-20, 80)
    ax.legend(fontsize=8.5, loc="upper right", framealpha=0.95)
    fig.tight_layout()
    fig.savefig(OUT / "link_margin.png")
    plt.close(fig)


if __name__ == "__main__":
    plot_margin()
    print(f"\nFigure written to {OUT}")
