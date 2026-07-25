# UI Spec — CW Atlas 3D Globe and Shell Viewer (P59)

**Phase:** T08 / P59 (Application, Documentation, and Release)
**Status:** SPEC. The 3D globe frontend (CesiumJS / React) is **not** built in
this Python repository's pytest gate; it is delivered as an implementation
specification against the same P57 backend service API as P58. The engine it
consumes is built and tested in `cwatlas/`.
**Depends on:** P58 (2D web app + service contract), P13/P14/P15 (icosahedron,
dodecahedron, subdivision), P16 (shells), P29 (radial/shell), P32/P44
(uncertainty regions), P35/P37 (icosahedral vector, route prefixes).

> `SOURCE_VECTOR_GEOGRAPHIC_SEMANTICS_NOT_CLAIMED`
> `PHYSICAL_VALIDATION_NOT_CLAIMED`

---

## 1. Scope

This document specifies the **three-dimensional globe and shell viewer**: a
CesiumJS globe on which the operator clicks to make an address, switches between
Earth and Mars, toggles shell layers `0..8`, overlays icosahedral faces and
alias regions, and inspects the radial/shell structure. It is the same engine
and the same claim boundary as the 2D app (P58); this is a different *view*, not
a different *truth*. No browser code ships here.

The 3D view obeys the same two non-negotiables: **no pin without CRS and epoch**
(invariant 9) and **no forced pin from a legacy vector** (invariant 4).

## 2. Recommended stack

```text
Language:   TypeScript (strict)
Framework:  React 18 + Vite
Globe:      CesiumJS (WebGL globe + 3D primitives)
Transport:  fetch/JSON against the P57 service API (shared with P58)
```

CesiumJS is **optional but supported** (Architecture Spec). The 3D viewer reuses
the P57 service contract verbatim; it adds only view-layer concerns (camera,
shell layers, face overlays). It holds no geodesy, codec, or claim logic.

## 3. Screen and component map

```text
GlobeShell
├── BodySwitch              (EARTH ⇄ MARS)
├── GlobeCanvas             (CesiumJS globe: click → address, camera, layers)
├── ShellLayerPanel         (shells 0..8, nonliteral labels, visibility toggles)
├── RadialInspector         (radial profile ⇄ shell mapping, P29)
├── FaceOverlayPanel        (icosahedral 20-face grid + recursive cells + route prefix)
├── OverlayLayers
│   ├── AliasRegionOverlay  (polygons / error regions on the globe surface)
│   └── UncertaintyOverlay  (circle / ellipse / cell-polygon regions, P32/P44)
├── ResultPanel             (shared with P58: Pin / AliasSet / Region / Heatmap / Refusal)
└── ReceiptDrawer           (shared with P58)
```

The `ResultPanel` and `ReceiptDrawer` are the **same components** as the 2D app;
the P48 vector-to-pin state machine is unchanged. This document specifies only
what is new to the globe.

## 4. Body switch — Earth / Mars

`BodySwitch` toggles the reference body via `atlas_params.allowed_bodies()`
(`EARTH`, `MARS`). Switching body:

- reloads the CesiumJS ellipsoid to that body (Earth `a = 6378137 m`; Mars
  `a = 3396190 m`, from `mars_frame.EARTH` / `MARS`);
- reloads the allowed frames (`allowed_frames(body)`): Earth carries `WGS84`, the
  ITRF realizations, and `IAU_EARTH_BODY_FIXED`; Mars carries only
  `IAU_MARS_BODY_FIXED`;
- reprojects any active pins/regions using the service, never client-side.

A body switch never silently reuses the other body's frame; if the current frame
is invalid for the new body the UI forces a re-selection before any pin.

## 5. Globe click → address

A click on the CesiumJS globe resolves to `(lat, lon)` on the selected body's
ellipsoid and calls `POST /address/from-click`
(`map_to_address.map_click_to_address`). As in the 2D app, **uncertainty is a
required explicit input** for a direct click; the globe supplies the operator's
declared click precision, never a hidden default. The resulting
`GeospatialAddress` flows into the shared `AddressPanel`/`ReceiptDrawer`.

If frame or epoch is unset, the endpoint refuses
(`refuse_pin_without_crs_epoch`) and the globe shows the `RefusalCard` — no
billboard is placed.

## 6. Shell layers 0..8 (P16) — nonliteral labels

`ShellLayerPanel` lists the shell registry (`shells.SHELL_REGISTRY`, indices
`0..8`). Each layer renders as a translucent radial band around the globe.

| Shell | Ontology label (nonliteral) | Surface semantics |
|-------|-----------------------------|-------------------|
| 0 | `SHELL_0_SURFACE_DATUM` | body-relative surface datum |
| 1–7 | `SHELL_1_BAND` … `SHELL_7_BAND` | body-relative altitude bands |
| 8 | `SHELL_8_OUTER_BAND` | outermost body-relative band |

The panel must render these as **labels, not altitudes**. The band edges in the
registry are source-ontology band ordinals, not measured metres; the UI must not
present them as physical altitudes. Labels carry the `SOURCE_CLAIM` claim class.

**8 ⇄ 0 closure.** The source ontology asserts shell 8 wraps to shell 0. This is
stored (`shells.SHELL_CLOSURE`) and is **never auto-applied**
(`apply_shell_closure(index, apply_closure=False)` refuses the 8→0 case by
default). The viewer may draw the closure as a dashed, explicitly-labelled
"SOURCE ontology closure (opt-in)" annotation only when the operator ticks an
opt-in control; it must never render shell 8 as if it were shell 0 by default.

## 7. Radial / shell inspector (P29)

`RadialInspector` visualizes the declared radial conventions
(`radial.RADIAL_PROFILES`): `DIMENSIONLESS`, `SURFACE`, `ATMOSPHERE`, `ORBIT`.
For a selected profile it shows the mapping

```text
u = (r - datum_offset) / band_width   →   shell ordinal
```

using `radial.radial_to_shell` / `shell_to_radial`. Band widths and datums are
**declared convention constants, not measured physics**; the inspector labels
them as such. The nonliteral `EFFECTIVE_POTENTIAL_ORDINAL_{i}` labels
(`radial.EFFECTIVE_POTENTIAL_LABELS`) may be shown as **ordinal re-expressions of
the shell index only** — never as physical potentials
(`radial.refuse_effective_potential_as_physical` is the engine guard).

## 8. Icosahedral face overlay and recursive cells (P13/P15/P35/P37)

`FaceOverlayPanel` overlays the 20-face spherical icosahedron
(`icosahedron.build_icosahedron`: 12 vertices, 30 edges, 20 faces) on the globe.

- **Face grid** — the 20 base faces, stably numbered. A globe click can be
  classified to its face (`icosahedron.classify_point`).
- **Recursive cells** — the one-to-eight refinement
  (`subdivision.refine` / `child_index`) drawn to the selected `depth`
  (`atlas_params.allowed_depths`), so the operator sees the octal path a
  `CW-HCM-ICO` vector walks (`ico_vector.address_to_ico_vector`).
- **Route prefix** — the variable-depth route (`route_prefix`: `terra:` / `sol:`
  namespaces, `d<N>/seg0/seg1/…`) shown as a breadcrumb over the face path.
- **Dual topology note** — a face id (icosahedron) and a dodecahedron vertex id
  (`dodecahedron.dual_vertex_of_face`) are distinct graphs; the overlay must not
  conflate them. A **face id is a cell of a synthetic tessellation, not a
  place** — the panel says so.

## 9. Alias-region and uncertainty overlays (P32/P44)

For a decoded vector, the globe reuses the P48 state machine (§ P58) and draws:

- **UNIQUE_POINT** — one billboard plus its uncertainty circle. Only when a
  prospective calibration exists.
- **ALIAS_SET** — one region per candidate, side by side, none highlighted.
- **REGION** — a single `ErrorRegion` from `alias_regions.region_for_uncertainty`.
- **HEATMAP** — a weighted density surface from `alias_regions.alias_heatmap`.
- **REFUSAL** — the shared `RefusalCard` with the engine's `why_unavailable` text.

Uncertainty regions render by `uncertainty.RegionKind`:

| RegionKind | Cesium primitive | Source |
|------------|------------------|--------|
| `CIRCLE` | `EllipseGraphics` (equal axes) | `uncertainty.propagate_circle` |
| `ELLIPSE` | `EllipseGraphics` with `orientation_deg` | `uncertainty.propagate_ellipse` |
| `CELL_POLYGON` | `PolygonGraphics` from `vertices_m` | `uncertainty.cell_polygon` |

Each region carries `area_m2`, `combined_sigma_m`, `k_sigma`, and
`search_space_count` into the receipt. A region collapsed to a point without
justification is refused by the engine (`uncertainty.refuse_invented_precision`);
the globe must never draw a zero-area "exact" marker for an uncalibrated decode.

## 10. Camera and altitude

Camera altitude in the viewer is a **display** parameter and must never be
conflated with a shell ordinal or a radial value. The viewer's zoom does not
change the address; the address's shell/altitude come only from the ParameterBar
and the service.

## 11. Non-claims (must hold in the 3D view)

- Shell labels, radial bands, and effective-potential ordinals are **nonliteral
  SOURCE ontology**; none is a measured altitude, potential, or physical field.
- An icosahedral face or recursive cell is a **synthetic tessellation cell, not a
  place**.
- A pasted source/legacy vector does **not** identify a real location on Earth,
  Mars, or anywhere; it yields an alias set, region, heatmap, or refusal.
- The 8⇄0 closure is source ontology and is never applied without an explicit
  opt-in.

## 12. Acceptance (spec-level)

- Every globe action maps to a named P57 endpoint and a tested `cwatlas`
  function; the viewer adds no independent transform.
- Shells `0..8` render with nonliteral labels and no auto-closure.
- Uncertainty regions render by `RegionKind`; no zero-area pin for an
  uncalibrated decode.
- Earth/Mars switching reloads body, ellipsoid, and allowed frames without
  frame carry-over.

```text
GREEN_R10_8_1_P59_THREE_DIMENSIONAL_GLOBE_AND_SHELL_VIEWER (SPEC)
```
