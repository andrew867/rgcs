"""RGCS closed-loop resonator platform (Agent R01; coverage R001-R008).

Design -> simulate -> fabricate -> fixture -> excite -> measure ->
identify mode -> select trim -> ablate/machine -> verify -> accept or
iterate. This package is the software platform for that loop.

BINDING BOUNDARIES (from the addendum and the shared contract):

- Everything this package has ever produced is SYNTHETIC. No physical
  resonator has been fabricated, fixtured, measured, or trimmed. The
  synthetic flag is carried on every record and cannot be removed.
- Predicted, measured, fitted, and accepted frequencies are FOUR
  different fields and are never conflated (R005).
- Irreversible actions (laser/CNC trim) require an explicit approval
  token AND a machine-capability flag; neither exists by default
  (R006, R036).
- A resonator is not an oscillator (R10 boundary).
- Measurement history is immutable and append-only (R004).
- No therapeutic, consciousness-effect, or anomalous-field claim is
  made anywhere in this package, its records, or its certificates.
"""

LIFECYCLE_STATES = (
    "DESIGNED", "SIMULATED", "FABRICATED", "FIXTURED", "MEASURED",
    "MODE_IDENTIFIED", "TRIM_PLANNED", "TRIM_APPROVED",
    "TRIM_EXECUTED", "VERIFIED", "ACCEPTED", "REJECTED",
    "QUARANTINED",
)

# legal transitions of the lifecycle state machine (R001)
LIFECYCLE_TRANSITIONS = {
    "DESIGNED": {"SIMULATED"},
    "SIMULATED": {"FABRICATED"},
    "FABRICATED": {"FIXTURED"},
    "FIXTURED": {"MEASURED"},
    "MEASURED": {"MODE_IDENTIFIED", "QUARANTINED"},
    "MODE_IDENTIFIED": {"TRIM_PLANNED", "ACCEPTED", "REJECTED"},
    "TRIM_PLANNED": {"TRIM_APPROVED", "REJECTED"},
    "TRIM_APPROVED": {"TRIM_EXECUTED"},
    "TRIM_EXECUTED": {"FIXTURED"},        # remeasure after every trim
    "VERIFIED": {"ACCEPTED", "REJECTED"},
    "ACCEPTED": set(),
    "REJECTED": set(),
    "QUARANTINED": {"FIXTURED"},
}
# VERIFIED is entered from MODE_IDENTIFIED when a held-out check runs
LIFECYCLE_TRANSITIONS["MODE_IDENTIFIED"].add("VERIFIED")
