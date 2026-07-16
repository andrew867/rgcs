# Canonical 110 mm Crystal Spec (Agent 05)

Module: rscs2_core/crystal110.py. Tests: tests/v4/test_rscs2_crystal110.py
(6). Evidence: evidence/v4/agent05/.

## Two configurations (never confusable; machine-tested distinct)

| Variant | Length (mm) | Provenance |
|---|---|---|
| ideal_n7 | 110.0376674107143 = 770.263671875/7 | (v_L/(2 f_c))/7 with FROZEN v2 defaults v_L=6310 m/s (RGCS-M.10), f_c=4096 Hz. ARITHMETIC derivation; no physical claim. |
| nominal | 110.000000 | real-specimen nominal |

## Geometry (defaults; all explicit parameters, recorded per manifest)

- 6 side facets; across_vertices diameters; face_slope angles.
- Female (receiver) 51.843 deg / male (transmitter) 60 deg -- Source
  claims (RG-16), conventions via FROZEN v2 helpers (RGCS-M.1..M.4).
- Diameter policy (documented default, not invented): SP-Q154 ratios
  40/154 and 30/154 x L -> ideal: D_w=28.5812, D_n=21.4359 mm; cap
  heights 15.751 / 16.077 mm; shaft 78.209 mm (caps+shaft == L, 1e-12).
- Frames: body +Z from female apex (z=0) to male apex (z=L); x_v2 ==
  z_body; quartz C-axis default +Z; orientation via Agent 04 Euler.
- Geometric centre z=L/2; RGCS node prior = frozen rgcs_core.geometry
  .nodes; NO measured node, NO eye coordinate assumed (record fields
  exist and are null/None).
- Region annotations (manifest): electrode candidates (opposed shaft
  facets, 0.35-0.65L), coil envelopes (0.3L/0.7L), optical entry (lower
  shaft facet ~0.4L), 3-point fixture pads at free-free flexural node
  stations 0.224L/0.776L.

## Canonical first modes (free, quartz C||Z, clmax=6 mm, P2)

| Mode | ideal_n7 (Hz) | nominal (Hz) | rel diff |
|---|---|---|---|
| 1 | 13776.54 | 13781.40 | -3.53e-4 |
| 2 | 13777.00 | 13781.81 | -3.49e-4 |
| 3 | 25912.27 | 25919.97 | -2.97e-4 |
| 4 | 31862.48 | 31873.91 | -3.58e-4 |
| 5 | 31867.00 | 31874.87 | -2.47e-4 |
| 6 | 35268.93 | 35280.99 | -3.42e-4 |
| 7 | 50578.30 | 50588.11 | -1.94e-4 |
| 8 | 52590.46 | 52608.70 | -3.47e-4 |

Internal consistency: dL/L = +3.42e-4 (ideal longer) -> frequencies
LOWER by ~3.4e-4, exactly as observed (f ~ 1/L scaling). Modes 1/2 and
4/5 are near-degenerate flexural pairs (hexagonal section) with the
small splitting expected from trigonal anisotropy + discretization; the
taxonomy tools of Agent 04 apply.

## STEP status

NOT_GENERATED. Built-in gmsh kernel cannot emit STEP; the OCC-kernel
path is documented and classified IMPLEMENTED_DOCUMENTED_UNTESTED per
user decision DV4-013(4). STL/OBJ/VTU/MSH exports are real and shipped.
