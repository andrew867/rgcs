# Phryll Generator Designer v2 (crystal-first)

v2 generates a **bespoke** cone, holder, and coil sleeve from your
measured crystal — it never picks or scales a stock M1/M2/L/L2/V3 mesh.
The CC-SA reference assets provide style, wall thickness, and
size-family examples only.

## Workflow

1. Enter the measured profile: length, top diameter (60° end), base
   diameter (52° end), max body width, facet count, and the **Eye
   coordinate** with its uncertainty. The Eye is entered, calculated,
   or imported — it is not a midpoint.
2. Choose fit settings (clearance, wall, print tolerance) and coil
   settings (wire gauge, groove depth).
3. **Generate** — the inner cone is your crystal envelope + clearance;
   the outer cone adds the wall; the crossed copper/silver grooves are
   phased so a crossing plane lands **exactly on the Eye coordinate**
   (residual reported against `max(0.25 mm, 2 × Eye uncertainty)`).
4. **Export bundle** — SCAD (full module set: cone, sleeve, grooves,
   Eye marker, base adapter, cap, LED holder, jack holder, locker),
   STL + 3MF from the built-in mesh backend (OpenSCAD optional), SVG
   axial/top templates, DXF winding template, compatibility PDF, build
   PDF, JSON receipts, and a `CHECKSUMS.sha256`-verified bundle.

## Spacing model

clear gap = 2 × wire Ø · groove pitch = 3 × wire Ø (AWG 28 → 0.66 /
0.99 mm) · nearest-conductor standoff = clearance + wall − groove
depth · coil-center standoff adds wire Ø / 2 (defaults land at ≈7–8
wire diameters — a design default to sweep, not a proven optimum).

## Crystal-bottom coupling

The coupling chain is: crystal bottom → open or lightly coupled gap →
flat pickup surface → annular pickup ring. The cone is **open below
the crystal base aperture** — the bottom is never overconstrained with
solid plastic, and the coupling path stays exposed. O-rings are
allowed as compliant mounts: contact stabilizes the crystal without
hard damping of internal oscillation (compression is bounded 5–30 %
and the material, cord diameter, ID, compression, and contact height
are all recorded on the build sheet).

## Excitation paths

Hardware excitation is implemented first, in this order: photonic /
laser · magneto-acoustic / pulsed coils · mechanical / acoustic ·
electrical / coil. Intention/focus-only operation is recorded as
source language only — it is not an implemented mode.

## Kept separate

Annular-ring craft locks (35/37 running, 33 steering, 47/72, 288/188 mm,
1,683,456 Hz) are a different lane and never size the cone. The M2
*text* profile (29/39/120) and the M2 *mesh-decoded* profile
(30.24/44.91/103.71) disagree and are both preserved — never merged.

## Claim boundary

Generated geometry is a model output and engineering plan.
Source-language wiring/pulse notes (copper CW + silver CCW crossed, no
contact, alternating 4096 Hz drive, user voltage limits) are recorded,
not validated. The compatibility sheet documents fit geometry; it does
not assert physical output.
