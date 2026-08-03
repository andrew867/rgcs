# Parametric Geometry Report

**Status:** `PASS_DESIGN_GEOMETRY_PUBLICATION_HOLD`

## Locked geometry

| Quantity | Value | Verification |
|---|---:|---|
| Physical sectors | 37 | Exact count |
| Sector pitch | `360/37 deg` | `fractions.Fraction` authority |
| Outer diameter / radius | 288 / 144 mm | Parameter and generated-edge check |
| Inner diameter / radius | 188 / 94 mm | Parameter and generated-edge check |
| Mean radius | 119 mm | Pickup and probe coordinate authority |
| ID/OD | `47/72` | Exact reduced fraction |
| Mechanical rotation | false | Parameter, fixture, and report lock |

The Python kernel emits deterministic annular-sector polygons with a declared
angular isolation gap. Board A uses the 110-128 mm band for 37 pickup sectors.
Board B uses 126-140 mm drive sectors and 98-108 mm loading sectors. These are
design bands, not manufacturer-approved clearances.

## Alignment

Both PCB variants and the fixture use four 3.2 mm registration holes on a
136 mm radius at 45, 135, 225, and 315 degrees. Fiducials mark sector 0 and
every fifth sector. The fixture carries 37 probe-holder positions at 119 mm.
Tests compare shared dataclass coordinates rather than duplicated rounded text.

## Inputs and outputs

- Parameters: `constants_revA.json` SHA-256
  `69defa4e8aa4b049baf5ebfb0f5733bd703360eaaa7903f3e812c12379c47437`.
- Desktop profile: SHA-256
  `926f0b2798b57cb1329e9ac84d551a06bbb8732ed5c6f55f4986384ddc2f6e9b`.
- Fixture scaffold: SHA-256
  `47e3c7ef1ce9cff318fe5e65bfe884ee36a2243a59b1ef82302c1d1ad2fe56ab`.

OpenSCAD rendering and tolerance inspection remain pending because the local
executable and physical material selections are unavailable. This does not
change the software geometry verdict and does block mechanical fabrication.
