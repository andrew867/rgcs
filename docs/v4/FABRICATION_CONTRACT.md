# Fabrication contract (Agent G03)

Coverage: **S011, S016–S021, S024, G020**. Gates: **G18, G20**.
Status: `ENGINEERING_PROTOTYPE`.
Implementation: `rscs2_core.spiral_cone` (SCAD/DXF/STL),
`rscs2_core.cymatic_disk` (Gerber/Excellon/BOM).

## What is generated, and what "valid" means here

| Format | Producer | Validity evidence |
|---|---|---|
| OpenSCAD | `openscad_text` | parses; contains `linear_extrude` + `polygon`; carries the `pinch` parameter |
| DXF | `dxf_polyline_text` | ASCII DXF with a closed `LWPOLYLINE`, correct section/EOF structure |
| STL | `stl_text_from_path` | ASCII STL; facet count matches the path; solid open/close balanced |
| Gerber | `gerber_spiral_text` | RS-274X header, aperture defined, `M02*` terminated |
| Excellon | `drill_text` | header + tool defs + `M30` |
| BOM | `bom` | line items with quantity and role |

**Honest limitation.** These are checked for *well-formedness by the
tests in this repository*. They have **not** been through a
manufacturer's DRC, no board house has accepted them, and no printer
has produced a part. `ENGINEERING_PROTOTYPE` means exactly that.

A registry row saying "fabrication exports" is not proof that valid
fabrication files exist — which is why this table names the specific
structural check behind each format.

## Determinism

Every generator is deterministic: same parameters → byte-identical
output. A fabrication file that changes between runs cannot be
reviewed or reproduced, and the tests pin this.

## Matched controls (G20)

The control set is the point of the whole geometry lane. For any claim
about a shape, the matched control must be fabricated **in the same
material, by the same process, in the same session**:

| Control | Matches | Isolates |
|---|---|---|
| plain disk (S016) | material, mass | the pattern |
| simple cone (S017) | material, envelope | the spiral |
| flat log spiral (S018) | pattern, planar | the 3-D lift |
| Archimedean spiral (S019) | turns, extent | the *logarithmic* law |
| mass-matched blank (S020) | mass | everything geometric |
| material controls (S021) | geometry | the material |

The Archimedean control is the sharpest: it has the same "spiralness"
and differs only in the growth law. A result that survives the plain
disk but not the Archimedean spiral is a result about spirals in
general, not about the logarithmic one.

## Material boundaries

- **Printed polymer is a geometry reference, not a quartz dynamical
  surrogate.** Its modulus, loss, and density are wrong by orders of
  magnitude. It tests whether the *shape* does something.
- **Glass is not piezoelectric single-crystal quartz.** Fused silica
  is amorphous and has no piezoelectric tensor. It is a control for
  "hard transparent thing", not a cheap quartz.
- Copper-on-FR4 is a laminate; its stack matters and is modelled.

## Receiving inspection (as-built)

Every fabricated part must be inspected before use: mass, key
dimensions, surface finish, and deviation from the design. The as-built
digital twin uses the **measured** geometry, not the intended one — a
part is what it is, not what it was asked to be. This routes through
[METROLOGY_PROTOCOL.md](METROLOGY_PROTOCOL.md), and no part has been
inspected because none exists.

## Blocker

`ENGINEERING_PROTOTYPE` / `PROTOCOL_READY_HARDWARE_REQUIRED`. Requires
a print service, a board house, and inspection instruments. Cost and
procurement are Andrew's decision; nothing here has been ordered.
