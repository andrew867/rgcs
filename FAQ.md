# FAQ

**Is this a free-energy / healing-crystal / fringe-physics project?**
No. The project makes no therapeutic, medical, cosmological, or
consciousness claims — a lint in the test suite enforces the vocabulary.
It *does* take unconventional source material seriously enough to turn it
into pre-registered, falsifiable, safety-bounded experiments. Several of
its own registered expectations are **nulls** (it predicts it will see
nothing).

**Has anything been experimentally confirmed?**
No. The repository states this on every claim-bearing surface. It
contains models, tools, controls, calibration plans, and failure
conditions — not confirmations. v2's bench work produced calibrations and
registered negative results.

**Then what's the point?**
Two things. Scientifically: a clean falsification programme — if the
hypotheses are wrong, this machinery shows it efficiently and honestly.
Methodologically: a working demonstration of claim classification,
equation-level provenance, frozen baselines, and conservative extension
in a real codebase — patterns useful to any research-software project.

**What are RGCS and RSCS?**
RGCS (Resonant Geometry Computational System) is the crystal application:
geometry, resonance ladders, coupled modes, anisotropy, optics, timing,
experiments. RSCS (Resonant Spacetime Coordinate System) is the typed
mathematical layer underneath: 17 coordinate types and 23 operators with
units, manifolds, classification, provenance, and machine tests.

**Why is v2 "frozen"? Why not just fix it in place?**
So that v3 can *prove* it changed nothing. The frozen archive plus the
Conservative Extension Property tests mean every generalization must
reproduce the old numbers on the old domain, on every test run. See
DESIGN_PHILOSOPHY.md §3.

**One test fails when I run the suite. Is my install broken?**
Almost certainly not. `test_generator_deterministic` checks *byte
equality* of a golden CSV generated on the Linux reference platform;
last-digit floating-point differences across platforms/library versions
make it fail elsewhere. Semantics are tolerance-checked separately and
pass everywhere. Expected result: **376 passed, 1 failed** off the
reference platform.

**Why five classification labels on everything? It seems heavy.**
Because "Derived inherits the weakest input label" plus a firewall makes
overclaiming a build failure instead of a review argument. It costs one
decorator per function; it has already caught real errors (see the
QA-D-04 story in RESEARCH_HISTORY.md).

**What's "the eye"?**
A term from the historical source material for a special interior locus
of a crystal. The project translates it into an eight-definition "node
menu" (metric centre, measured vibration node, electrical node, …), each
with an observable and a failure condition, with the *measured* node
superseding all theory. See the Crystal Application manuscript §3.

**Can I run the experiments at home?**
The schemas describe low-energy, safety-bounded bench work (≤ 30 V,
≤ 3 A, laser class ≤ 3R with interlocks, dummy-load-first, no human
exposure — DECISION_LOG D7-003 is binding). If you replicate any branch,
report results — negative ones included — per CONTRIBUTING.md.

**Where did the source operating points (4096 Hz, 46 ms, …) come from?**
A historical working log. They are Source claims: they parameterize
protocols and carry no truth value. The exact-cycle arithmetic around
them (e.g. 125 ms closes 512 + 187 cycles) is Derived and confers none.

**Why is the Arisaka NHT/HAL material in here?**
Its *structure* (allocentric/egocentric records, frame transforms,
predicted-vs-observed states) made a useful, ordinary software memory
record — adapted as Engineering, tested as software. The neuroscience
itself is quarantined as Hypothesis/Source: constructing the quarantined
objects literally requires an `acknowledge_hypothesis=True` flag.

**Which Python versions / platforms?**
Python ≥ 3.11; CI covers Linux + Windows × 3.11/3.13. The desktop
workbench needs PySide6 (`pip install -e ".[desktop]"`).

**How do I cite this?**
`CITATION.cff` (GitHub shows a "Cite this repository" button).
