# New-paper reference models and mechanism discrimination
(Agents B01, Q01–Q06)

Coverage: **B009–B016, Q001–Q056**. Sources: five 2026 papers,
ingested with hashes and claim cards in
[`sources/registry/v4x2_source_registry.py`](../../../sources/registry/v4x2_source_registry.py).
Tests: `tests/v4/test_v4x2_refmodels.py`,
`tests/v4/test_v4x2_eye_sources.py`.

**None of these models is quartz evidence.** Each is mathematics from
a named system, kept in that system by a firewall that raises on
forbidden transfers. The playground (Q06) can compare the mathematics;
it is structurally unable to write evidence.

## Q01 — spin-electric exchange (`refmodels/spin_electric.py`)

FePc on MgO, mK. Exchange field follows orbital occupation
(logistic threshold), giving nonlinear resonance shifts near the
threshold (max relative shift > 10%, tested), all-electrical Rabi
detuning, pair selectivity (addressable only when the local shift
exceeds the Rabi width), and the paper's engineering lesson computed:
**the knob that tunes the frequency feeds noise into it**
(`tunability_coherence_tradeoff`). `guard_target()` refuses quartz,
resonators, and room temperature.

## Q02 — triangular many-body transport (`refmodels/triangular_transport.py`)

TBTAP trimers on Pb(111). Three-site Anderson + Pauli master
equation. Reproduces qualitatively: charge enters site-by-site with
Coulomb steps; a **REDISTRIBUTION window** where site occupations
move at nearly constant total; NDC machinery with asymmetric
couplings. The lasting transfer is the classification vocabulary —
`TOTAL_CHANGE` / `REDISTRIBUTION` /
`NO_CHANGE_TRANSFER_FUNCTION_CANDIDATE` — now wired into the Q05
discrimination tree: *a spatial pattern can be a property of the
measurement, not the state.*

(Audit note: the first implementation had a sign error in the
substrate-removal Fermi factor, which saturated the cluster at any
bias; it was caught because the redistribution test could not find
its window, and fixed by rederiving the rate. The broken version is
in git history.)

## Q03 — honeycomb VHS (`refmodels/honeycomb_vhs.py`)

LaRh3B2 boron surface state. Expansion reduces hopping exponentially
→ band narrows → VHS DOS grows (computed, tested). Anisotropic bonds
(C6→C2) split the M points; δ=0 restores symmetry exactly (tested
limit). The ONLY engineering transfer: spacing tunes modal bandwidth
and deliberate anisotropy splits degeneracies **in our mechanical
lattices** — no electronic nematicity claim for any RGCS artifact.

## Q04 — geometric filtration (`refmodels/filtration_solver.py`)

Workflow analogy only. A hidden-triangular demo system is revealed by
a filtration ordering + prefactor rescaling; ε-dependence factorizes
in the revealing basis (verified affine to 1e-12). The source's own
caveat — that its ordering is conjecturally general — is preserved
verbatim, and `rgcs_application()` states plainly that **no RGCS
solve has been restructured and no benefit is claimed yet.**

## Q05 — mechanism discrimination (`refmodels/discrimination.py`)

For every observation class (shift, pattern, splitting, nonlinear),
the ordinary alternatives are enumerated. The tree's honest outputs:

- unevaluated alternative → **INCONCLUSIVE** (silence excludes
  nothing);
- surviving ordinary alternative → **ORDINARY_SUFFICIENT**;
- all excluded with evidence → **CANDIDATE_NOVEL**, which licenses
  further work, never a claim.

`identifiability_report` closes the loop: an effect inside the noise
margin is INCONCLUSIVE no matter how exciting.

## Q06 — the playground (`model_playground.py`, neutral ground)

The playground lives OUTSIDE both `rscs2_core` and
`consciousness_lane`: audit gate G51 caught the first version
(inside the quartz namespace) referencing the quarantined lane,
and the fix was to move the module, not weaken the gate.

Six registered models run under one schema. Every envelope carries an
immutable source-system label and
`evidence_status: REFERENCE_MATHEMATICS_ONLY`; `compare()` keeps the
label attached to every number so a table cannot silently merge
systems.

## B01 — sources

Five records with sha256 prefixes + sizes (hash-regression tested
against the local corpus when present), claim cards separating
measurement/model/inference/speculation, allowed and forbidden
transfers, equation records with provenance and implementation
pointers, DOI/file/equation lookup, an in-press **drift guard** for
the Nature Communications manuscript, and a cross-source concept map
that explicitly disclaims any shared physical mechanism.
