# RGCS — Resonant Geometry Computational System

[![ci](https://github.com/andrew867/rgcs/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/andrew867/rgcs/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.21387947.svg)](https://doi.org/10.5281/zenodo.21387947)

**RGCS V1 Map Workbench — `v1.0.0-rc1`** · MIT · Author: Andrew Green

---

RGCS is a coordinate, mapping, signal, and provenance research workbench. It converts
received or user-supplied numeric vectors into reproducible binary/octal parse
receipts, candidate Earth-root positions, great-circle paths, and polygonal map
regions.

**RGCS does not claim that anomalous sources, craft, crop formations, physical
propulsion, or non-human communication are proven.**

```text
RGCS V1 is done-for-now as a frozen candidate codec + Earth-root workbench.
The mapping, path, and polygon geometry are implemented and testable.
The projector endpoints remain candidate outputs under B01/B02.
```

This is released as **software**, not as **proof**.

---

## Install and run

```bash
python -m pip install -e .
```

```bash
python -m r1053 --help
```

### Parse a vector

```bash
python -m r1053 parse 168930443
```

```
vector          168930443
lane            DIRECT_30BIT  (30-bit direct word)
binary30        001010000100011010110010001011
octal10         1204326213
branch          120  (North American)
F5 / Q22 / S3   5 / 144785 / 3   (S3 is the check digit, not geometry)
source face     19  = (F5 + 14) % 20
active label    Toronto hard anchor
V1 projection   43.653200, -79.383200
claim class     EXACT_ARITHMETIC, TRAINING_EQUALITY, NOT_EVIDENCE_FITS_THE_MAP
blockers        V1-B01, V1-B02, V1-B05
```

### Map a single vector

```bash
python -m r1053 map 168930443
```

### Draw a path between two vectors

```bash
python -m r1053 path 167849523 168930443
```

```
distance        178.846 km (11.93 depth-9 cell edges)
initial bearing 18.41 deg
midpoint        42.891736, -79.738486
cross-check     3 formulas agree: True (spread 2.67e-11 km)
```

### Build a polygon from three or more

```bash
python -m r1053 polygon 165876523,165892743,165892763,165892783
```

```
vertices        4  (AS_SUPPLIED)
perimeter       77.330 km
area            105.268 km2
  cross-check   105.268 km2 (rel diff 7.19e-11)
centroid        51.282952, -1.970409
branches        117  (all same: True)
```

### View the maps

```bash
python -m r1053 serve
```

A `file://` page cannot load basemap tiles — serve them, then open
<http://127.0.0.1:8791/>. Loopback only, no telemetry, no outbound calls beyond the
basemap tiles themselves.

---

## Screenshots

Real captures from a live run. Each has a companion JSON receipt in
[`docs/assets/user-manual/`](docs/assets/user-manual/) carrying its UTC timestamp,
commit SHA, command, input vectors, and output SHA-256. None are mock-ups.

| | |
|---|---|
| ![Erie to Toronto](docs/assets/user-manual/06_path_erie_toronto.png) | **Erie → Toronto**, 178.846 km. Markers on the Lake Erie south shore and Lake Ontario north shore; route across the Niagara peninsula. |
| ![Polygon builder](docs/assets/user-manual/10_polygon_uk4.png) | **Polygon builder**, four branch-117 vectors over Wiltshire. Add/Remove/reorder on the left; area, perimeter, centroid recompute live. |
| ![B01](docs/assets/user-manual/08_path_B01_disagreement.png) | **Blocker B01 rendered.** One vector, one octal word, one branch — two admissible positions 5121.7 km apart. Both fit all three anchors exactly. |

That last image is in the README on purpose. A tool that only showed its successes
would be a tool you could not check.

---

## The claim boundary

```text
Vertex POSITIONS are projector output and remain underdetermined under V1-B01/B02.

Path, polygon, distance, perimeter, centroid, and area geometry are exact for the
selected vertices.

The tool verifies geometry.
It does not verify that a candidate vertex is physically true.
```

The longer form, unchanged since R10.59:

> RGCS V1 is a coordinate/research workbench with a candidate Earth-root projection. It can parse and emit structured vector receipts, reproduce the V1 calibration artifacts, and classify residuals under declared cell-scale and operational-envelope hypotheses. It does not prove physical craft, alien sources, crop-circle authorship, Phryll propulsion, or metric engineering.

### Verified

| question | how |
|---|---|
| Codec parses exactly and reversibly | field reconstruction; `F5<<25 \| Q22<<3 \| S3 == word` |
| Check digit excluded from geometry | 8 words differing only in `S3` land in the identical cell |
| Great-circle distances | three independent formulas agree to < 1e-6 km; 90° = exactly ¼ circumference |
| Drawn paths are true great circles | sampled midpoint equidistant from both ends; segments sum to the distance |
| Polygon areas | two independent exact methods agree to ~1e-13; a spherical octant is exactly ⅛ of the sphere |
| Browser kernel matches the library | 0.000000 m drift on all seven known vectors |
| Wide records refused, never truncated | structural bit-width gate |

### Not verified

**Whether the projected endpoints are the right places.** `A` is scale-invariant —
9 entries, 8 free parameters — fitted against 6 constraints from 3 anchors. Measured
rank is 6, leaving a 2-dimensional free family. Every member fits every anchor to
machine precision, and two members put `165879243` on different continents.

A zero anchor residual is arithmetic, not evidence. **Five** independently sourced hard
anchors is the threshold at which the projection first becomes falsifiable.

### Never claimed

```text
the coordinate system is proven
physical craft are proven
Phryll is proven
Orion's Arm is a factual authority
"The L's" are externally verified
crop circles validate the codec
```

Lore and provenance sources may motivate a test. They may never stand in for one. If
every Orion's Arm reference were deleted from this repository, no verdict and no
blocker would change.

---

## Known blockers

| id | severity | blocker | clears when |
|---|---|---|---|
| B01 | structural | Pinning irreproducibility (gaps 177–5122 km) | pinning recorded upstream, or 4th+5th anchor |
| B02 | structural | Three anchors cannot test a free projective law | ≥5 independently sourced hard anchors |
| B03 | structural | `165879243` is branch-117 (British) with a Quebec label | independent coordinate, or demonstrated crossover |
| B04 | evidential | 15 km cell-scale reading is n = 1 | ≥3 independent words at the declared relation |
| B05 | operational | No coastline; water acceptance cannot score | coastline dataset **and** B01/B02 cleared |
| B06 | operational | Saint-Frédéric is a proxy **and** an observer location | exact civic geocode; observer/object distinction settled |
| B07 | structural | No transport bridge (affine refuted) | bridge reproducing all three labelled pairs |

Full statements, unsoftened: [docs/BLOCKERS_B01_B07.md](docs/BLOCKERS_B01_B07.md).

---

## Documentation

| document | covers |
|---|---|
| [Quickstart](docs/QUICKSTART.md) | clone to map in five minutes |
| [User Manual](docs/USER_MANUAL.md) | full walkthrough with real screenshots |
| [V1 Coordinate System](docs/V1_COORDINATE_SYSTEM.md) | the pipeline, one page |
| [Variable-Length Codec](docs/VARIABLE_LENGTH_CODEC.md) | direct octal lane, staged grammar, wide-envelope gate |
| [Earth Root V1](docs/EARTH_ROOT_V1.md) | frame D_V1, SAA phase hand, the pinning problem |
| [Map / Path / Polygon Guide](docs/MAP_PATH_POLYGON_GUIDE.md) | how the geometry is computed and cross-checked |
| [15 km Cell & Field Envelope Model](docs/15KM_CELL_FIELD_ENVELOPE_MODEL.md) | the cell-scale derivation **and its null** |
| [Frames, Epochs, Galactic Directions](docs/FRAMES_EPOCHS_AND_GALACTIC_DIRECTIONS.md) | epoch gating, Ba-130, SPICE hygiene |
| [Claim Boundaries](docs/CLAIM_BOUNDARIES.md) | verified vs not, claim classes |
| [Blockers B01–B07](docs/BLOCKERS_B01_B07.md) | the open problems |
| [OA Convergence Ledger](docs/OA_CONVERGENCE_LEDGER.md) | hard-SF material as prior, never as evidence |
| [Manuscript](manuscripts/RGCS_Earth_Root_V1_Manuscript.md) | thesis-length technical treatment |
| [Release notes](docs/releases/v1.0.0-rc1.md) | what shipped |
| [Examples](examples/) | ready-to-run vector lists |

Superseded documents are preserved in [`docs/archive/`](docs/archive/) with correction
banners. The wider evidence-governance set (claim register, defect register, decision
log) remains in [`docs/`](docs/).

---

## Tests

```bash
pytest tests/test_r1053_v1.py tests/test_r1059_docs.py tests/test_r1059_polygon.py -q
```

The suite asserts the boundaries, not just the behaviour: that anchor residuals are
labelled non-evidential, that the null accompanies the cell-scale claim, that no
document asserts proof, and that every blocker keeps its detail and clearing
condition.

### Verification status at the frozen release commit (v8.3.0)

- **8129 tests passed**, 15 skipped, 1 deselected, exit 0
  (`expect: 8129 passed`).
- The single deselected node is
  `tests/regression/test_generator_determinism.py::test_generator_deterministic`
  — a byte-equality test that requires the archived v2.0.0 build environment. Hosted
  CI deselects exactly that node id under policy **D-V3-04**. It is the only known
  environment-dependent test in the repository.
- Proof-bundle checksums: **115/115**
  (`rgcs-v4 verify-checksums`).

Counts are derived from a real pytest run into `docs/v4/RELEASE_METADATA.json` and are
guarded — a document that drifts from the recorded number fails the build.

---

## The wider programme, and what it concluded

The map workbench is one lane. RGCS also contains a validated anisotropic FEM and
piezoelectric solver stack, and a resonance/coherence research line. Those lanes
reached **typed refusals**, and the refusals are part of the published result:

| result | typed verdict |
|---|---|
| Canonical 110 mm eye-node study | `UNCERTAINTY_OVERLAPS_CONVENTIONAL_NODE` — the candidate node sits **3.906 mm** from the nearest conventional comparator, and the uncertainty interval overlaps it. Not a distinct node. |
| Quartz mechanism firewall | `MECHANISM_NOT_IMPLEMENTED_FOR_MATERIAL` — a mechanism absent from the model is **not implemented**, which is a statement about the software and never a claim of physical impossibility. |

That second distinction is the house rule of this repository: *not implemented* and
*does not exist* are different claims, and only the first one is ever made here. See
[docs/CLAIM_REGISTER.md](docs/CLAIM_REGISTER.md) and
[docs/v4/WHAT_THIS_QUARTZ_MODEL_DOES_NOT_INCLUDE.md](docs/v4/WHAT_THIS_QUARTZ_MODEL_DOES_NOT_INCLUDE.md).

---

## Release status

```text
current release:   v8.3.0
this candidate:    v1.0.0-rc1 — RGCS V1 Map Workbench (not yet tagged)
codec and workbench: frozen
physical interpretation: candidate, under B01/B02
```

Current release: [v8.3.0](https://github.com/andrew867/rgcs/releases/tag/v8.3.0).

Frozen history: v2.0.0 (`archive/v2.0.0/`), v3.0.x, v4.0.0, v4.1.x — tags and records
are never modified. The DOI badge is the latest **minted** DOI (v3.0.1).

## Citing

See [CITATION.cff](CITATION.cff) and the DOI badge above.
