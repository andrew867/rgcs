# PCB Design Specification

**Status:** `PASS_KICAD_DESIGN_SCAFFOLD_PUBLICATION_HOLD`

**Fabrication status:** `REFUSED`

## Board A: passive sensor and calibration

Board A has the 288/188 mm annular outline, 37 isolated `SENSE_nn` pickup
zones, eight board-edge `COMPASS_n` pickups, guard/reference nets, sector
fiducials, and shared mounting holes. Because the PCB has a 188 mm center
aperture, `CENTER_REF` is explicitly an interface pad for a fixture-mounted
center probe, not fictional copper at the origin. Board A contains no drive or
loading zones and no active components.

## Board B: active drive and loading

Board B independently has 37 `DRV_nn` and 37 `LOAD_nn` copper zones, optional
0603 trim/isolation footprints, `KELVIN_P_nn` and `KELVIN_N_nn` points,
external-driver breakout, preserved `SENSE_nn` access, guards, fiducials, and
the same registration holes. RevA does not merge the boards.

## Deterministic registry and generator

The checked-in registry contains 196 unique names: five sector nets for each
of 37 sectors, two guards, center reference, and eight compass nets. Its
SHA-256 is
`9e4ea79c79f05d58ff2744f34584a8ee4a169a36dd5fbe4f42139043f9b9b7f6`.
Tests regenerate and byte-compare board artifacts and metadata.

| Generated design | SHA-256 |
|---|---|
| Board A `.kicad_pcb` | `ed9a64212e5a9444b91d64b2bc2e66ca50242ea9992d1271dc5a60dc712111eb` |
| Board B `.kicad_pcb` | `b8eaea96124a6913e8c0df768f814fa84e4a0dfa2ba945d32ee4a04cd967e081` |

Each metadata file records R10.73 hashes, `seed_used=false`,
`fabrication_ready=false`, `drc_executed=false`, and the publication hold.
KiCad owns copper, pads, nets, DRC, board exports, and fabrication plots.
OpenSCAD owns only fixture solids.

## Refusal

The local environment has no `kicad-cli`. The manufacturer stackup remains
unset, and no native DRC, reviewed BOM, assembly drawing, Gerbers, drills,
STEP, pick/place, or hashed fabrication archive exists. The design generator
therefore emits no manufacturing archive or `FAB_READY` state.
