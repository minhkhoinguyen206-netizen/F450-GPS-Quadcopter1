# Regulatory context

Why autonomous waypoint missions are not enabled, and what would change that.

---

## Current position

The vehicle was built and flown in Auburn, Alabama. Two constraints applied:

- **FAA recreational flyer rules** require the aircraft to be kept within the visual line of sight of the operator, or of a visual observer co-located with and in direct communication with the operator.
- **Local ordinance** covering the parks and open areas used for flight testing.

An autonomous waypoint mission is, by definition, a flight in which the aircraft navigates on its own to positions the operator has not commanded in real time. On any route long enough to be interesting, that puts the aircraft outside line of sight.

INAV's mission planner has therefore been **studied but not activated**. This is a legal constraint rather than a technical one: the firmware supports up to 120 waypoints, the position estimator has been validated by the position-hold and return-to-home tests, and nothing in the vehicle would prevent it.

---

## What is enabled

| Capability | Status | Line of sight |
|---|---|---|
| Angle and acro modes | Enabled | Maintained |
| Altitude hold | Enabled | Maintained |
| GPS position hold | Enabled | Maintained |
| Return to home | Enabled | Maintained; the aircraft returns toward the operator |
| Waypoint missions | **Not enabled** | Would be broken |

Return to home is worth distinguishing from a waypoint mission. It is a failsafe behaviour that brings the aircraft back toward the operator rather than away, it triggers on link loss or explicit command, and it does not extend the operating envelope. It is a safety feature, not an autonomy feature.

---

## Safety practices in use

Not regulation, but they belong in the same document.

- Flights are conducted in open areas, away from people, buildings and roads.
- Propellers are removed for every bench test involving powered motors.
- The vehicle is armed only when it is on the ground and clear.
- Battery voltage is monitored, with the pack calibrated in INAV against a multimeter to within 0.05 V, so the low-voltage warning is trustworthy.
- After every crash, the whole airframe is inspected mechanically, not only the part that visibly broke. This one was learned the hard way; see [`fault-analysis.md`](fault-analysis.md).

The vehicle carries 1.2 kg on four unguarded propellers turning at over 7000 rpm. Propeller guards are under consideration and are not currently fitted.

---

## What changes on relocation

The vehicle moves to Oregon with the author. Before any waypoint testing:

1. Review the airspace classification for the intended area, including any controlled airspace around Corvallis Municipal Airport, and obtain authorisation where required.
2. Identify authorised model-aircraft flying areas and any Oregon State University policy covering unmanned aircraft on campus property.
3. Confirm current federal requirements, including registration and Remote ID, which have changed within the lifetime of this project and should not be assumed from memory.
4. Only then enable missions, starting with a short route entirely inside visual range so that the estimator and the failsafe behaviour can be checked against something observable before the aircraft is asked to do anything unobserved.

Step 4 is the same principle as the rest of the build: prove the subsystem where you can see it before you rely on it where you cannot.

---

## Note on this document

Regulations change and vary by jurisdiction. Nothing here is legal advice, and anyone reproducing this build is responsible for confirming the rules that apply to them at the time they fly.
