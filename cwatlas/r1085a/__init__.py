"""R10.8.5A — outer-in gravity-shell projection layer.

Downstream of the recovered F5 | Q22 | S3 packet grammar (R10.8.5,
``r12.icosapacket`` / ``r12.icosarefine``, reused verbatim and NOT
modified here). This package implements the corrected projection the
operator locked on 2026-07-26:

* the radial calculation begins at the **outermost operational
  boundary** and proceeds **inward along a gravity-field line** — never
  outward from Earth's geometric centre;
* the **shell-3 zero** is referenced to an epoch-appropriate **average
  land-height** surface measured along gravity vertical — not mean sea
  level, not a spherical radius, not WGS84 altitude;
* **magnetics are geometry**: shell boundaries are level sets of a
  declared functional of gravity and magnetic scalars, run as a bounded
  candidate family with every member retained;
* **time and ground reference** are mandatory inputs: epoch selects the
  field states and shell geometry, ground reference selects rotational
  phase and body-fixed alignment;
* hierarchical X/Y/Z indices are **addresses, not coordinates** —
  conventional latitude/longitude appear only as the final output.

Claims discipline: ``SOURCE_ORIGIN_VALIDATED: no`` throughout. The
Stonehenge word ``165876523`` is a **hard training equality** — a
calibration input, never a validation result. Nothing in this package
measures anything physical.
"""

SOURCE_ORIGIN_VALIDATED = "no"

VERDICTS = (
    "RGCS_R10_8_5A_GREEN_OUTER_IN_GRAVITY_SHELL_PROJECTION_SOLVED",
    "RGCS_R10_8_5A_YELLOW_PACKET_AUTHORITY_HELD_PROJECTION_UNDERDETERMINED",
    "RGCS_R10_8_5A_RED_CORRECTED_PROJECTION_NOT_EXECUTED",
)
