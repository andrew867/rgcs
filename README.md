# RGCS — Resonant Geometry Computational System

**v3.0.0-rc1 (RSCS 1.0)** · MIT license · Author: Andrew Green
Frozen baseline: v2.0.0 (tag `v2.0.0`, `archive/v2.0.0/` — byte-identical, never modified)

RGCS is a **reproducible research framework** for studying acoustic/mechanical
resonance and phase coherence in engineered quartz geometries: a typed,
provenance-checked mathematics library, a desktop workbench, safety-bounded
experiment schemas, and four fully generated manuscripts — plus a
pre-registered falsification plan for every hypothesis the project holds.

## Honest scope — read this first

**No RGCS hypothesis has been experimentally confirmed.** The repository
contains zero confirming measurements of real crystals. What it contains is
the machinery to test its 30 pre-registered claims honestly: every hypothesis
ships with an observable, matched controls, an uncertainty statement, and a
failure condition — several directional claims are pre-registered **nulls**
(the expected outcome is *no effect*). The project makes **no therapeutic,
medical, cosmological, or consciousness claims**, and a forbidden-vocabulary
lint enforces that in the test suite.

Every scientific statement in code, docs, UI, and manuscripts carries one of
five machine-checked labels (`docs/SCIENTIFIC_CLASSIFICATION_POLICY.md`):

| Label | Meaning |
|---|---|
| **Established** (EST) | textbook math/physics anyone can verify independently |
| **Derived** (DER) | computed within RGCS from stated inputs by stated math; inherits the weakest input label |
| **Hypothesis** (HYP) | a falsifiable RGCS conjecture; never presented as fact |
| **Source claim** (SRC) | an external source's statement, reported with provenance, not endorsed |
| **Engineering plan** (ENG) | unbuilt software/hardware design; never evidence |

A machine-enforced firewall rejects any Established/Derived output computed
from Hypothesis/Source/Engineering inputs.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│ rgcs_desktop      PySide6 workbench (13 panels) + headless,     │
│                   tested services (provenance graph, waveform/   │
│                   timing preview, phase-budget views)             │
├─────────────────────────────────────────────────────────────────┤
│ rgcs_core         crystal application: geometry, resonance       │
│                   ladders, coupled modes, anisotropy (Christoffel)│
│                   optics, timing/drive, experiments, crystal DB,  │
│                   FEA export — 61 frozen equations RGCS-M.1..61   │
├─────────────────────────────────────────────────────────────────┤
│ rscs_core         RSCS 1.0 typed framework: 17 coordinates +     │
│                   23 operators on declared manifolds, machine     │
│                   registry, classification firewall, embedding ι  │
├─────────────────────────────────────────────────────────────────┤
│ Conservative Extension Property (machine-tested, every commit):   │
│        O_RSCS(ι(x)) = ι(O_RGCS(x))  on the frozen v2 domain      │
├─────────────────────────────────────────────────────────────────┤
│ RGCS v2.0.0 — FROZEN  (tag v2.0.0, archive/v2.0.0/)              │
└─────────────────────────────────────────────────────────────────┘

experiments/   JSON schemas + validated example manifests (13 schemas)
manuscripts/   4 XeLaTeX manuscripts, every number generated from code
embedded/      HG Embedded OS contract (ESP32/CYD; ENG until built)
scad/          OpenSCAD CAD generators (v7 fixes the v6 D-02 defect)
docs/          full specification, decision log, QA and audit trail
release/       v3.0.0-rc1 artifacts, SHA256SUMS, provenance manifest
```

The layering rule: v3 never edits v2 — it reaches the frozen core only
through the embedding, and the Conservative Extension Property battery
proves the round trip on every test run.

## A taste of what's inside

The flagship v3 result — the v2 scalar wave-speed *hypothesis* resolved into
a measured-orientation anisotropic model that recovers the scalar as its
special case (its ±5 % band turns out to be the physical X–Z spread):

![Anisotropic wave speed vs direction, with the v2 scalar band](docs/images/anisotropy_sweep.png)

The three frozen macro drive envelopes, rendered by the same code the
desktop preview and firmware acceptance tests use (the source's ambiguous
"shorter by half" phrase is preserved as *two* distinctly named modes):

![The three frozen macro drive envelopes](docs/images/macro_envelopes.png)

Desktop workbench screenshots will accompany the T2 panel tranche; until
then the headless services behind those panels are fully tested and their
outputs are what you see above.

## Quick start

```bash
git clone <this-repo> && cd RGCS
python3 -m pip install -e ".[dev]"        # core + test tooling
python3 -m pytest -q                       # 377 tests; expect 376 passed
                                           # (1 documented golden-CSV
                                           # byte-equality test is
                                           # Linux-reference-only)
```

Then try the library:

```python
from rscs_core.coupling import couple_modes
couple_modes([1000.0, 1000.0], [[0.0, 10.0], [10.0, 0.0]])
# hybrid frequencies 990/1010 Hz — the 2g splitting, anti-Hermitian K = i·2πg

from rgcs_core.anisotropy import axis_speeds
axis_speeds()["Z"]["v_quasi_long_m_s"]   # 6330 m/s = sqrt(c33/rho)
```

Desktop workbench: `pip install -e ".[desktop]"` then
`python -m rgcs_desktop` (or `--smoke-check` headless).
Validate experiment manifests: `python experiments/schemas/validate.py`.

## Build the manuscripts

```bash
python tools/make_v3_artifacts.py       # regenerate every table/figure
cd manuscripts/rscs_foundations
xelatex rscs_foundations.tex && bibtex rscs_foundations \
  && xelatex rscs_foundations.tex && xelatex rscs_foundations.tex
```

(Each manuscript directory has a `BUILD.md`; `latexmk -xelatex` works where
perl is available.) The v2 manuscript builds the same way in `manuscript/`.

## Publications

| Work | What it covers | Source |
|---|---|---|
| **RSCS Foundations** | the typed framework, conservative extension, coupling keystone | `manuscripts/rscs_foundations/` |
| **RGCS Crystal Application** | anisotropic propagation, node menu, optical probe layer | `manuscripts/rgcs_crystal_application/` |
| **Software & Hardware Roadmap** | platform layering, timing architecture, safety envelope, embedded contract | `manuscripts/software_hardware_plan/` |
| **Historical & Source Companion** | the source corpus in its own words, adaptations and binding exclusions | `manuscripts/historical_source_companion/` |
| RGCS v2 manuscript (28 pp.) | the frozen v2 system | `manuscript/rgcs_v2.pdf` |

Every numeric table, figure, and inline value in all five documents is
generated from the tested libraries at build time — no number is hand-typed.

## Lessons learned

- Independent QA is most valuable when it is allowed to overturn the
  project's own mathematics. A v2 review found an incorrect time-domain
  coupling map; fixing it (anti-Hermitian `K = i·2πg`) changed the physical
  interpretation and produced a permanent regression test.
- Provenance and classification matter as much as equations. Separating
  Established, Derived, Hypothesis, Source, and Engineering claims allowed
  historical material to inspire tests without becoming evidence by
  repetition — and a machine-enforced firewall keeps it that way.
- Historical or unconventional claims can often be translated into
  measurable variables without presuming they are true: "the eye" became an
  eight-definition node menu with failure conditions; "a single crystal
  tone" became a scalar wave speed that anisotropic modelling then explained.
- A resonant system cannot be characterized by geometry and nominal
  frequency alone: boundary conditions, anisotropy, mode overlap, phase,
  delay, damping, loading, uncertainty, and measurement fidelity all matter.
  The phase-at-coordinate model exists because commanded phase is never the
  phase at the crystal.
- Cross-platform numerical reproducibility requires declared environments
  plus tolerance-aware portability tests. Two of our "Windows defects"
  turned out to be an undeclared dependency; the third was a real
  path-separator bug. A two-OS CI matrix caught what code review had not.
- Frozen registries and conservative-extension tests made it possible to
  expand the framework without silently rewriting earlier results.
- Software and modelling advanced faster than the measurement programme.
  The project's strongest current output is a reproducible framework and
  falsification plan, not experimental confirmation — and every
  claim-bearing surface says so.
- Independent review, negative results, and explicit failure conditions
  strengthened rather than weakened the project.

Fuller engineering version: `docs/SOFTWARE_HARDWARE_ARCHITECTURE.md`.

## Roadmap

| Tranche | Content | Status |
|---|---|---|
| — | Green Linux CI run | **the only gate to final v3.0.0** |
| T2 | Desktop Qt panels over the tested headless services | contracts fixed |
| T3 | FEA import scripts, coupling-graph panel | scoped |
| T4 | HG Embedded OS firmware (BSP, timing service, self-test) | contract published |
| T5 | Timing hardware (TCXO/DDS/CPLD + interlocks) | ENG until measured |
| T6 | Latency-calibration campaign (unblocks phase claims, gate H-29) | pre-registered |
| — | Bench campaigns for claims H-20..H-30 | pre-registered |

## Limitations (honest list)

1. One inherited test failure by design: a golden CSV is byte-exact only on
   the Linux reference platform (semantics are tolerance-checked
   everywhere; deselected in Windows CI with documented justification).
2. The CI matrix is defined but the Linux legs have not yet executed.
3. Desktop panels, FEA import, firmware, and hardware are contracts and
   tested headless services — not shipped UI/firmware/hardware.
4. No bench data: nothing physical is confirmed (see Honest scope).
5. The four v3 manuscripts are concise generated-number spines (3–5 pp.)
   over the fuller repository documentation, by design at this stage.

Full list with evidence: `release/RELEASE_NOTES.md` and
`docs/QA_REPORT_V3.md`.

## Contributing, support, and conduct

See [CONTRIBUTING.md](CONTRIBUTING.md), [SUPPORT.md](SUPPORT.md),
[CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md), [SECURITY.md](SECURITY.md),
[FAQ.md](FAQ.md), and — for the *why* behind the unusual discipline —
[DESIGN_PHILOSOPHY.md](DESIGN_PHILOSOPHY.md) and
[RESEARCH_HISTORY.md](RESEARCH_HISTORY.md).

## Citing

See [`CITATION.cff`](CITATION.cff) (GitHub renders a "Cite this repository"
button from it). Release provenance — commit, environment, checksums, test
evidence: `release/PROVENANCE.json` and `release/SHA256SUMS.txt`.

## Acknowledgements

- The historical crystal-practice corpus and personal working logs that
  posed the questions this programme formalizes (preserved, with authorship
  and original wording, in the Historical & Source Companion).
- K. Arisaka (UCLA) for the publicly presented NHT/HAL proposals whose
  *structure* inspired the Hydrogenuine memory record — adapted as
  engineering, with the neuroscience explicitly quarantined.
- The authors of the six photonics/magnonics papers whose published
  mathematics is adapted (and only the mathematics — every forbidden
  transfer is registered): Sohn, Orsel & Bahl; Cheng et al.; Lapointe,
  Coia & Vallée; Wang et al.; Zhang, Zhan, Gong & Niu; Chao, Yam, Vivien
  & Dagens; and Koster et al. for the coherence-metric methodology.
- The open-source stack this project stands on: NumPy, SciPy, matplotlib,
  PySide6, pytest, Hypothesis, jsonschema, TeX Gyre/XeLaTeX.
