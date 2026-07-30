# RGCS — Resonant Geometry Computational System

[![ci](https://github.com/andrew867/rgcs/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/andrew867/rgcs/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.21387947.svg)](https://doi.org/10.5281/zenodo.21387947)

**V1 Earth Root: variable codec, South-Up frame, 15 km cell/envelope model**
· MIT license · Author: Andrew Green

```text
V1_STATUS:       OPERATIONAL
PHYSICAL_STATUS: NOT_VALIDATED
OPEN_BLOCKERS:   7 (4 structural)
```

Frozen history: v2.0.0 (`archive/v2.0.0/`), v3.0.x, v4.0.0, v4.1.x — tags and records
are never modified. The DOI badge is the latest **minted** DOI (v3.0.1); v4.x Zenodo
records remain pending human verification.

---

## What this is

> RGCS V1 is a coordinate/research workbench with a candidate Earth-root projection. It can parse and emit structured vector receipts, reproduce the V1 calibration artifacts, and classify residuals under declared cell-scale and operational-envelope hypotheses. It does not prove physical craft, alien sources, crop-circle authorship, Phryll propulsion, or metric engineering.

RGCS is an **evidence-governed research framework** for relational coordinate records,
nested reference frames, uncertainty, provenance, and explicit scientific refusal. The
V1 lane parses a family of compact decimal words as **hierarchical recursive
addresses** and projects them onto Earth under a declared candidate law.

The parsing is exact and tested. The projection is a **candidate that is not yet
falsifiable**, and the repository is built to keep saying so — in the receipts, the
maps, the UI, and the tests.

The project's actual standard:

> It appears possible. Can it be proved, measured, implemented, or honestly refused?

For most physical claims so far the answer has been **refused** or **unmeasured**.
Those results are published alongside everything else, because they are most of the
science.

## What it is not

This project does **not** claim that the coordinate system is proven, that physical
craft are proven, that Phryll is proven, that Orion's Arm is a factual authority, that
"The L's" are externally verified, or that crop circles validate the codec.

---

## Quickstart

```bash
python -m pip install -e .
```

```bash
rgcs-lab doctor
```

```bash
rgcs-lab serve --host 127.0.0.1 --port 8787
```

Then open <http://127.0.0.1:8787/> — loopback only, telemetry off, no outbound calls.

Decode a vector:

```bash
rgcs-lab coordinate decode 165876523
```

Emit a typed address certificate — never a naked coordinate:

```python
from r1053 import certificate
cert = certificate.address_certificate(165879243)
```

Run the coordinate-lane tests:

```bash
pytest tests/test_r1053_v1.py tests/test_r1059_docs.py -q
```

---

## The V1 law

```
direct RGCS-30 word
  → F5 | Q22 | S3
  → source_face = (F5 + 14) % 20
  → 11 × 4-way spherical refinement at split t = 10/19
  → lat/lon = normalize(A u)
```

Two results worth stating plainly:

- **`t = 10/19` wins.** Across all 20 face offsets, depths 9–11, and
  `t ∈ {10/19, 1/2, 9/19}`, the source ratio is the best-performing split at every
  setting.
- **A rotation is refuted.** A rotation would have been testable at three anchors; its
  best anchor RMS is 451.6 km. The free projective form is forced — and with it, the
  under-determination below.

---

## The central limitation

`A` is used projectively, so it is scale-invariant: **9 entries, 8 free parameters**.
Three anchors give **6 constraints**. Measured constraint-matrix rank is 6, leaving a
**2-dimensional free family**.

Every member of that family reproduces all three anchors to machine precision. Under
this repository's recorded pinning, all four V1 words land in southern England —
matching their octal branch `117`. Under the operator-supplied member, `165879243`
lands **5122 km away in Quebec**.

**The law cannot choose between them.** A zero anchor residual is arithmetic, not
evidence. **Five** independently sourced hard anchors is the threshold at which `A`
first becomes over-determined and the projection becomes falsifiable for the first
time.

---

## Blockers

| id | severity | blocker | clears when |
|---|---|---|---|
| B01 | structural | Pinning irreproducibility (gaps 177–5122 km) | a pinning rule is recorded upstream, or a 4th and 5th anchor arrive |
| B02 | structural | Three anchors cannot test a free projective law | ≥5 independently sourced hard anchors |
| B03 | structural | `165879243` is branch-117 (British) with a Quebec label | an independent coordinate, or a demonstrated crossover |
| B04 | evidential | 15 km cell-scale reading is n = 1 | ≥3 independent words at the declared relationship |
| B05 | operational | No coastline; water acceptance cannot score | coastline dataset **and** B01/B02 cleared |
| B06 | operational | Saint-Frédéric is a proxy and an observer location | exact civic geocode + observer/object distinction |
| B07 | structural | No transport bridge (affine refuted) | a bridge reproducing all three labelled pairs |

---

## Documentation

| document | what it covers |
|---|---|
| [User Manual](docs/USER_MANUAL.md) | install, workbench, decoding, receipts, maps — with real screenshots |
| [V1 Earth Root Final Spec](docs/RGCS_V1_EARTH_ROOT_FINAL_SPEC.md) | frame D_V1, SAA phase hand, projection stages, the pinning problem |
| [Variable Codec Final Spec](docs/RGCS_VARIABLE_CODEC_FINAL_SPEC.md) | direct octal lane, staged grammar, long envelope, the gate |
| [15 km Field Envelope Model](docs/RGCS_15KM_FIELD_ENVELOPE_MODEL.md) | cell-scale derivation, envelope analogue, scoring bands, **the null** |
| [Frames, Epochs, Galactic Directions](docs/RGCS_FRAMES_EPOCHS_AND_GALACTIC_DIRECTIONS.md) | epoch gating, Ba-130, calendars, SPICE hygiene |
| [OA Convergence Ledger](docs/RGCS_OA_CONVERGENCE_LEDGER.md) | how hard-SF material is used as a prior and never as evidence |
| [Manuscript](manuscripts/RGCS_Earth_Root_V1_Manuscript.md) | thesis-length technical treatment |
| [CHANGELOG](CHANGELOG.md) | release history |

Superseded public documents are preserved in
[`docs/archive/pre-r1059/`](docs/archive/pre-r1059/) with a correction banner. The
wider evidence-governance document set (claim register, defect register, decision log,
acceptance criteria) remains in [`docs/`](docs/).

---

## How claims are handled

Every result carries a **claim class**. The ones that matter most:

- `EXACT_ARITHMETIC` — reproducible bit arithmetic; the codec lane is here.
- `TRAINING_EQUALITY` — fits because it was fitted. **Not evidence.** The three
  anchors are here.
- `PROJECTION_UNDERDETERMINED` — output of a law with free parameters remaining.
- `CANDIDATE_NOT_LOCATED_TARGET` — a projected point, not a place.

Lore and provenance sources may motivate a test. They may never stand in for one. If
every Orion's Arm reference were deleted from this repository, no verdict and no
blocker would change.

---

## Privacy

Loopback by default (`127.0.0.1`), telemetry off, no outbound calls, and no private
operator transcripts in public builds. Verify with `rgcs-lab doctor`.

## Citing

See [CITATION.cff](CITATION.cff) and the DOI badge above.
