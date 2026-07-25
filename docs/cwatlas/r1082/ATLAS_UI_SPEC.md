# Atlas UI and Operator Workflow — Spec (R10.8.2, P30)

**Status:** Spec-level (the live browser UI is untestable in this environment;
`node` exists but no DOM/canvas harness). The **contract** this spec describes
is code-backed and tested by `cwatlas/r1082/ui_state.py`
(`build_view_model`) and `tests/cwatlas/r1082/test_ui_state.py`.

**Objective:** the usable **map-to-vector** and **vector-to-map** product the
operator requested, built over the locked `EARTH_ROOT_D_V1` two-layer root.

**Governance posture (non-negotiable, shown in every screen):**

```
measured_here            = nothing
PHYSICAL_VALIDATION_NOT_CLAIMED
PHYSICAL_EFFECTS_NOT_CLAIMED
SOURCE_ORIGIN_NOT_VALIDATED
```

A pin is at most a `CALIBRATED_CANDIDATE` — a software result under a declared,
frozen calibration. The UI renders regions and alias sets, **never** a
false-exact pin, and **never** a measured or origin-validated coordinate.

---

## 1. The code-backed contract

The UI binds to the serializable view-model produced by
`ui_state.build_view_model(epoch, shell, source_vector=…, profile_kind=…)`. It
has **no hidden defaults**: every control value and every assumption is present
in the model *before* an operation runs. The model round-trips through JSON and
is deterministic (`ui_state.is_serializable`).

Top-level keys the UI binds:

| Key | Purpose |
|-----|---------|
| `controls` | control domains (shell, epoch, profile, packet_depth, mode) |
| `control_values` | the operator's current selections (no hidden defaults) |
| `assumptions` | everything assumed, shown **before** execution |
| `overlay` | the two-layer-root globe layers (`overlay_spec.build_overlay_state`) |
| `candidate_panel` | the decoded candidate (pins / region / alias set) for a pasted vector |
| `agreement_surface` | per-cell variance / angular dispersion across retained families |
| `semantic_fields` | the seven logical decode fields |
| `export` | one-click export formats (JSON / GeoJSON / KML) |

---

## 2. Screens

### 2.1 Globe (shared)

Renders the five overlay layers from `overlay_spec.build_overlay_state`:

1. **`FIXED_ROOT_MARKER`** — the Wilkes gravity-anomaly root marker and its
   icosahedral face centre. **Epoch-independent**: animating the epoch never
   rotates it.
2. **`DYNAMIC_SAA_PHASE_ZERO`** — the South Atlantic Anomaly field-magnitude
   minimum at `(epoch, shell)`. It **moves** as epoch and shell change; drawn
   with its uncertainty region, never as a bare point.
3. **`ORIENTATION_FRAME`** — the South-Up basis with viewpoint-safe arrows:
   **clockwise-positive** from the Antarctic external viewpoint,
   **anticlockwise** from the North-down inverse view (the same physical
   rotation). The UI must render both labels so the sign is never ambiguous.
4. **`SHELL_SURFACE`** — the shell index and the radius it supplies
   (`shell_supplies_radius = true`, `altitude_missing = false`).
5. **`CANDIDATE_OUTPUTS`** — pins/regions from the forward geocoder.

Out of field-model validity the overlay yields a single
`MODEL_VALIDITY_REFUSAL` layer; the globe shows a refusal banner, **not** an
invented direction.

### 2.2 Map-to-vector (encode) screen

The operator **clicks a location** (or types lat/lon) on the globe and gets a
source-style address back.

* Controls: shell, epoch (coarse/fine), profile, packet-depth, optional family.
* On click: call the inverse geocoder (`geocode_inverse.inverse_geocode`).
* Show, **before** the operator copies the vector:
  * the five-token display (`01|65|87|65|23`) and the wire packet;
  * **quantization** — the residual chord distance to the nearest encodable
    point and whether the address is exact (the source codec is quantized, so
    an arbitrary click is generally not exactly representable);
  * **non-uniqueness** — the address each *other* retained family would emit for
    the same click (`aliases`), so one family's route is never mistaken for the
    only answer.

### 2.3 Vector-to-map (decode) screen

The operator **pastes a source vector** and gets pins / cell / region / alias
set back.

* Controls: paste box, shell, epoch, body, profile, family.
* Flow: `inspect` (structural parse: tokens, wire) → `decode`
  (`geocode_forward.geocode`).
* The `candidate_panel` renders:
  * `CANDIDATE_CALIBRATED_POINT` → a single pin **with its cell footprint**;
  * `CANDIDATE_REGION` → a bounded region (uncalibrated single candidate — a pin
    would invent precision);
  * `CANDIDATE_ALIAS_SET` → the complete bounded alias set of pins;
  * `UNDERDETERMINED` → a bounded heatmap region;
  * `INVALID` / foreign body → a typed explanation, never a forced pin.
* `rendered_as_measured` is always `false`.

---

## 3. Uncertainty and the CANDIDATE_ALIAS_SET / agreement surface

Ambiguity is **always** a region or alias set, never invented precision:

* every candidate carries an uncertainty footprint (terminal-cell quantization
  of the source codec);
* the **agreement surface** (`agreement_surface`, from
  `candidate_ensemble.build_candidate_map`) reports, across the retained
  families: `member_count`, `cluster_count`, `agreement_fraction`,
  `dispersion_deg`, and `per_component_variance`. Tightly-clustered members
  agree; spread members disagree. `collapsed_to_point` is always `false`.
* the UI renders agreement as a shaded confidence surface and the alias set as
  distinct pins, so the operator sees the disagreement rather than a single
  confident dot.

---

## 4. Operator workflows

### 4.1 Click-to-address (map → vector)

1. Pick shell, epoch, profile, packet-depth (all shown; no hidden default).
2. Review the stated assumptions.
3. Click the globe (or type lat/lon).
4. Read the five-token address, the quantization residual, and the family
   aliases **before** copying.
5. One-click export (JSON / GeoJSON / KML).

### 4.2 Paste-vector-to-pin (vector → map)

1. Paste the source vector; `inspect` shows the parsed tokens and wire.
2. Pick shell, epoch, body, profile, family.
3. Review the stated assumptions.
4. `decode`; read the result class, pins/region/alias set, and the agreement
   surface.
5. One-click export.

---

## 5. Hidden-default and locked-decision guardrails

* **No hidden defaults.** Every control value is in `control_values` and every
  assumption in `assumptions`. Nothing is silently applied.
* **Locked decisions are never reopened.** `assumptions.locked_decisions_reopened
  = false`; any change to a locked field must mint a **new profile id** — the UI
  exposes no in-place edit of `EARTH_ROOT_D_V1`.
* **Frozen parameters are shown, not editable.** The seven
  `FROZEN_PARAMETERS` are surfaced read-only.
* **Training anchors are not scored as holdout predictions.** The Wilkes fixed
  root and the Stonehenge training anchor (opaque id `STONEHENGE_PRIVATE_001`)
  are rendered as *training* markers, distinct from any holdout candidate.

---

## 6. Privacy firewall

The UI and this spec use **synthetic/public** data only: opaque fixture ids
(e.g. `STONEHENGE_PRIVATE_001`), the synthetic public Stonehenge coordinate
(~51.1789 N, 1.8262 W) with a non-zero uncertainty, and public routes. No
private path literals, no raw private vectors, no private narrative are ever
rendered or logged.

---

## 7. What this UI does **not** claim

The Atlas UI is a viewer over a software calibration. It renders candidate maps;
it measures nothing, asserts no physical effect, and validates no source origin.
Every pin it shows is a `CALIBRATED_CANDIDATE` under a declared, frozen
calibration.
