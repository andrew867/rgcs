# RGCS Licence Map

**No previously released code is being relicensed.** The MIT licence
attached to v3.0.0 through v4.8.1 remains exactly as it was. This
document adds a map; it does not change terms, and it does not
retroactively pretend earlier releases used different ones.

## Current state

| Component | Licence | Notes |
|---|---|---|
| Source code (all packages) | **MIT** | `LICENSE`, unchanged since v3.0.0 |
| `pyproject.toml` declaration | MIT | `license = { text = "MIT" }` |
| Tests and test vectors | MIT | same grant as source |
| Schemas (`schemas/`, coordinate/root specs) | MIT | intended as interoperability material |
| Documentation and findings (`docs/`) | MIT | ships in the same tree |
| Papers and technical reports (`papers/`) | MIT | see caveat below |
| Generated workbook (`.xlsx`) | MIT | generated from source, one-way |
| Figures | MIT | generated from code, not hand-drawn from third-party art |

## Caveat on papers

The manuscripts in `papers/` are currently MIT along with the rest of
the tree. **If any is submitted to a journal, the publisher's
agreement may impose different terms on the published version.** That
affects the version of record, not this repository's copy, and any
such divergence should be recorded here when it happens.

## Third-party material

| Item | Status |
|---|---|
| Runtime dependencies (numpy, scipy, pydantic, pyyaml) | not vendored; each under its own permissive licence, installed from PyPI |
| Optional (PySide6, pyqtgraph, openpyxl) | not vendored; PySide6 is LGPL and is used as an unmodified dynamically-linked dependency |
| gmsh | GPL, **isolated as a subprocess** (defect DV4-006), not linked |
| pyopencl | MIT, optional |
| `references/references.bib` | bibliographic metadata only — citations, not copied text |
| Source-claim corpus | **third-party wording quoted for study.** Preserved verbatim under the project's source-hierarchy policy; the project does not claim copyright in it and does not relicense it |

**No third-party material is redistributed under a licence the
project does not hold.** Where source wording is quoted, it is quoted
as source material under study, labelled `SOURCE_CLAIM`, and
attributed.

## What is *not* covered by MIT

- Trademarks and project naming.
- Patent rights — see `PATENT_NON_ASSERTION_INTENT.md`, which is
  intent only, not a covenant.
- Any physical hypothesis. Licensing software says nothing about
  whether a claim is true, and every physical claim here is
  unmeasured.

## Attribution request

Not a licence condition, but asked for in the spirit of the charter:
if you redistribute or build on this work, keep the evidence classes,
the negative-results registers and the scientific boundaries with it.
The machinery without the refusals is a different and worse artifact.
