# RGCS

**Turn a number into a place on a map — and see exactly how much to trust it.**

[![ci](https://github.com/andrew867/rgcs/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/andrew867/rgcs/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.21387947.svg)](https://doi.org/10.5281/zenodo.21387947)

RGCS is a coordinate, mapping, signal, and provenance research workbench. It converts
received or user-supplied numeric vectors into reproducible binary/octal parse
receipts, candidate Earth-root positions, great-circle paths, and polygonal map
regions.

![Erie to Toronto](docs/assets/user-manual/06_path_erie_toronto.png)

*Two vectors in. A real basemap, a great-circle route, distance, bearing and midpoint
out — with every number cross-checked three ways.*

---

## Sixty-second tour

```bash
python -m pip install -e .
```

**Parse a vector.** Decimal in, structure out — no guessing about what the digits mean.

```bash
python -m r1053 parse 168930443
```

```
vector          168930443
octal10         1204326213
branch          120  (North American)
F5 / Q22 / S3   5 / 144785 / 3   (S3 is the check digit, not geometry)
source face     19  = (F5 + 14) % 20
V1 projection   43.653200, -79.383200
claim class     EXACT_ARITHMETIC, TRAINING_EQUALITY, NOT_EVIDENCE_FITS_THE_MAP
blockers        V1-B01, V1-B02, V1-B05
```

**Map one.**

```bash
python -m r1053 map 168930443
```

**Draw a path between two.**

```bash
python -m r1053 path 167849523 168930443
```

```
distance        178.846 km (11.93 depth-9 cell edges)
initial bearing 18.41 deg
midpoint        42.891736, -79.738486
cross-check     3 formulas agree: True (spread 2.67e-11 km)
```

**Build a region from three or more.**

```bash
python -m r1053 polygon 165876523,165892743,165892763,165892783
```

```
vertices        4  (AS_SUPPLIED)
perimeter       77.330 km
area            105.268 km2
  cross-check   105.268 km2 (rel diff 7.19e-11)
centroid        51.282952, -1.970409
```

**See it.** A `file://` page can't fetch basemap tiles, so serve them:

```bash
python -m r1053 serve
```

Open <http://127.0.0.1:8791/>. Loopback only. Full walkthrough in the
[Quickstart](docs/QUICKSTART.md).

---

## The polygon builder

![Polygon builder](docs/assets/user-manual/10_polygon_uk4.png)

Type a vector and press **Add**, paste a comma-separated list, **Remove** any row,
reorder with **Up**, or hit **Order by bearing**. Area, perimeter, centroid and the
self-intersection check recompute on every edit.

The page carries a JavaScript port of the projector so anything you type resolves
instantly. That port is a second implementation of the same law — so it is tested
against the Python library on every known vector. Current drift: **0.000000 m**.

---

## What it will not tell you

![B01](docs/assets/user-manual/08_path_B01_disagreement.png)

*One vector. One octal word `1170616713`. One branch. Two positions 5121.7 km apart —
and both fit all three calibration anchors to machine precision.*

That image is in this README on purpose.

The projector matrix `A` is scale-invariant: 9 entries, **8 free parameters**, fitted
against **6 constraints** from 3 anchors. A 2-dimensional family of solutions survives,
every member fits every anchor exactly, and two of them put the same vector on
different continents. **A zero anchor residual is arithmetic, not evidence.**

So the line this whole project is built around:

```text
Vertex POSITIONS are projector output and remain underdetermined under V1-B01/B02.

Path, polygon, distance, perimeter, centroid, and area geometry are exact for the
selected vertices.

The tool verifies geometry.
It does not verify that a candidate vertex is physically true.
```

**RGCS does not claim that anomalous sources, craft, crop formations, physical
propulsion, or non-human communication are proven.**

The longer form, emitted by the software itself as `r1053.certificate.CLAIM_BOUNDARY`:

> RGCS V1 is a coordinate/research workbench with a candidate Earth-root projection. It can parse and emit structured vector receipts, reproduce the V1 calibration artifacts, and classify residuals under declared cell-scale and operational-envelope hypotheses. It does not prove physical craft, alien sources, crop-circle authorship, Phryll propulsion, or metric engineering.

---

## Verified, and not

| | |
|---|---|
| ✅ Codec parses exactly and reversibly | `F5<<25 \| Q22<<3 \| S3 == word` |
| ✅ Check digit stays out of the geometry | 8 words differing only in `S3` land in the identical cell |
| ✅ Great-circle distances | haversine, law of cosines and Vincenty agree to < 1e-6 km; 90° is exactly ¼ circumference |
| ✅ Drawn paths are true great circles | sampled midpoint equidistant from both ends; segments sum to the distance |
| ✅ Polygon areas | two independent exact methods agree to ~1e-13; a spherical octant is exactly ⅛ of the sphere |
| ✅ Browser kernel matches the library | 0.000000 m drift, all seven known vectors |
| ✅ Oversized records refused, never truncated | structural bit-width gate |
| ❌ **That the projected points are the right places** | open — see below |

**Five** independently sourced hard anchors is the threshold at which the projection
becomes falsifiable for the first time. There are currently three.

---

## Open blockers

| id | blocker | clears when |
|---|---|---|
| **B01** | Two admissible pinnings disagree by up to 5122 km | pinning recorded upstream, or a 4th and 5th anchor |
| **B02** | Three anchors cannot test an 8-parameter law | ≥5 independently sourced hard anchors |
| **B03** | `165879243` is octal branch 117 (British) with a Quebec label | independent coordinate, or a demonstrated crossover |
| **B04** | The 15 km cell-scale reading is n = 1 | ≥3 independent words at the declared relation |
| **B05** | No coastline data, so water acceptance cannot score | coastline dataset **and** B01/B02 cleared |
| **B06** | Saint-Frédéric is a proxy **and** an observer location | exact civic geocode; observer/object distinction settled |
| **B07** | No transport bridge — the affine was refuted | a bridge reproducing all three labelled pairs |

Stated in full, with the numbers that make them real:
**[docs/BLOCKERS_B01_B07.md](docs/BLOCKERS_B01_B07.md)**

---

## How it works

```
decimal wire
   ↓  binary / octal — never decimal triplets              exact
30-bit word
   ↓  F5 | Q22 | S3   (and R4 | S8 | P12 | tail)           exact
   ↓  source_face = (F5 + 14) % 20                         declared
   ↓  11 × 4-way spherical refinement at t = 10/19         declared
kernel vector u
   ↓  lat/lon = normalize(A u)                             underdetermined
candidate position
```

Two findings worth stating plainly:

- **The source ratio wins.** Across all 20 face offsets, depths 9–11 and
  `t ∈ {10/19, ½, 9/19}`, `t = 10/19` is the best-performing split at every setting.
- **A rotation is refuted.** A rotation would have been testable at three anchors; its
  best anchor RMS is 451.6 km. The free projective form — and its under-determination —
  is forced by the data, not chosen.

Coordinates never travel bare. Every one is wrapped in an address certificate carrying
its frame (Earth centre of mass, South-Up mean rotation axis, Wilkes angular root
candidate, SAA phase hand, mean-sea-level datum), its epoch gating, its claim class and
its applicable blockers.

---

## Documentation

**Start here** → [Quickstart](docs/QUICKSTART.md) · [User Manual](docs/USER_MANUAL.md) · [Examples](examples/)

| | |
|---|---|
| [V1 Coordinate System](docs/V1_COORDINATE_SYSTEM.md) | the whole pipeline on one page |
| [Map / Path / Polygon Guide](docs/MAP_PATH_POLYGON_GUIDE.md) | how the geometry is computed and cross-checked |
| [Variable-Length Codec](docs/VARIABLE_LENGTH_CODEC.md) | direct octal lane, staged grammar, the gate |
| [Earth Root V1](docs/EARTH_ROOT_V1.md) | frame D_V1, SAA phase hand, the pinning problem |
| [15 km Cell & Field Envelope Model](docs/15KM_CELL_FIELD_ENVELOPE_MODEL.md) | the cell-scale reading **and its null** |
| [Frames, Epochs, Galactic Directions](docs/FRAMES_EPOCHS_AND_GALACTIC_DIRECTIONS.md) | epoch gating, Ba-130, SPICE hygiene |
| [Claim Boundaries](docs/CLAIM_BOUNDARIES.md) | claim classes; what is and isn't established |
| [Blockers B01–B07](docs/BLOCKERS_B01_B07.md) | the open problems, unsoftened |
| [OA Convergence Ledger](docs/OA_CONVERGENCE_LEDGER.md) | hard-SF material as a prior, never as evidence |
| [Manuscript](manuscripts/RGCS_Earth_Root_V1_Manuscript.md) | thesis-length technical treatment |
| [Release notes](docs/releases/v1.0.0-rc1.md) | what shipped |

Superseded documents live in [`docs/archive/`](docs/archive/) with correction banners.
They are never deleted.

---

## The house rule

> It appears possible. Can it be proved, measured, implemented, or honestly refused?

For most physical claims in this project the answer has been **refused** or
**unmeasured** — and those results are published alongside everything else, because
they are most of the science. Two examples, both carried as typed verdicts in the code:

| result | verdict |
|---|---|
| Canonical 110 mm eye-node study | `UNCERTAINTY_OVERLAPS_CONVENTIONAL_NODE` — the candidate sits **3.906 mm** from the nearest conventional comparator and the uncertainty interval overlaps it. Not a distinct node. |
| Quartz mechanism firewall | `MECHANISM_NOT_IMPLEMENTED_FOR_MATERIAL` — a mechanism absent from the model is *not implemented*. That is a statement about software, never a claim of physical impossibility. |

*Not implemented* and *does not exist* are different claims. Only the first is ever
made here.

The same rule governs every lore and provenance source — Orion's Arm, witness reports,
crop-glyph material. They may motivate a test. They may never stand in for one. If
every such reference were deleted from this repository, no verdict and no blocker
would change.

---

## Tests

```bash
pytest tests/test_r1053_v1.py tests/test_r1059_docs.py \
       tests/test_r1059_polygon.py tests/test_r1062_release.py -q
```

The suite asserts the boundaries, not just the behaviour: that anchor residuals are
labelled non-evidential, that the null travels with the cell-scale claim, that no
document asserts proof, and that every blocker keeps its detail and its clearing
condition.

**Verification status at the frozen release commit (v8.3.0):**
**8129 tests passed**, 15 skipped, 1 deselected, exit 0 (`expect: 8129 passed`);
proof-bundle checksums **115/115** via `rgcs-v4 verify-checksums`. Counts derive from a
real pytest run recorded in `docs/v4/RELEASE_METADATA.json` — a document that drifts
from the recorded number fails the build.

The one deselected node is
`tests/regression/test_generator_determinism.py::test_generator_deterministic`, a
byte-equality check requiring the archived v2.0.0 build environment. Hosted CI
deselects exactly that node id under policy **D-V3-04**. It is the only known
environment-dependent test in the repository.

---

## Release status

```text
current release:  v8.3.0
this candidate:   v1.0.0-rc1 — RGCS V1 Map Workbench
codec + workbench: frozen
physical interpretation: candidate, under B01/B02
```

Current release: [v8.3.0](https://github.com/andrew867/rgcs/releases/tag/v8.3.0).
Frozen history — v2.0.0 (`archive/v2.0.0/`), v3.0.x, v4.0.0, v4.1.x — tags and records
are never modified. The DOI badge is the latest **minted** DOI (v3.0.1).

This release is **software, not proof**.

---

MIT licensed · Author: Andrew Green · Citing: [CITATION.cff](CITATION.cff)
