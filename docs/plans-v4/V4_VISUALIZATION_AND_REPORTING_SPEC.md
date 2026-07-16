# V4 Visualization & Reporting Spec — `rscs2_core.report`

**Status:** PLANNING. **matplotlib (present) is the always-available
baseline renderer**; pyvista/VTK are optional for interactive 3D. Every
figure is generated from tested code (no hand-drawn numbers) and is
deterministic (SOURCE_DATE_EPOCH pinned — the D-V3-02/05/06 lesson is
law: no raw mathtext, no non-reproducible timestamps).

## 1. Visual products

| Product | Baseline (always) | Enhanced (optional) |
|---|---|---|
| 3D mesh | matplotlib trisurf / PNG | pyvista interactive |
| animated mode shapes | matplotlib frames → GIF/MP4 | pyvista animation |
| displacement / strain-energy fields | matplotlib slices + colourbar | pyvista volume |
| optical ray paths | matplotlib 3D lines | pyvista |
| coil & field overlays | matplotlib quiver/slice | pyvista streamlines |
| eye-diagnostic overlays | matplotlib field + region contours | pyvista isosurface |
| mode-spectrum plot | matplotlib | — |
| avoided crossings | matplotlib (reuse v3 style) | — |
| mesh-convergence plot | matplotlib | — |
| CPU/GPU parity plot | matplotlib | — |
| uncertainty envelopes | matplotlib fill_between | — |

**CPU-only users get every essential figure** from matplotlib; nothing
scientific requires VTK.

## 2. Honesty in visuals (binding)

- Circulation/streamlines are labelled "field feature", **never** a
  physical vortex (exclusion); captions carry the classification chip.
- Eye overlays show *regions with confidence*, never a lone point; a
  NULL verdict renders as an explicit "no stable candidate" panel, not a
  blank.
- Every figure caption states the fidelity Level, backend, and
  classification of what it shows.

## 3. Automatic report generation

A run → a Markdown/PDF report: geometry + mesh manifest summary, mode
spectrum, per-mode fields, eye-diagnostic maps + regions + verdict + the
four comparisons, uncertainty envelopes, benchmark-status table
(V.1..V.10 green/red for the build), backend + parity status, and a
**provenance graph** (extends the v3 `provenance_graph` service) linking
every number to its RSCS2-* id and inputs. Reports are regenerable
byte-stably (tolerance-aware) from a tagged state.

## 4. Visual regression tests

Perceptual-hash / small-tolerance image comparison against committed
reference PNGs (deterministic renderer settings); a **mathtext-render
lint** (the D-V3-05 guard: no raw `$...$` leaks into an image);
report-freshness test (regenerate → diff tables/numbers byte-stable);
NULL-verdict rendering test; caption-classification-chip presence test.

## 5. Screenshots / demo recordings

Scripted screenshot + short screen-recording generation for the desktop
panels and CLI runs (for README/manuscripts), produced by a headless
harness so they regenerate in CI where a display is emulated
(`QT_QPA_PLATFORM=offscreen`, as v3).
