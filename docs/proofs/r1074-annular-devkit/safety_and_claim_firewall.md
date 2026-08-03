# Safety and Claim Firewall

**Status:** `PASS_CODE_FIREWALL_PHYSICAL_REVIEW_PENDING`

RGCS-ARDK-001 is a low-power, stationary measurement demonstrator. It is not
a propulsion, thrust, lift, antigravity, over-unity, operational-craft, source
attribution, medical, or biological package. The only primary observable is
the complex electromagnetic field-asymmetry quantity `DeltaB`.

## Structural controls

- The bench gate rejects every primary observable other than `DeltaB`.
- Missing angular or amplitude uncertainty raises.
- Missing any of seven controls raises.
- Missing raw hashes or calibration identifiers raises.
- Crystal participation requires a no-crystal or dummy-crystal condition.
- Positive performance inference raises before a bench verdict.
- PASS and FAIL remain reachable with complete bounded inputs.
- An AST audit scanned 27 executable files and 3,032 identifiers with zero prohibited namespace leaks.
- The public-path filter excludes private message/ASCII and phenomenology lanes.
- `PUBLICATION_HOLD` is a constant true return and a checked-in report.

## Hardware safeguards

Default-off state, hardware current limit, fuse, enclosure interlock, thermal
sensors, derating, overtemperature abort, heartbeat abort, sensor-failure
abort, shielded wiring, strain relief, dummy-load commissioning, and magnetic
access control are required. The repository models state transitions but does
not certify physical implementation.

## Residual rule

A residual after modeled ordinary effects is a request for more controls. It
is not evidence of new physics, a named source, energy production, or
mechanical performance.
